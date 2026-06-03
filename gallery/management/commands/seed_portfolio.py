import urllib.request
import urllib.error
from io import BytesIO
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from gallery.models import PortfolioCategory, PortfolioImage

CATEGORIES = [
    {
        'name': 'Wedding',
        'slug': 'wedding',
        'order': 1,
        'images': [
            ('https://images.unsplash.com/photo-1519741497674-611481863552?w=800&q=80', 'Wedding Ceremony'),
            ('https://images.unsplash.com/photo-1606216794074-735e91aa2c92?w=800&q=80', 'Bride Portrait'),
            ('https://images.unsplash.com/photo-1511285560929-80b456fea0bc?w=800&q=80', 'Wedding Couple'),
            ('https://images.unsplash.com/photo-1465495976277-4387d4b0b4c6?w=800&q=80', 'Wedding Rings'),
            ('https://images.unsplash.com/photo-1583939003579-730e3918a45a?w=800&q=80', 'First Dance'),
            ('https://images.unsplash.com/photo-1591604466107-ec97de577aff?w=800&q=80', 'Wedding Bouquet'),
            ('https://images.unsplash.com/photo-1525772764200-be829a350797?w=800&q=80', 'Wedding Vows'),
            ('https://images.unsplash.com/photo-1507504031003-b417219a0fde?w=800&q=80', 'Wedding Kiss'),
            ('https://images.unsplash.com/photo-1469371670807-013ccf25f16a?w=800&q=80', 'Wedding Party'),
            ('https://images.unsplash.com/photo-1550005809-91ad75fb315f?w=800&q=80', 'Wedding Details'),
        ],
    },
    {
        'name': 'Birthday',
        'slug': 'birthday',
        'order': 2,
        'images': [
            ('https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80', 'Birthday Cake'),
            ('https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=800&q=80', 'Birthday Celebration'),
            ('https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?w=800&q=80', 'Birthday Candles'),
            ('https://images.unsplash.com/photo-1513151233558-d860c5398176?w=800&q=80', 'Birthday Party'),
            ('https://images.unsplash.com/photo-1567696153798-9111f9cd3d0d?w=800&q=80', 'Birthday Balloons'),
            ('https://images.unsplash.com/photo-1602631985686-1bb0e6a8696e?w=800&q=80', 'Birthday Joy'),
            ('https://images.unsplash.com/photo-1543946207-39bd91e70ca7?w=800&q=80', 'Birthday Surprise'),
            ('https://images.unsplash.com/photo-1587653915936-5b6e5e5e5e5e?w=800&q=80', 'Birthday Gifts'),
            ('https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=800&q=80', 'Birthday Fun'),
            ('https://images.unsplash.com/photo-1533294455009-a77b7557d2d1?w=800&q=80', 'Birthday Moments'),
        ],
    },
    {
        'name': 'Model Shot',
        'slug': 'model-shot',
        'order': 3,
        'images': [
            ('https://images.unsplash.com/photo-1529626455594-4ff0802cfb7e?w=800&q=80', 'Fashion Portrait'),
            ('https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&q=80', 'Model Pose'),
            ('https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=800&q=80', 'Studio Shot'),
            ('https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=800&q=80', 'Editorial Look'),
            ('https://images.unsplash.com/photo-1488161628813-04466f872be2?w=800&q=80', 'Model Portrait'),
            ('https://images.unsplash.com/photo-1509631179647-0177331693ae?w=800&q=80', 'Fashion Model'),
            ('https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=800&q=80', 'Runway Style'),
            ('https://images.unsplash.com/photo-1485968579580-b6d095142e6e?w=800&q=80', 'Model Close Up'),
            ('https://images.unsplash.com/photo-1492106087820-71f1a00d2b11?w=800&q=80', 'Glamour Shot'),
            ('https://images.unsplash.com/photo-1500917293891-ef795e70e1f6?w=800&q=80', 'Model Outdoor'),
        ],
    },
    {
        'name': 'Puberty Ceremony',
        'slug': 'puberty-ceremony',
        'order': 4,
        'images': [
            ('https://images.unsplash.com/photo-1604017011826-d3b4c23f8914?w=800&q=80', 'Ceremony Flowers'),
            ('https://images.unsplash.com/photo-1591604466107-ec97de577aff?w=800&q=80', 'Ceremony Decor'),
            ('https://images.unsplash.com/photo-1519225421980-715cb0215aed?w=800&q=80', 'Ceremony Portrait'),
            ('https://images.unsplash.com/photo-1606800052052-a08af7148866?w=800&q=80', 'Ceremony Moments'),
            ('https://images.unsplash.com/photo-1583939003579-730e3918a45a?w=800&q=80', 'Ceremony Family'),
            ('https://images.unsplash.com/photo-1511285560929-80b456fea0bc?w=800&q=80', 'Ceremony Celebration'),
            ('https://images.unsplash.com/photo-1465495976277-4387d4b0b4c6?w=800&q=80', 'Ceremony Details'),
            ('https://images.unsplash.com/photo-1469371670807-013ccf25f16a?w=800&q=80', 'Ceremony Joy'),
            ('https://images.unsplash.com/photo-1550005809-91ad75fb315f?w=800&q=80', 'Ceremony Traditions'),
            ('https://images.unsplash.com/photo-1525772764200-be829a350797?w=800&q=80', 'Ceremony Blessings'),
        ],
    },
    {
        'name': 'Reception',
        'slug': 'reception',
        'order': 5,
        'images': [
            ('https://images.unsplash.com/photo-1478146059778-26028b07395a?w=800&q=80', 'Reception Hall'),
            ('https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=800&q=80', 'Reception Decor'),
            ('https://images.unsplash.com/photo-1464366400600-7168b8af9bc3?w=800&q=80', 'Reception Dinner'),
            ('https://images.unsplash.com/photo-1507504031003-b417219a0fde?w=800&q=80', 'Reception Dance'),
            ('https://images.unsplash.com/photo-1533294455009-a77b7557d2d1?w=800&q=80', 'Reception Toast'),
            ('https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=800&q=80', 'Reception Party'),
            ('https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&q=80', 'Reception Cake'),
            ('https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=800&q=80', 'Reception Guests'),
            ('https://images.unsplash.com/photo-1513151233558-d860c5398176?w=800&q=80', 'Reception Lights'),
            ('https://images.unsplash.com/photo-1567696153798-9111f9cd3d0d?w=800&q=80', 'Reception Moments'),
        ],
    },
    {
        'name': 'Outdoor',
        'slug': 'outdoor',
        'order': 6,
        'images': [
            ('https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&q=80', 'Mountain View'),
            ('https://images.unsplash.com/photo-1501854140801-50d01698950b?w=800&q=80', 'Nature Portrait'),
            ('https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=800&q=80', 'Forest Light'),
            ('https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?w=800&q=80', 'Sunset Shot'),
            ('https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=800&q=80', 'Beach Portrait'),
            ('https://images.unsplash.com/photo-1504701954957-2010ec3bcec1?w=800&q=80', 'Garden Session'),
            ('https://images.unsplash.com/photo-1518173946687-a4c8892bbd9f?w=800&q=80', 'Golden Hour'),
            ('https://images.unsplash.com/photo-1475924156734-496f6cac6ec1?w=800&q=80', 'Outdoor Couple'),
            ('https://images.unsplash.com/photo-1490750967868-88df5691cc5e?w=800&q=80', 'Flower Field'),
            ('https://images.unsplash.com/photo-1500534314209-a25ddb2bd429?w=800&q=80', 'Outdoor Family'),
        ],
    },
]


def fetch_image(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return BytesIO(resp.read())
    except urllib.error.URLError:
        return None


class Command(BaseCommand):
    help = 'Seed portfolio categories and mock images from Unsplash'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Delete existing portfolio data before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            PortfolioImage.objects.all().delete()
            PortfolioCategory.objects.all().delete()
            self.stdout.write('Cleared existing portfolio data.')

        for cat_data in CATEGORIES:
            cat, created = PortfolioCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'order': cat_data['order'],
                    'is_active': True,
                }
            )
            action = 'Created' if created else 'Found'
            self.stdout.write(f'{action} category: {cat.name}')

            for order, (url, title) in enumerate(cat_data['images'], start=1):
                if PortfolioImage.objects.filter(category=cat, title=title).exists():
                    self.stdout.write(f'  Skipping existing: {title}')
                    continue

                self.stdout.write(f'  Downloading: {title}')
                img_data = fetch_image(url)

                photo = PortfolioImage(
                    category=cat,
                    title=title,
                    order=order,
                    is_featured=(order <= 2),
                )

                if img_data:
                    filename = f"{cat_data['slug']}_{order:02d}.jpg"
                    photo.image.save(filename, ContentFile(img_data.read()), save=False)
                    photo.save()
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Saved: {title}'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ✗ Failed to download: {title} — skipped'))

        self.stdout.write(self.style.SUCCESS('\nSeeding complete!'))
