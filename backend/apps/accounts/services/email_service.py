"""Email sending service with audit logging."""

import logging

from django.conf import settings
from django.template.loader import render_to_string

from apps.accounts.models import EmailLog, User

logger = logging.getLogger(__name__)


def send_email(
    user: User,
    email_type: str,
    subject: str,
    recipient: str,
    template_data: dict,
) -> EmailLog:
    """Send email via Resend and create audit log entry.

    Args:
        user: User object who is receiving the email
        email_type: One of EmailLog.EmailType choices (verification, password_reset, test)
        subject: Email subject line
        recipient: Recipient email address
        template_data: Dict to pass to email template

    Returns:
        EmailLog object with populated resend_message_id

    Raises:
        Exception: If Resend API fails (email not sent)
    """
    # Render HTML template
    template_path = f"emails/{email_type}.html"
    html_body = render_to_string(template_path, template_data)

    # Send via Resend
    try:
        from resend import Resend
    except ImportError:
        raise ImportError(
            "resend package not installed. "
            "Install it with: pip install resend"
        )

    resend = Resend(api_key=settings.RESEND_API_KEY)
    try:
        response = resend.emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": recipient,
            "subject": subject,
            "html": html_body,
        })
    except Exception as e:
        logger.error(f"Resend API error sending {email_type} email to {recipient}: {str(e)}")
        raise

    # Create audit log entry
    email_log = EmailLog.objects.create(
        user=user,
        recipient_email=recipient,
        email_type=email_type,
        subject=subject,
        resend_message_id=response.get("id") if response else None,
        status=EmailLog.Status.PENDING,
    )

    return email_log
