from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0003_packagecard'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='tiktok_url',
            field=models.URLField(blank=True),
        ),
    ]
