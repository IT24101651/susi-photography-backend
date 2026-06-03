import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from gallery.models import HeroSlide, PortfolioCategory, PortfolioImage, AboutSection, TeamMember

PUBLIC = os.path.normpath(os.path.join(settings.BASE_DIR, '..', 'frontend', 'public'))

def img(rel_path):
    return os.path.normpath(os.path.join(PUBLIC, rel_path))


SLIDES = []

CATEGORIES = [
    {'name': 'Birthday',   'slug': 'birthday',   'order': 1},
    {'name': 'Model Shot', 'slug': 'model-shot', 'order': 2},
    {'name': 'Outdoor',    'slug': 'outdoor',    'order': 3},
    {'name': 'Poverty',    'slug': 'poverty',    'order': 4},
    {'name': 'Reception',  'slug': 'reception',  'order': 5},
    {'name': 'Wedding',    'slug': 'wedding',    'order': 6},
]

PORTFOLIO = [
    ('birthday',   img('Birthday/Baby1.jpg'),        'Baby Moments 1', 1),
    ('birthday',   img('Birthday/Baby2.webp'),       'Baby Moments 2', 2),
    ('birthday',   img('Birthday/Baby3.avif'),       'Baby Moments 3', 3),
    ('model-shot', img('Model shot/model1.jpg'),     'Model Shot 1',   1),
    ('model-shot', img('Model shot/model2.jpg'),     'Model Shot 2',   2),
    ('model-shot', img('Model shot/model3.jpg'),     'Model Shot 3',   3),
    ('outdoor',    img('Outdoor/outdoor1.jpeg'),     'Outdoor 1',      1),
    ('outdoor',    img('Outdoor/outdoor2.webp'),     'Outdoor 2',      2),
    ('outdoor',    img('Outdoor/outdoor3.jpg'),      'Outdoor 3',      3),
    ('poverty',    img('Poverty/puberty.jpg'),       'Poverty 1',      1),
    ('poverty',    img('Poverty/puberty2.jpg'),      'Poverty 2',      2),
    ('poverty',    img('Poverty/puberty3.jpg'),      'Poverty 3',      3),
    ('reception',  img('Reception/reception1.webp'), 'Reception 1',    1),
    ('reception',  img('Reception/reception2.jpg'),  'Reception 2',    2),
    ('reception',  img('Reception/reception3.jpeg'), 'Reception 3',    3),
    ('wedding',    img('Wedding/Wedding1.webp'),     'Wedding 1',      1),
    ('wedding',    img('Wedding/wedding2.avif'),     'Wedding 2',      2),
    ('wedding',    img('Wedding/wedding3.jpg'),      'Wedding 3',      3),
]

TEAM = [
    {'name': 'Cody Fisher',   'role': 'Founder',             'photo': img('Team/member1.jpg'),  'order': 1},
    {'name': 'Jacob Jones',   'role': 'Design Team Lead',    'photo': img('Team/member2.avif'), 'order': 2},
    {'name': 'Annette Black', 'role': 'Design Team Lead',    'photo': img('Team/member3.avif'), 'order': 3},
    {'name': 'Jane Cooper',   'role': 'Front End Team Lead', 'photo': img('Team/member4.avif'), 'order': 4},
]

ABOUT = {
    'heading': 'Born from a Passion for Real Moments',
    'subheading': 'Every frame tells a story worth keeping.',
    'body_text': (
        'It started with a single camera and an unshakeable belief - that the most beautiful '
        'photographs are not staged, they are felt.\n\n'
        'Susi Photography was founded on the streets of a small town, where our founder Susi spent '
        'her early mornings chasing golden light and her evenings studying the faces of strangers '
        'who became subjects, then friends.\n\n'
        'Over the years, that belief grew into a team - a family of artists who share the same '
        'obsession with authenticity. From intimate weddings to bold outdoor portraits, from the '
        'quiet tenderness of a newborn\'s first breath to the electric energy of a reception dance '
        'floor, we show up with our whole hearts.\n\n'
        'We don\'t just take pictures. We preserve the moments that make life worth living.'
    ),
    'image': img('Team/team.webp'),
}


def save_file(field, path, name):
    if os.path.exists(path):
        with open(path, 'rb') as f:
            field.save(name, File(f), save=False)
        return True
    return False


class Command(BaseCommand):
    help = 'Seed database with the local images shown on the user site'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Clear existing data before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            HeroSlide.objects.all().delete()
            PortfolioImage.objects.all().delete()
            PortfolioCategory.objects.all().delete()
            TeamMember.objects.all().delete()
            self.stdout.write('Cleared existing data.')

        # Hero Slides
        self.stdout.write('\n-- Hero Slides')
        for s in SLIDES:
            if HeroSlide.objects.filter(title=s['title']).exists():
                self.stdout.write('  Skip: ' + s['title']); continue
            slide = HeroSlide(title=s['title'], subtitle=s['subtitle'], order=s['order'], is_active=True)
            ok = save_file(slide.image, s['image'], os.path.basename(s['image']))
            slide.save()
            self.stdout.write(self.style.SUCCESS('  OK: ' + s['title'] + ('' if ok else ' (no image file)')))

        # Portfolio
        self.stdout.write('\n-- Portfolio Categories')
        cat_map = {}
        for c in CATEGORIES:
            cat, _ = PortfolioCategory.objects.get_or_create(
                slug=c['slug'], defaults={'name': c['name'], 'order': c['order'], 'is_active': True}
            )
            cat_map[c['slug']] = cat
            self.stdout.write('  Category: ' + cat.name)

        self.stdout.write('\n-- Portfolio Images')
        for slug, path, title, order in PORTFOLIO:
            cat = cat_map.get(slug)
            if PortfolioImage.objects.filter(title=title, category=cat).exists():
                self.stdout.write('  Skip: ' + title); continue
            photo = PortfolioImage(title=title, category=cat, order=order, is_featured=(order <= 2))
            ok = save_file(photo.image, path, os.path.basename(path))
            photo.save()
            self.stdout.write(self.style.SUCCESS('  OK: ' + title + ('' if ok else ' (no image file)')))

        # Team
        self.stdout.write('\n-- Team Members')
        for m in TEAM:
            if TeamMember.objects.filter(name=m['name']).exists():
                self.stdout.write('  Skip: ' + m['name']); continue
            member = TeamMember(name=m['name'], role=m['role'], order=m['order'], is_active=True)
            ok = save_file(member.photo, m['photo'], os.path.basename(m['photo']))
            member.save()
            self.stdout.write(self.style.SUCCESS('  OK: ' + m['name'] + ('' if ok else ' (no image file)')))

        # About
        self.stdout.write('\n-- About Section')
        about = AboutSection.load()
        if not about.heading:
            about.heading = ABOUT['heading']
            about.subheading = ABOUT['subheading']
            about.body_text = ABOUT['body_text']
            save_file(about.image, ABOUT['image'], os.path.basename(ABOUT['image']))
            about.save()
            self.stdout.write(self.style.SUCCESS('  OK: About section saved'))
        else:
            self.stdout.write('  Skip: About already has content')

        self.stdout.write(self.style.SUCCESS('\nSeeding complete!'))
