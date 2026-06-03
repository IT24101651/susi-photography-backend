from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0007_sitesettings_captured_moments_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='portfolioimage',
            name='wedding_type',
            field=models.CharField(
                blank=True,
                choices=[
                    ('hindu', 'Hindu Wedding'),
                    ('christian', 'Christian Wedding'),
                    ('sinhala', 'Sinhala Wedding'),
                ],
                default='',
                max_length=20,
            ),
        ),
    ]
