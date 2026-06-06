from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, TransactionTestCase, override_settings
from PIL import Image

from .models import HeroSlide, PortfolioCategory, PortfolioImage
from .admin import PortfolioImageAdmin
from .image_utils import get_local_file_path, get_public_image_url
from .serializers import PortfolioImageWriteSerializer


class PortfolioImageWriteSerializerTests(TestCase):
    def setUp(self):
        self.wedding_category = PortfolioCategory.objects.create(
            name='Wedding',
            slug='wedding',
            order=1,
            is_active=True,
        )
        self.portrait_category = PortfolioCategory.objects.create(
            name='Portrait',
            slug='portrait',
            order=2,
            is_active=True,
        )

    def _make_image_upload(self, name='photo.jpg', color='blue'):
        buffer = BytesIO()
        Image.new('RGB', (48, 48), color=color).save(buffer, format='JPEG', quality=85)
        return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/jpeg')

    def _create_wedding_parent_with_gallery(self):
        parent = PortfolioImage.objects.create(
            category=self.wedding_category,
            title='Wedding Story',
            subtitle='',
            description='',
            wedding_type='hindu',
            shoot_phase='',
            order=1,
        )
        child = PortfolioImage.objects.create(
            parent=parent,
            category=self.wedding_category,
            title='Wedding Story Gallery 1',
            subtitle='',
            description='',
            wedding_type='hindu',
            shoot_phase='pre_wedding',
            order=1,
        )
        return parent, child

    def test_create_batches_gallery_uploads_with_matching_shoot_phases(self):
        serializer = PortfolioImageWriteSerializer(
            data={
                'category': self.wedding_category.pk,
                'title': 'Wedding Story',
                'subtitle': '',
                'description': 'Batch upload test',
                'wedding_type': 'hindu',
                'shoot_phase': '',
                'order': 1,
                'is_featured': False,
                'image': self._make_image_upload('main.jpg', 'navy'),
                'gallery_uploads': [
                    self._make_image_upload('gallery-1.jpg', 'red'),
                    self._make_image_upload('gallery-2.jpg', 'green'),
                ],
                'gallery_upload_shoot_phases': ['pre_wedding', 'wedding_day'],
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        parent = serializer.save()

        gallery = list(parent.gallery_images.order_by('order'))
        self.assertEqual(len(gallery), 2)
        self.assertEqual([image.shoot_phase for image in gallery], ['pre_wedding', 'wedding_day'])
        self.assertEqual([image.title for image in gallery], ['Wedding Story Gallery 1', 'Wedding Story Gallery 2'])

    def test_create_batches_cloudinary_public_ids_with_matching_shoot_phases(self):
        serializer = PortfolioImageWriteSerializer(
            data={
                'category': self.wedding_category.pk,
                'title': 'Wedding Story',
                'subtitle': '',
                'description': 'Direct upload test',
                'wedding_type': 'hindu',
                'shoot_phase': '',
                'order': 1,
                'is_featured': False,
                'image_public_id': 'portfolio/main-story',
                'gallery_upload_public_ids': ['portfolio/gallery-1', 'portfolio/gallery-2'],
                'gallery_upload_shoot_phases': ['pre_wedding', 'wedding_day'],
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        parent = serializer.save()

        parent.refresh_from_db()
        self.assertEqual(parent.image.name, 'portfolio/main-story')

        gallery = list(parent.gallery_images.order_by('order'))
        self.assertEqual(len(gallery), 2)
        self.assertEqual([image.image.name for image in gallery], ['portfolio/gallery-1', 'portfolio/gallery-2'])
        self.assertEqual([image.shoot_phase for image in gallery], ['pre_wedding', 'wedding_day'])

    def test_update_keeps_existing_gallery_shoot_phase_when_category_stays_same(self):
        parent, child = self._create_wedding_parent_with_gallery()

        serializer = PortfolioImageWriteSerializer(
            instance=parent,
            data={
                'category': self.wedding_category.pk,
                'title': 'Wedding Story Updated',
                'subtitle': '',
                'description': '',
                'wedding_type': 'hindu',
                'shoot_phase': '',
                'order': 1,
                'is_featured': False,
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        child.refresh_from_db()
        self.assertEqual(child.shoot_phase, 'pre_wedding')
        self.assertEqual(child.wedding_type, 'hindu')

    def test_update_clears_gallery_shoot_phase_when_category_changes(self):
        parent, child = self._create_wedding_parent_with_gallery()

        serializer = PortfolioImageWriteSerializer(
            instance=parent,
            data={
                'category': self.portrait_category.pk,
                'title': 'Portrait Story',
                'subtitle': '',
                'description': '',
                'wedding_type': '',
                'shoot_phase': '',
                'order': 1,
                'is_featured': False,
            },
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        child.refresh_from_db()
        self.assertEqual(child.shoot_phase, '')
        self.assertEqual(child.category_id, self.portrait_category.id)


class BackfillWeddingShootPhasesTests(TestCase):
    def setUp(self):
        self.wedding_category = PortfolioCategory.objects.create(
            name='Wedding',
            slug='wedding',
            order=1,
            is_active=True,
        )

    def test_backfill_assigns_phases_by_gallery_order(self):
        parent = PortfolioImage.objects.create(
            category=self.wedding_category,
            title='Wedding Story',
            subtitle='',
            description='',
            wedding_type='hindu',
            shoot_phase='',
            order=1,
        )

        children = [
            PortfolioImage.objects.create(
                parent=parent,
                category=self.wedding_category,
                title=f'Wedding Story Gallery {index + 1}',
                subtitle='',
                description='',
                wedding_type='hindu',
                shoot_phase='',
                order=index + 1,
            )
            for index in range(4)
        ]

        call_command('backfill_wedding_shoot_phases')

        for image, expected_phase in zip(children, ['pre_wedding', 'wedding_day', 'post_wedding', 'post_wedding']):
            image.refresh_from_db()
            self.assertEqual(image.shoot_phase, expected_phase)


class PortfolioImageAdminBulkDeleteTests(TransactionTestCase):
    def setUp(self):
        self.wedding_category = PortfolioCategory.objects.create(
            name='Wedding',
            slug='wedding',
            order=1,
            is_active=True,
        )

    def test_bulk_delete_removes_parent_and_child_media_files(self):
        with TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            parent = PortfolioImage.objects.create(
                category=self.wedding_category,
                title='Wedding Story',
                subtitle='',
                description='',
                wedding_type='hindu',
                shoot_phase='',
                order=1,
                image=SimpleUploadedFile('parent.jpg', b'parent-image-bytes'),
            )
            child = PortfolioImage.objects.create(
                parent=parent,
                category=self.wedding_category,
                title='Wedding Story Gallery 1',
                subtitle='',
                description='',
                wedding_type='hindu',
                shoot_phase='pre_wedding',
                order=1,
                image=SimpleUploadedFile('child.jpg', b'child-image-bytes'),
            )

            parent_file = Path(parent.image.name)
            child_file = Path(child.image.name)

            admin = PortfolioImageAdmin(PortfolioImage, AdminSite())
            admin.delete_queryset(None, PortfolioImage.objects.filter(pk__in=[parent.pk, child.pk]))

            self.assertFalse(PortfolioImage.objects.filter(pk=parent.pk).exists())
            self.assertFalse(PortfolioImage.objects.filter(pk=child.pk).exists())
            self.assertFalse((Path(media_root) / parent_file).exists())
            self.assertFalse((Path(media_root) / child_file).exists())


class LocalFilePathHelperTests(TestCase):
    def test_returns_none_when_storage_has_no_local_path(self):
        class RemoteFile:
            @property
            def path(self):
                raise NotImplementedError

        self.assertIsNone(get_local_file_path(RemoteFile()))

    def test_returns_local_path_when_file_exists(self):
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / 'photo.jpg'
            file_path.write_bytes(b'photo-bytes')

            class LocalFile:
                def __init__(self, path):
                    self._path = path

                @property
                def path(self):
                    return self._path

            self.assertEqual(get_local_file_path(LocalFile(str(file_path))), file_path)


class PublicImageUrlHelperTests(TestCase):
    @override_settings(USE_CLOUDINARY_STORAGE=True)
    @patch('cloudinary.utils.cloudinary_url')
    def test_strips_media_prefix_for_cloudinary_urls(self, mock_cloudinary_url):
        mock_cloudinary_url.return_value = ('https://res.cloudinary.com/example/image/upload/v1/hero/10.jpg', {})

        class CloudinaryFile:
            name = 'media/hero/10'

        url = get_public_image_url(CloudinaryFile())

        self.assertEqual(url, 'https://res.cloudinary.com/example/image/upload/v1/hero/10.jpg')
        mock_cloudinary_url.assert_called_once_with(
            'hero/10',
            secure=True,
            resource_type='image',
            format=None,
        )

    @override_settings(USE_CLOUDINARY_STORAGE=True)
    @patch('cloudinary.utils.cloudinary_url')
    def test_preserves_image_format_suffix_in_public_id(self, mock_cloudinary_url):
        mock_cloudinary_url.return_value = ('https://res.cloudinary.com/example/image/upload/v1/packages/IMG_1422.JPG.jpg', {})

        class CloudinaryFile:
            name = 'media/packages/IMG_1422.JPG'

        url = get_public_image_url(CloudinaryFile())

        self.assertEqual(url, 'https://res.cloudinary.com/example/image/upload/v1/packages/IMG_1422.JPG.jpg')
        mock_cloudinary_url.assert_called_once_with(
            'packages/IMG_1422.JPG',
            secure=True,
            resource_type='image',
            format='jpg',
        )


class ImageOptimizationUploadTests(TestCase):
    def test_uploaded_images_are_resized_before_storage(self):
        with TemporaryDirectory() as public_root, override_settings(FRONTEND_PUBLIC_ROOT=public_root):
            image = Image.new('RGB', (3200, 2400), color='red')
            buffer = BytesIO()
            image.save(buffer, format='JPEG', quality=95)

            slide = HeroSlide.objects.create(
                title='Hero',
                subtitle='Subtitle',
                image=SimpleUploadedFile('hero.jpg', buffer.getvalue(), content_type='image/jpeg'),
                order=1,
                is_active=True,
            )

            stored_path = Path(public_root) / slide.image.name
            self.assertTrue(stored_path.exists())

            with Image.open(stored_path) as stored_image:
                self.assertLessEqual(stored_image.size[0], 1600)
                self.assertLessEqual(stored_image.size[1], 1000)
