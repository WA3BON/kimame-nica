from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductVariant, ProductImage, Order, OrderItem, Address


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'order', 'preview')
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:4px;">', obj.image.url)
        return ''
    preview.short_description = 'プレビュー'


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('weight_kg', 'price', 'stock')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('thumbnail', 'no', 'name', 'product_type', 'origin', 'roast_level', 'starting_price', 'created_at')
    list_filter = ('product_type', 'origin', 'roast_level')
    search_fields = ('name', 'origin')
    readonly_fields = ('created_at', 'thumbnail')
    inlines = [ProductVariantInline, ProductImageInline]
    fieldsets = (
        (None, {'fields': ('thumbnail', 'no', 'name', 'title', 'description', 'product_type', 'origin', 'roast_level')}),
        ('画像', {'fields': ('logo', 'image', 'map')}),
        ('産地マップ(座標)', {'fields': ('latitude', 'longitude')}),
        ('その他', {'fields': ('created_at',)}),
    )

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:50px;border-radius:4px;" title="トップ画像(サムネイル)">', obj.image.url)
        return '(画像なし)'
    thumbnail.short_description = 'トップ画像'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'variant', 'product_name', 'weight_kg', 'unit_price', 'quantity')
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total', 'created_at', 'paid_at')
    list_filter = ('status',)
    search_fields = ('contact_email', 'shipping_name', 'stripe_checkout_session_id')
    readonly_fields = (
        'subtotal', 'total', 'stripe_checkout_session_id', 'stripe_payment_intent_id',
        'created_at', 'updated_at', 'paid_at',
    )
    inlines = [OrderItemInline]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'prefecture', 'city', 'is_default')
    search_fields = ('full_name', 'user__email')