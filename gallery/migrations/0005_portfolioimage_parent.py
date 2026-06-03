from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0004_sitesettings_tiktok_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='portfolioimage',
            name='parent',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='gallery_images',
                to='gallery.portfolioimage',
            ),
        ),
    ]
