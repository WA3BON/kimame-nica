from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join

from .google.gmail import send_mail_with_gmail
from .notifications import sender_name
from .models import Faq, CompanyInfo, Inquiry, InquiryReply, ShippingStep, WhyChooseUs, PrivacyPolicy, OrderPolicy, TermsOfService, AppPolicy

INQUIRY_STATUS_COLORS = {
    Inquiry.Status.NEW: '#dc2626',
    Inquiry.Status.REPLIED: '#2563eb',
    Inquiry.Status.CLOSED: '#16a34a',
}


class InquiryReplyForm(forms.Form):
    subject = forms.CharField(label='件名', max_length=200, widget=forms.TextInput(attrs={'style': 'width:100%'}))
    body = forms.CharField(label='本文', widget=forms.Textarea(attrs={'rows': 18, 'style': 'width:100%'}))


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'status_badge', 'kind', 'name', 'email', 'product', 'quantity', 'message_preview', 'reply_count')
    list_display_links = ('created_at', 'name')
    list_filter = ('status', 'kind', 'created_at')
    search_fields = ('name', 'email', 'message')
    date_hierarchy = 'created_at'
    # What the customer submitted is shown but never editable, even for admins.
    customer_fields = ('kind', 'name', 'email', 'user', 'product', 'quantity', 'prefecture', 'message', 'created_at')
    readonly_fields = customer_fields + ('reply_button', 'reply_history')
    fieldsets = (
        ('対応', {'fields': ('reply_button', 'status', 'admin_note')}),
        ('お客様からの内容(編集不可)', {'fields': customer_fields}),
        ('返信履歴', {'fields': ('reply_history',)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_reply_count=Count('replies'))

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        urls = [
            path('<int:pk>/reply/', self.admin_site.admin_view(self.reply_view), name='core_inquiry_reply'),
        ]
        return urls + super().get_urls()

    def reply_view(self, request, pk):
        inquiry = get_object_or_404(Inquiry, pk=pk)
        if not self.has_change_permission(request, inquiry):
            raise PermissionDenied
        change_url = reverse('admin:core_inquiry_change', args=[inquiry.pk])

        if request.method == 'POST':
            form = InquiryReplyForm(request.POST)
            if form.is_valid():
                try:
                    send_mail_with_gmail(
                        to_email=inquiry.email,
                        subject=form.cleaned_data['subject'],
                        body=form.cleaned_data['body'],
                        sender_name=sender_name(),
                    )
                except Exception as e:
                    self.message_user(request, f"送信に失敗しました: {e}", messages.ERROR)
                else:
                    InquiryReply.objects.create(
                        inquiry=inquiry, sent_by=request.user, **form.cleaned_data
                    )
                    if inquiry.status == Inquiry.Status.NEW:
                        inquiry.status = Inquiry.Status.REPLIED
                        inquiry.save(update_fields=['status'])
                    self.message_user(request, f"{inquiry.email} に返信を送信しました。", messages.SUCCESS)
                    return redirect(change_url)
        else:
            quoted = "\n".join(f"> {line}" for line in inquiry.message.splitlines())
            form = InquiryReplyForm(initial={
                'subject': f"Re: 【KiMame】{inquiry.get_kind_display()}について",
                'body': (
                    f"{inquiry.name} 様\n\n"
                    f"この度は{inquiry.get_kind_display()}いただき、誠にありがとうございます。\n\n\n\n"
                    f"今後ともよろしくお願いいたします。\n{sender_name()}\n\n"
                    f"---- お問い合わせ内容 ----\n{quoted}"
                ),
            })

        context = {
            **self.admin_site.each_context(request),
            'title': f'{inquiry.name} 様へ返信',
            'inquiry': inquiry,
            'form': form,
            'change_url': change_url,
            'opts': self.model._meta,
        }
        return TemplateResponse(request, 'admin/core/inquiry/reply.html', context)

    @admin.display(description='状態', ordering='status')
    def status_badge(self, obj):
        return format_html(
            '<span style="display:inline-block;padding:3px 10px;border-radius:999px;background:{};'
            'color:#fff;font-weight:bold;font-size:12px;white-space:nowrap;">{}</span>',
            INQUIRY_STATUS_COLORS.get(obj.status, '#6b7280'), obj.get_status_display(),
        )

    @admin.display(description='内容')
    def message_preview(self, obj):
        return obj.message[:40] + ('…' if len(obj.message) > 40 else '')

    @admin.display(description='返信数', ordering='_reply_count')
    def reply_count(self, obj):
        return obj._reply_count or '-'

    @admin.display(description='返信')
    def reply_button(self, obj):
        if not obj.pk:
            return '-'
        return format_html(
            '<a class="button" style="padding:8px 16px;" href="{}">✉️ {} 様にメールで返信する</a>',
            reverse('admin:core_inquiry_reply', args=[obj.pk]), obj.name,
        )

    @admin.display(description='送信済みの返信')
    def reply_history(self, obj):
        replies = list(obj.replies.select_related('sent_by'))
        if not replies:
            return 'まだ返信していません'
        return format_html_join(
            '', '<div style="border:1px solid var(--hairline-color);border-radius:6px;padding:10px;margin-bottom:10px;">'
                '<div style="font-size:12px;color:var(--body-quiet-color);">{} / {}</div>'
                '<div style="font-weight:bold;margin:4px 0;">{}</div>'
                '<div style="white-space:pre-line;">{}</div></div>',
            ((timezone.localtime(r.sent_at).strftime('%Y-%m-%d %H:%M'),
              r.sent_by.email if r.sent_by else '-', r.subject, r.body) for r in replies),
        )


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'updated_at', 'logo', 'favicon', 'ogp_image',)
    readonly_fields = ('updated_at',)

    def has_add_permission(self, request):
        if CompanyInfo.objects.exists():
            return False
        return True

@admin.register(ShippingStep)
class ShippingStepAdmin(admin.ModelAdmin):
    list_display = ('no', 'title', 'duration', 'description', 'image', 'updated_at')
    ordering = ('no',)
    readonly_fields = ('updated_at',)

@admin.register(WhyChooseUs)
class WhyChooseUsAdmin(admin.ModelAdmin):
    list_display = ('no', 'title', 'image', 'updated_at')
    ordering = ('no',)
    readonly_fields = ('updated_at',)

@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(admin.ModelAdmin):
    list_display = ('no', 'title', 'description',)
    ordering = ('no',) 

@admin.register(OrderPolicy)
class OrderPolicyAdmin(admin.ModelAdmin):
    list_display = ("company_name", "manager", "email", "updated_at")
    search_fields = ("company_name", "manager", "email")
    ordering = ("-updated_at",)

@admin.register(TermsOfService)
class TermsOfServiceAdmin(admin.ModelAdmin):
    list_display = ('no', 'title', 'updated_at') 
    ordering = ('no',)  

@admin.register(AppPolicy)
class OAuthAppPolicyAdmin(admin.ModelAdmin):
    list_display = ("no", "title", "updated_at")
    ordering = ("no",)

@admin.register(Faq)
class FaqAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'no', 'is_published', 'show_on_top', 'updated_at')
    list_editable = ('no', 'is_published', 'show_on_top')
    list_filter = ('category', 'is_published', 'show_on_top')
    search_fields = ('question', 'answer')
    ordering = ('no', 'id')
    readonly_fields = ('updated_at',)
