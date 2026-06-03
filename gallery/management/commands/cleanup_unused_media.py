from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from gallery.models import (
    AboutSection,
    HeroSlide,
    PackageCard,
    PortfolioImage,
    TeamMember,
    Testimonial,
)


TRACKED_IMAGE_FIELDS = (
    (HeroSlide, 'image'),
    (PortfolioImage, 'image'),
    (PackageCard, 'image'),
    (AboutSection, 'image'),
    (TeamMember, 'photo'),
    (Testimonial, 'client_photo'),
)

VALID_IMAGE_SUFFIXES = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tif', '.tiff'}


class Command(BaseCommand):
    help = 'Delete unused image files from MEDIA_ROOT that are no longer referenced by the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which files would be deleted without removing them.',
        )

    def handle(self, *args, **options):
        media_root = Path(settings.MEDIA_ROOT)
        dry_run = options['dry_run']

        if not media_root.exists():
            self.stdout.write(self.style.WARNING('MEDIA_ROOT does not exist.'))
            return

        referenced_files = self._get_referenced_files()
        all_media_files = self._get_media_files(media_root)
        orphaned_files = sorted(all_media_files - referenced_files)

        if not orphaned_files:
            self.stdout.write(self.style.SUCCESS('No unused media files found.'))
            return

        for relative_path in orphaned_files:
            self.stdout.write(str(relative_path))

        if dry_run:
            self.stdout.write(self.style.WARNING(f'Dry run complete. {len(orphaned_files)} files would be deleted.'))
            return

        deleted_count = 0
        for relative_path in orphaned_files:
            absolute_path = media_root / relative_path
            if absolute_path.exists():
                absolute_path.unlink()
                deleted_count += 1

        self._remove_empty_directories(media_root)
        self.stdout.write(self.style.SUCCESS(f'Deleted {deleted_count} unused media files.'))

    def _get_referenced_files(self):
        referenced_files = set()

        for model_class, field_name in TRACKED_IMAGE_FIELDS:
            for file_name in model_class.objects.exclude(**{field_name: ''}).values_list(field_name, flat=True):
                if file_name:
                    referenced_files.add(Path(file_name))

        return referenced_files

    def _get_media_files(self, media_root):
        media_files = set()
        for file_path in media_root.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in VALID_IMAGE_SUFFIXES:
                media_files.add(file_path.relative_to(media_root))
        return media_files

    def _remove_empty_directories(self, media_root):
        for directory in sorted((path for path in media_root.rglob('*') if path.is_dir()), reverse=True):
            if directory == media_root:
                continue
            try:
                next(directory.iterdir())
            except StopIteration:
                directory.rmdir()
