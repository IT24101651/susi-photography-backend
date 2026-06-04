from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError


def get_local_file_path(file_field):
    if not file_field:
        return None

    try:
        path = Path(file_field.path)
    except (AttributeError, NotImplementedError, ValueError):
        return None

    if not path.exists():
        return None

    return path


def get_public_image_url(file_field):
    if not file_field:
        return None

    try:
        file_name = file_field.name or ''
    except AttributeError:
        file_name = ''

    if not file_name:
        return None

    if file_name.startswith(('http://', 'https://')):
        return file_name

    if not getattr(settings, 'USE_CLOUDINARY_STORAGE', False):
        try:
            return file_field.url
        except (AttributeError, ValueError, NotImplementedError):
            return None

    public_id = file_name
    suffix = Path(public_id).suffix.lower()
    cloudinary_format = suffix.lstrip('.') if suffix in {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.avif'} else None

    try:
        from cloudinary.utils import cloudinary_url
    except ImportError:
        try:
            return file_field.url
        except (AttributeError, ValueError, NotImplementedError):
            return None

    url, _ = cloudinary_url(
        public_id,
        secure=True,
        resource_type='image',
        format=cloudinary_format,
    )
    return url


def optimize_uploaded_image_file(
    uploaded_file,
    *,
    max_width=2200,
    max_height=2200,
    quality=82,
    max_file_size=None,
):
    if not uploaded_file:
        return None

    file_name = getattr(uploaded_file, 'name', '') or 'image'
    source = getattr(uploaded_file, 'file', uploaded_file)

    try:
        source.seek(0)
    except (AttributeError, OSError, ValueError):
        pass

    try:
        raw_bytes = source.read()
    except (AttributeError, OSError, ValueError):
        return None

    if not raw_bytes:
        return None

    extension = Path(file_name).suffix.lower()
    if extension in {'.jpg', '.jpeg'}:
        output_format = 'jpeg'
        output_extension = '.jpg'
    elif extension == '.webp':
        output_format = 'webp'
        output_extension = '.webp'
    elif extension == '.png':
        output_format = 'png'
        output_extension = '.png'
    else:
        output_format = 'jpeg'
        output_extension = '.jpg'

    attempt_plan = [
        (1.0, quality),
    ]
    if max_file_size is not None:
        attempt_plan.extend([
            (0.85, max(quality - 12, 70)),
            (0.7, max(quality - 24, 60)),
        ])

    def _save_image(image, current_quality):
        save_kwargs = {'optimize': True}

        if output_format == 'jpeg':
            if image.mode in ('RGBA', 'LA') or ('transparency' in image.info):
                rgba = image.convert('RGBA')
                background = Image.new('RGB', rgba.size, (255, 255, 255))
                background.paste(rgba, mask=rgba.getchannel('A'))
                image = background
            elif image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')
            save_kwargs.update({
                'format': 'JPEG',
                'quality': current_quality,
                'progressive': True,
            })
        elif output_format == 'webp':
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGBA' if ('transparency' in image.info) else 'RGB')
            save_kwargs.update({
                'format': 'WEBP',
                'quality': current_quality,
                'method': 4,
            })
        else:
            if image.mode not in ('RGB', 'RGBA', 'L'):
                image = image.convert('RGBA')
            save_kwargs.update({'format': 'PNG'})

        output = BytesIO()
        image.save(output, **save_kwargs)
        return output.getvalue()

    for scale, current_quality in attempt_plan:
        try:
            with Image.open(BytesIO(raw_bytes)) as img:
                img = ImageOps.exif_transpose(img)
                target_size = (
                    max(1, int(max_width * scale)),
                    max(1, int(max_height * scale)),
                )
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                data = _save_image(img, current_quality)
                optimized_name = Path(file_name).with_suffix(output_extension).name

                if max_file_size is None or len(data) <= max_file_size:
                    return ContentFile(data, name=optimized_name)
        except (UnidentifiedImageError, OSError, ValueError):
            continue

    return None


def optimize_image_file(file_path, *, max_width=2200, max_height=2200, quality=82):
    path = Path(file_path)
    if not path.exists():
        return

    try:
        with Image.open(path) as img:
            img = ImageOps.exif_transpose(img)
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            extension = path.suffix.lower()
            save_kwargs = {'optimize': True}

            if extension in {'.jpg', '.jpeg'}:
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                save_kwargs.update({
                    'format': 'JPEG',
                    'quality': quality,
                    'progressive': True,
                })
            elif extension == '.webp':
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
                save_kwargs.update({
                    'format': 'WEBP',
                    'quality': quality,
                    'method': 6,
                })
            elif extension == '.png':
                if img.mode not in ('RGB', 'RGBA', 'L'):
                    img = img.convert('RGBA')
                save_kwargs.update({'format': 'PNG'})
            else:
                if img.mode not in ('RGB', 'L'):
                    img = img.convert('RGB')
                save_kwargs.update({
                    'format': 'JPEG',
                    'quality': quality,
                    'progressive': True,
                })

            img.save(path, **save_kwargs)
    except (UnidentifiedImageError, OSError):
        return
