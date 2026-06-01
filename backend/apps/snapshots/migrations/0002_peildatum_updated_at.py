from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("snapshots", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="peildatumsnapshot",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
