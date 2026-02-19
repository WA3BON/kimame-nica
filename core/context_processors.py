from .models import CompanyInfo

def company_info(request):
    company = CompanyInfo.objects.order_by("-updated_at").first()
    return {"company_info": company}
