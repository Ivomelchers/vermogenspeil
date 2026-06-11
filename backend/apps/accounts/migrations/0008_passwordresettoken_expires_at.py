from django.db import migrations, models
from django.utils import timezone
from datetime import timedelta


def set_expiry_times(apps, schema_editor):
    PasswordResetToken = apps.get_model("accounts", "PasswordResetToken")
    PASSWORD_RESET_TOKEN_HOURS = 1
    for token in PasswordResetToken.objects.filter(expires_at__isnull=True):
        token.expires_at = token.created_at + timedelta(hours=PASSWORD_RESET_TOKEN_HOURS)
        token.save(update_fields=["expires_at"])


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_user_deleted_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="passwordresettoken",
            name="expires_at",
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text="Token expiration timestamp.",
            ),
        ),
        migrations.RunPython(set_expiry_times),
        migrations.AlterField(
            model_name="passwordresettoken",
            name="expires_at",
            field=models.DateTimeField(
                help_text="Token expiration timestamp.",
            ),
        ),
    ]
