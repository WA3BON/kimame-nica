from .models import CompanyInfo

def company_info(request):
    company = CompanyInfo.objects.first()
    return {"company_info": company}
