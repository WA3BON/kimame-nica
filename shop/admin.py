import csv

from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join
from django.utils.translation import gettext as _g, gettext_lazy as _

from core.models import CompanyInfo
from .models import Product, ProductVariant, ProductImage, Order, OrderItem, Address

User = get_user_model()

admin.site.site_header = _("KiMame 管理画面")
admin.site.site_title = _("KiMame 管理")
admin.site.index_title = _("ダッシュボード")

# Status → (background colour, short hint shown under the badge in the order list)
STATUS_STYLES = {
    Order.Status.PENDING: ('#9ca3af', _('決済待ち')),
    Order.Status.PAID: ('#dc2626', _('要対応:発送準備へ')),
    Order.Status.PREPARING: ('#d97706', _('梱包・発送待ち')),
    Order.Status.FULFILLED: ('#16a34a', _('完了')),
    Order.Status.FAILED: ('#6b7280', ''),
    Order.Status.CANCELED: ('#374151', ''),
}

# Orders that count as real sales (money received).
SOLD_STATUSES = [Order.Status.PAID, Order.Status.PREPARING, Order.Status.FULFILLED]


def status_badge_html(order):
    color, _hint = STATUS_STYLES.get(order.status, ('#6b7280', ''))
    return format_html(
        '<span style="display:inline-block;padding:3px 10px;border-radius:999px;'
        'background:{};color:#fff;font-weight:bold;font-size:12px;white-space:nowrap;">{}</span>',
        color, order.get_status_display(),
    )


def yen(value):
    return f"¥{value:,.0f}" if value is not None else "-"


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'order', 'preview')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:4px;">', obj.image.url)
        return ''
    preview.short_description = _('プレビュー')


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('weight_kg', 'price', 'stock')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'no', 'name', 'product_type', 'origin', 'roast_level', 'starting_price_display', 'stock_summary', 'created_at')
    list_display_links = ('thumbnail', 'name')
    list_filter = ('product_type', 'origin', 'roast_level')
    search_fields = ('name', 'origin')
    readonly_fields = ('created_at', 'thumbnail')
    inlines = [ProductVariantInline, ProductImageInline]
    fieldsets = (
        (None, {'fields': ('thumbnail', 'no', 'name', 'title', 'description', 'notes', 'product_type', 'origin', 'roast_level')}),
        (_('画像'), {'fields': ('logo', 'image', 'map')}),
        (_('産地マップ(座標)'), {'fields': ('latitude', 'longitude')}),
        (_('その他'), {'fields': ('created_at',)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('variants')

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:50px;border-radius:4px;">', obj.image.url)
        return _g('(画像なし)')
    thumbnail.short_description = _('トップ画像')

    def stock_summary(self, obj):
        variants = list(obj.variants.all())
        if not variants:
            return '-'
        return format_html_join(
            '<br>', '{}: <span style="color:{};font-weight:bold;">{}</span>',
            ((v.label, '#dc2626' if v.stock <= 3 else 'inherit', v.stock) for v in variants),
        )
    stock_summary.short_description = _('在庫')

    @admin.display(description=_('最安値'))
    def starting_price_display(self, obj):
        return yen(obj.starting_price)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product_name', 'weight_kg', 'unit_price', 'quantity', 'line_total_display')
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def line_total_display(self, obj):
        return yen(obj.line_total)
    line_total_display.short_description = _('小計')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_no', 'status_badge', 'created_at', 'shipping_name', 'shipping_prefecture',
        'items_summary', 'total_display', 'tracking_link', 'sheet_link',
    )
    list_display_links = ('order_no',)
    list_filter = ('status', 'created_at', 'shipping_prefecture')
    date_hierarchy = 'created_at'
    search_fields = ('id', 'contact_email', 'shipping_name', 'shipping_phone', 'tracking_number', 'stripe_checkout_session_id')
    list_per_page = 50
    actions = ['mark_preparing', 'mark_fulfilled', 'mark_canceled', 'export_csv']
    inlines = [OrderItemInline]
    # What the customer chose (items, amounts, contact/shipping details) is never editable here,
    # even for admins; only the fulfilment fields below are.
    customer_fields = (
        'user', 'contact_email', 'shipping_name', 'shipping_phone', 'shipping_postal_code',
        'shipping_prefecture', 'shipping_city', 'shipping_address_line1', 'shipping_address_line2',
        'subtotal', 'shipping_fee', 'total',
    )
    readonly_fields = customer_fields + (
        'status_badge', 'sheet_link', 'tracking_link', 'stripe_checkout_session_id', 'stripe_payment_intent_id',
        'created_at', 'updated_at', 'paid_at',
    )
    fieldsets = (
        (_('ステータス'), {'fields': (('status_badge', 'sheet_link'), 'status', ('tracking_number', 'tracking_link'), 'shipped_at', 'admin_note')}),
        (_('お客様・お届け先(編集不可)'), {'fields': (
            'user', 'contact_email', 'shipping_name', 'shipping_phone', 'shipping_postal_code',
            'shipping_prefecture', 'shipping_city', 'shipping_address_line1', 'shipping_address_line2',
        )}),
        (_('金額(編集不可)'), {'fields': ('subtotal', 'shipping_fee', 'total')}),
        (_('決済・日時'), {'classes': ('collapse',), 'fields': (
            'paid_at', 'created_at', 'updated_at', 'stripe_checkout_session_id', 'stripe_payment_intent_id',
        )}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items')

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = [
            path('<int:pk>/sheet/', self.admin_site.admin_view(self.sheet_view), name='shop_order_sheet'),
        ]
        return urls + super().get_urls()

    def sheet_view(self, request, pk):
        order = get_object_or_404(Order.objects.prefetch_related('items'), pk=pk)
        context = {
            **self.admin_site.each_context(request),
            'title': _g('受注シート #{pk}').format(pk=order.pk),
            'order': order,
            'items': order.items.all(),
            'company': CompanyInfo.objects.first(),
            'status_badge': status_badge_html(order),
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/shop/order/sheet.html', context)

    def save_model(self, request, obj, form, change):
        if obj.status == Order.Status.FULFILLED and not obj.shipped_at:
            obj.shipped_at = timezone.now()
        super().save_model(request, obj, form, change)

    # --- list columns ---

    @admin.display(description=_('注文番号'), ordering='id')
    def order_no(self, obj):
        return f"#{obj.pk}"

    @admin.display(description=_('状態'), ordering='status')
    def status_badge(self, obj):
        _color, hint = STATUS_STYLES.get(obj.status, ('', ''))
        if hint:
            return format_html('{}<div style="font-size:11px;color:var(--body-quiet-color);margin-top:2px;">{}</div>',
                               status_badge_html(obj), hint)
        return status_badge_html(obj)

    @admin.display(description=_('商品'))
    def items_summary(self, obj):
        return format_html_join(
            '<br>', '{} ({}kg) × {}',
            ((i.product_name, f"{float(i.weight_kg):g}", i.quantity) for i in obj.items.all()),
        )

    @admin.display(description=_('合計'), ordering='total')
    def total_display(self, obj):
        return yen(obj.total)

    @admin.display(description=_('DHL追跡'), ordering='tracking_number')
    def tracking_link(self, obj):
        if not obj.tracking_number:
            return '-'
        return format_html('<a href="{}" target="_blank" rel="noopener">{}</a>', obj.tracking_url, obj.tracking_number)

    @admin.display(description=_('受注シート'))
    def sheet_link(self, obj):
        if not obj.pk:
            return '-'
        url = reverse('admin:shop_order_sheet', args=[obj.pk])
        return format_html('<a href="{}" target="_blank">📄 {}</a>', url, _g('シートを開く'))

    # --- bulk actions ---

    def _bulk_set_status(self, request, queryset, status, allowed_from, **extra):
        target = queryset.filter(status__in=allowed_from)
        updated = target.update(status=status, **extra)
        skipped = queryset.count() - updated
        label = Order.Status(status).label
        self.message_user(request, _g('{n}件を「{label}」に変更しました。').format(n=updated, label=label), messages.SUCCESS)
        if skipped:
            self.message_user(request, _g('{n}件は現在の状態では変更できないためスキップしました。').format(n=skipped), messages.WARNING)

    @admin.action(description=_('選択した注文を「発送準備中」にする'))
    def mark_preparing(self, request, queryset):
        self._bulk_set_status(request, queryset, Order.Status.PREPARING, [Order.Status.PAID])

    @admin.action(description=_('選択した注文を「発送済み」にする'))
    def mark_fulfilled(self, request, queryset):
        queryset.filter(status__in=[Order.Status.PAID, Order.Status.PREPARING], shipped_at__isnull=True).update(
            shipped_at=timezone.now()
        )
        self._bulk_set_status(request, queryset, Order.Status.FULFILLED, [Order.Status.PAID, Order.Status.PREPARING])

    @admin.action(description=_('選択した注文を「キャンセル」にする'))
    def mark_canceled(self, request, queryset):
        self._bulk_set_status(
            request, queryset, Order.Status.CANCELED,
            [Order.Status.PENDING, Order.Status.PAID, Order.Status.PREPARING, Order.Status.FAILED],
        )

    @admin.action(description=_('選択した注文をCSV(Excel用)でダウンロード'))
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        filename = f"orders_{timezone.localtime():%Y%m%d_%H%M}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.write('﻿')  # BOM so Excel opens UTF-8 Japanese correctly
        writer = csv.writer(response)
        writer.writerow([_g(h) for h in (
            '注文番号', '状態', '注文日時', '支払日時', '発送日時', 'DHL追跡番号', 'お名前', 'メール', '電話',
            '郵便番号', '住所', '商品', '小計', '送料', '合計', '社内メモ',
        )])
        fmt = lambda dt: timezone.localtime(dt).strftime('%Y-%m-%d %H:%M') if dt else ''
        for o in queryset.prefetch_related('items'):
            items = ' / '.join(f"{i.product_name}({float(i.weight_kg):g}kg)×{i.quantity}" for i in o.items.all())
            address = f"{o.shipping_prefecture}{o.shipping_city}{o.shipping_address_line1} {o.shipping_address_line2}".strip()
            writer.writerow([
                o.pk, o.get_status_display(), fmt(o.created_at), fmt(o.paid_at), fmt(o.shipped_at), o.tracking_number,
                o.shipping_name, o.contact_email, o.shipping_phone, o.shipping_postal_code, address, items,
                int(o.subtotal), int(o.shipping_fee), int(o.total), o.admin_note,
            ])
        return response


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'prefecture', 'city', 'phone', 'is_default')
    search_fields = ('full_name', 'user__email', 'phone')


# --- Users: show their orders and addresses on the user page ---

class UserAddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ('full_name', 'postal_code', 'prefecture', 'city', 'address_line1', 'address_line2', 'phone', 'is_default')


class UserOrderInline(admin.TabularInline):
    model = Order
    extra = 0
    fields = ('status', 'created_at', 'total', 'shipping_name')
    readonly_fields = fields
    show_change_link = True
    can_delete = False
    verbose_name_plural = _('注文履歴')

    def has_add_permission(self, request, obj=None):
        return False


admin.site.unregister(User)


@admin.register(User)
class KiMameUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'date_joined', 'last_login', 'order_count', 'total_spent', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    inlines = [UserAddressInline, UserOrderInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            _order_count=Count('orders', filter=Q(orders__status__in=SOLD_STATUSES), distinct=True),
            _total_spent=Sum('orders__total', filter=Q(orders__status__in=SOLD_STATUSES)),
        )

    def get_inlines(self, request, obj):
        # The "add user" form has no user yet, so the related inlines make no sense there.
        return self.inlines if obj else []

    @admin.display(description=_('購入回数'), ordering='_order_count')
    def order_count(self, obj):
        return obj._order_count

    @admin.display(description=_('購入金額'), ordering='_total_spent')
    def total_spent(self, obj):
        return yen(obj._total_spent) if obj._total_spent else '-'
