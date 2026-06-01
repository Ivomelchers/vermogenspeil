from django.db import migrations


def seed_parameters(apps, schema_editor):
    from apps.tax.services.parameters import ensure_default_parameters

    ensure_default_parameters()


class Migration(migrations.Migration):
    dependencies = [
        ("tax", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_parameters, migrations.RunPython.noop),
    ]
