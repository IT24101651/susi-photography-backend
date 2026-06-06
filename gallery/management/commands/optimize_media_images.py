from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from gallery.image_utils import optimize_image_file


IMAGE_OPTIONS = {
    'hero': {'max_width': 1600, 'max_height': 1000, 'quality': 70},
    'portfolio': {'max_width': 1800, 'max_height': 1800, 'quality': 78},
    'packages': {'max_width': 1600, 'max_height': 1600, 'quality': 78},
    'about': {'max_width': 1600, 'max_height': 1600, 'quality': 78},
    'team': {'max_width': 1200, 'max_height': 1200, 'quality': 76},
    'testimonials': {'max_width': 900, 'max_height': 900, 'quality': 76},
}


class Command(BaseCommand):
    help = 'Optimize existing media images in place for faster frontend loading.'

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        frontend_public_root = Path(getattr(
            settings,
            'FRONTEND_PUBLIC_ROOT',
            media_root.parent / 'frontend' / 'public',
        ))
        if not media_root.exists():
            self.stdout.write(self.style.WARNING('MEDIA_ROOT does not exist.'))
            return

        total = 0
        for folder, optimize_options in IMAGE_OPTIONS.items():
            folder_paths = [media_root / folder]
            if folder == 'hero':
                folder_paths.append(frontend_public_root / folder)

            for folder_path in folder_paths:
                if not folder_path.exists():
                    continue

                for image_path in folder_path.rglob('*'):
                    if image_path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp'}:
                        continue
                    optimize_image_file(image_path, **optimize_options)
                    total += 1

        self.stdout.write(self.style.SUCCESS(f'Optimized {total} images.'))
