import logging

from django.conf import settings

from .google.gmail import send_mail_with_gmail
from .models import CompanyInfo

logger = logging.getLogger(__name__)


def sender_name():
    company = CompanyInfo.objects.first()
    return company.name if company else "KiMame"


def notify_admins(*, subject, body):
    """Send a notification mail to every address in ADMIN_EMAIL. Failures are logged, never raised,
    so a mail problem can't break the customer's request."""
    name = sender_name()
    for address in settings.ADMIN_EMAILS:
        try:
            send_mail_with_gmail(to_email=address, subject=subject, body=body, sender_name=name)
        except Exception:
            logger.exception("Failed to send admin notification to %s", address)
