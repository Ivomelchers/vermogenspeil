# Generated migration for OKX domain selection (regional API endpoints)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0007_platformconnection_api_passphrase'),
    ]

    operations = [
        migrations.AddField(
            model_name='platformconnection',
            name='okx_domain',
            field=models.CharField(
                choices=[
                    ('okx.com', 'okx.com (Global - www.okx.com)'),
                    ('eea.okx.com', 'eea.okx.com (EU/Nederland - my.okx.com)'),
                    ('us.okx.com', 'us.okx.com (US/AU - app.okx.com)'),
                ],
                default='okx.com',
                help_text='OKX API domein gebaseerd op registratielocatie',
                max_length=32,
            ),
        ),
    ]
