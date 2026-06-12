from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.accounts.models import EmailLog
from apps.accounts.services.email_service import send_email

User = get_user_model()


class Command(BaseCommand):
    help = "Send a test email to verify Resend integration"

    def add_arguments(self, parser):
        parser.add_argument(
            "email",
            type=str,
            help="Email address to send test email to",
        )

    def handle(self, *args, **options):
        recipient_email = options["email"]

        try:
            user = User.objects.filter(email="system@verbox.nl").first()
            if not user:
                user = User.objects.first()
            if not user:
                self.stdout.write(
                    self.style.ERROR("No users found in database. Create a user first.")
                )
                return

            self.stdout.write(f"Sending test email to {recipient_email}...")

            send_email(
                user=user,
                email_type=EmailLog.EmailType.TEST,
                subject="Test Email — Vermogenspeil",
                recipient=recipient_email,
                template_data={"test_message": "This is a test email from Vermogenspeil"},
            )

            self.stdout.write(
                self.style.SUCCESS(f"[OK] Test email sent to {recipient_email}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"[ERROR] Failed to send email: {str(e)}")
            )
