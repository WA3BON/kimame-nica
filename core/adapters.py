from allauth.account.adapter import DefaultAccountAdapter
from django.template.loader import render_to_string

from core.models import CompanyInfo
from core.google.gmail import send_mail_with_gmail


class GmailAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        subject = render_to_string(f'{template_prefix}_subject.txt', context).strip()
        body = render_to_string(f'{template_prefix}_message.txt', context).strip()
        company = CompanyInfo.objects.first()
        send_mail_with_gmail(
            to_email=email,
            subject=subject,
            body=body,
            sender_name=company.name if company else "KiMame",
        )
