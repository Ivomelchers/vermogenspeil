import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PeilDatumSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.PositiveIntegerField(verbose_name="belastingjaar / peildatum-jaar")),
                ("data", models.JSONField(verbose_name="snapshot payload")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="peildatum_snapshots",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "peildatum-snapshot",
                "verbose_name_plural": "peildatum-snapshots",
                "ordering": ["-year"],
            },
        ),
        migrations.AddConstraint(
            model_name="peildatumsnapshot",
            constraint=models.UniqueConstraint(
                fields=("user", "year"),
                name="unique_peildatum_snapshot_per_user_year",
            ),
        ),
    ]
