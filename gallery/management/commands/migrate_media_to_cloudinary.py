from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from gallery.image_utils import optimize_uploaded_image_file
from gallery.models import (
    AboutSection,
    HeroSlide,
    PackageCard,
    PortfolioImage,
    TeamMember,
    Testimonial,
)


TRACKED_IMAGE_FIELDS = (
    (HeroSlide, ('image',)),
    (PortfolioImage, ('image',)),
    (PackageCard, ('image',)),
    (AboutSection, ('image',)),
    (TeamMember, ('photo',)),
    (Testimonial, ('client_photo',)),
)


class Command(BaseCommand):
    help = 'Upload existing local media files to Cloudinary and update the stored image paths.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which files would be migrated without uploading or saving anything.',
        )
        parser.add_argument(
            '--delete-local',
            action='store_true',
            help='Remove the local media file after a successful Cloudinary upload.',
        )

    def handle(self, *args, **options):
        cloud_name = settings.CLOUDINARY_CLOUD_NAME
        api_key = settings.CLOUDINARY_API_KEY
        api_secret = settings.CLOUDINARY_API_SECRET

        if not all([cloud_name, api_key, api_secret]):
            raise CommandError(
                'Cloudinary credentials are missing. Set CLOUDINARY_CLOUD_NAME, '
                'CLOUDINARY_API_KEY, and CLOUDINARY_API_SECRET first.'
            )

        try:
            import cloudinary
            from cloudinary import uploader
            from cloudinary.exceptions import Error as CloudinaryError
        except ImportError as exc:
            raise CommandError(
                'Cloudinary packages are not installed. Run pip install -r backend/requirements.txt first.'
            ) from exc

        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True,
        )

        media_root = Path(settings.MEDIA_ROOT)
        if not media_root.exists():
            self.stdout.write(self.style.WARNING('MEDIA_ROOT does not exist.'))
            return

        dry_run = options['dry_run']
        delete_local = options['delete_local']

        migrated_count = 0
        skipped_count = 0

        for model_class, field_names in TRACKED_IMAGE_FIELDS:
            for obj in model_class.objects.all().iterator():
                changed_fields = []
                local_paths_to_delete = []
                for field_name in field_names:
                    file_field = getattr(obj, field_name)
                    file_name = getattr(file_field, 'name', '')
                    if not file_name:
                        continue

                    local_path = self._resolve_local_path(media_root, file_name)
                    if not local_path.exists():
                        skipped_count += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'Skipping {model_class.__name__} #{obj.pk} {field_name}: '
                                f'local file not found at {local_path}.'
                            )
                        )
                        continue

                    public_id = Path(file_name).with_suffix('').as_posix()
                    if dry_run:
                        migrated_count += 1
                        self.stdout.write(
                            f'[dry-run] {model_class.__name__} #{obj.pk} {field_name} -> {public_id}'
                        )
                        continue

                    file_bytes = local_path.read_bytes()
                    original_upload = SimpleUploadedFile(
                        local_path.name,
                        file_bytes,
                        content_type='application/octet-stream',
                    )
                    optimized_upload = optimize_uploaded_image_file(
                        original_upload,
                        **{
                            **model_class.optimized_image_fields[field_name],
                            'max_file_size': 9_500_000,
                        },
                    )
                    upload_source = optimized_upload or original_upload
                    try:
                        upload_source.seek(0)
                    except (AttributeError, OSError, ValueError):
                        pass
                    upload_buffer = BytesIO(upload_source.read())
                    upload_buffer.name = getattr(upload_source, 'name', local_path.name)

                    try:
                        result = uploader.upload(
                            upload_buffer,
                            public_id=public_id,
                            resource_type='image',
                            overwrite=True,
                            unique_filename=False,
                            use_filename=False,
                        )
                    except CloudinaryError as exc:
                        message = str(exc)
                        if 'File size too large' in message:
                            skipped_count += 1
                            self.stdout.write(
                                self.style.WARNING(
                                    f'Skipping {model_class.__name__} #{obj.pk} {field_name}: '
                                    'Cloudinary still rejected the resized file because it is over the '
                                    'plan limit.'
                                )
                            )
                            continue
                        raise

                    uploaded_public_id = result.get('public_id', public_id)
                    setattr(obj, field_name, uploaded_public_id)
                    changed_fields.append(field_name)
                    migrated_count += 1

                    if delete_local and local_path.exists():
                        local_paths_to_delete.append(local_path)

                if changed_fields and not dry_run:
                    with transaction.atomic():
                        obj.save(update_fields=changed_fields)
                    for local_path in local_paths_to_delete:
                        if local_path.exists():
                            local_path.unlink()

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Dry run complete. {migrated_count} files would be uploaded and {skipped_count} would be skipped.'
                )
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'Migrated {migrated_count} files to Cloudinary. Skipped {skipped_count} missing local files.'
            )
        )

    def _resolve_local_path(self, media_root, file_name):
        direct_path = media_root / file_name
        if direct_path.exists():
            return direct_path

        base_name = Path(file_name).stem
        parent = direct_path.parent
        if not parent.exists():
            return direct_path

        matches = sorted(parent.glob(f'{base_name}.*'))
        if matches:
            return matches[0]

        return direct_path
