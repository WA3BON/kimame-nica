from django.conf import settings
from .models import CompanyInfo

def company_info(request):
    company = CompanyInfo.objects.order_by("-updated_at").first()
    return {"company_info": company}

def turnstile(request):
    return {"TURNSTILE_SITE_KEY": settings.TURNSTILE_SITE_KEY}
