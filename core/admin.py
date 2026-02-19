from traceback import format_tb
from django.contrib import admin
from .models import CompanyInfo, ShippingStep, PrivacyPolicy, OrderPolicy, TermsOfService, AppPolicy

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
    list_display = ('no', 'title', 'description', 'image', 'updated_at')
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