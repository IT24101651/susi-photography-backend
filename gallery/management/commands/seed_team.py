import urllib.request
import urllib.error
from io import BytesIO
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from gallery.models import TeamMember

MEMBERS = [
    {
        'name': 'Susi Priya',
        'role': 'Lead Photographer & Founder',
        'bio': 'With over 12 years behind the lens, Susi founded the studio with a passion for capturing raw, emotional moments. Specialises in weddings and portraits.',
        'instagram_url': 'https://instagram.com',
        'photo_url': 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=600&q=80',
        'order': 1,
    },
    {
        'name': 'Arjun Mehta',
        'role': 'Senior Wedding Photographer',
        'bio': 'Arjun brings a cinematic eye to every wedding, blending candid storytelling with artistic composition. 8 years of experience across South India.',
        'instagram_url': 'https://instagram.com',
        'photo_url': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600&q=80',
        'order': 2,
    },
    {
        'name': 'Meera Nair',
        'role': 'Portrait & Fashion Photographer',
        'bio': 'Meera specialises in editorial portraits and fashion shoots. Her work has been featured in regional lifestyle magazines.',
        'instagram_url': 'https://instagram.com',
        'photo_url': 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=600&q=80',
        'order': 3,
    },
    {
        'name': 'Karthik Rajan',
        'role': 'Outdoor & Nature Photographer',
        'bio': 'Karthik chases golden hour light across landscapes and outdoor sessions. Known for his dramatic use of natural light.',
        'instagram_url': 'https://instagram.com',
        'photo_url': 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=600&q=80',
        'order': 4,
    },
    {
        'name': 'Divya Krishnan',
        'role': 'Event & Ceremony Photographer',
        'bio': 'Divya covers puberty ceremonies, receptions, and cultural events with sensitivity and attention to tradition.',
        'instagram_url': 'https://instagram.com',
        'photo_url': 'https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=600&q=80',
        'order': 5,
    },
    {
        'name': 'Rahul Sharma',
        'role': 'Videographer & Cinematographer',
        'bio': 'Rahul crafts cinematic wedding films and event highlight reels that couples treasure for a lifetime.',
        'instagram_url': 'https://instagram.com',
        'photo_url': 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=600&q=80',
        'order': 6,
    },
    {
        'name': 'Priya Sundaram',
        'role': 'Photo Editor & Retoucher',
        'bio': 'Priya is the magic behind the final images — her colour grading and retouching give every photo its signature warm tone.',
        'instagram_url': 'https://instagram.com',
        'photo_url': 'https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=600&q=80',
        'order': 7,
    },
    {
        'name': 'Vikram Das',
        'role': 'Second Shooter',
        'bio': 'Vikram works alongside the lead photographer to ensure no moment is missed, covering multiple angles simultaneously.',
        'instagram_url': 'https://instagram.com',
        'photo_url': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=600&q=80',
        'order': 8,
    },
    {
        'name': 'Ananya Pillai',
        'role': 'Studio Manager & Coordinator',
        'bio': 'Ananya ensures every shoot runs smoothly — from client consultations to on-day coordination and delivery timelines.',
        'instagram_url': 'https://instagram.com',
        'photo_url': 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=600&q=80',
        'order': 9,
    },
    {
        'name': 'Suresh Babu',
        'role': 'Lighting Technician',
        'bio': 'Suresh manages studio and on-location lighting setups, ensuring perfect exposure in every environment.',
        'instagram_url': 'https://instagram.com',
        'photo_url': 'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=600&q=80',
        'order': 10,
    },
    {
        'name': 'Lakshmi Venkat',
        'role': 'Social Media & Marketing',
        'bio': 'Lakshmi curates the studio\'s online presence, managing Instagram, client galleries, and brand storytelling.',
        'instagram_url': 'https://instagram.com',
        'photo_url': 'https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=600&q=80',
        'order': 11,
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
    help = 'Seed 11 team members with mock photos'

    def add_arguments(self, parser):
        parser.add_argument('--clear', action='store_true', help='Delete existing team members before seeding')

    def handle(self, *args, **options):
        if options['clear']:
            TeamMember.objects.all().delete()
            self.stdout.write('Cleared existing team members.')

        for m in MEMBERS:
            if TeamMember.objects.filter(name=m['name']).exists():
                self.stdout.write(f"Skipping existing: {m['name']}")
                continue

            self.stdout.write(f"Downloading photo for: {m['name']}")
            img_data = fetch_image(m['photo_url'])

            member = TeamMember(
                name=m['name'],
                role=m['role'],
                bio=m['bio'],
                instagram_url=m['instagram_url'],
                order=m['order'],
                is_active=True,
            )

            if img_data:
                filename = f"team_{m['order']:02d}.jpg"
                member.photo.save(filename, ContentFile(img_data.read()), save=False)
                member.save()
                self.stdout.write(self.style.SUCCESS(f"  ✓ Saved: {m['name']} — {m['role']}"))
            else:
                member.save()
                self.stdout.write(self.style.WARNING(f"  ✗ No photo: {m['name']} — saved without image"))

        self.stdout.write(self.style.SUCCESS('\nTeam seeding complete!'))
