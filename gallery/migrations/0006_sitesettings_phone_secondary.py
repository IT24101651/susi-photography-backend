from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0005_portfolioimage_parent'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='phone_secondary',
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
