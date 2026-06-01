from django.db import migrations, models
from django.utils import timezone


def mark_existing_users_onboarded(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    now = timezone.now()
    User.objects.filter(onboarding_completed_at__isnull=True).update(
        onboarding_completed_at=now,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_restore_self_hosted_2fa"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="onboarding_completed_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Eerste gebruikersflow (3 stappen) afgerond.",
                null=True,
                verbose_name="onboarding afgerond",
            ),
        ),
        migrations.RunPython(mark_existing_users_onboarded, migrations.RunPython.noop),
    ]
