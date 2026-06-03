from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0006_sitesettings_phone_secondary'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='captured_moments_count',
            field=models.PositiveIntegerField(default=1000),
        ),
    ]
