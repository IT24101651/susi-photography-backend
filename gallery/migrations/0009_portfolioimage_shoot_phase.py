from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gallery', '0008_portfolioimage_wedding_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='portfolioimage',
            name='shoot_phase',
            field=models.CharField(
                blank=True,
                choices=[
                    ('pre_wedding', 'Pre-Wedding Shoot'),
                    ('wedding_day', 'Wedding Day Shoot'),
                    ('post_wedding', 'Post-Wedding Shoot'),
                ],
                default='',
                max_length=20,
            ),
        ),
    ]
