from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("integrations", "0005_sharedcsvcolumnalias_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="platformconnection",
            name="api_passphrase_encrypted",
            field=models.TextField(blank=True, default=""),
        ),
    ]
