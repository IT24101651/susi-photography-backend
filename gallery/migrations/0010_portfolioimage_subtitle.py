from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('gallery', '0009_portfolioimage_shoot_phase'),
    ]

    operations = [
        migrations.AddField(
            model_name='portfolioimage',
            name='subtitle',
            field=models.CharField(blank=True, default='', max_length=300),
        ),
    ]
