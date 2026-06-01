from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0006_user_onboarding_completed_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="deleted_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Tijdstip van soft-delete (GDPR).",
                null=True,
                verbose_name="verwijderd op",
            ),
        ),
    ]
