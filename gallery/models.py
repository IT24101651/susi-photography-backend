from django.conf import settings
from django.db import models, transaction
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator

from .image_utils import optimize_uploaded_image_file


class OptimizedImageModelMixin(models.Model):
    optimized_image_fields = {}

    class Meta:
        abstract = True

    def _get_tracked_image_field_names(self):
        tracked = set(self.optimized_image_fields.keys())
        for field in self._meta.fields:
            if isinstance(field, models.ImageField):
                tracked.add(field.name)
        return tracked

    def _delete_file_if_unused(self, field_name, file_name):
        if not file_name:
            return

        field = self._meta.get_field(field_name)
        model_class = type(self)
        in_use_elsewhere = model_class.objects.exclude(pk=self.pk).filter(**{field_name: file_name}).exists()
        if not in_use_elsewhere:
            field.storage.delete(file_name)

    def save(self, *args, **kwargs):
        replaced_files = []
        tracked_image_fields = self._get_tracked_image_field_names()
        previous = None

        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).first()

        if previous:
            for field_name in tracked_image_fields:
                previous_file = getattr(previous, field_name, None)
                current_file = getattr(self, field_name, None)
                previous_name = previous_file.name if previous_file else None
                current_name = current_file.name if current_file else None
                if previous_name and previous_name != current_name:
                    replaced_files.append((field_name, previous_name))

        if self.optimized_image_fields:
            for field_name in self.optimized_image_fields:
                current_file = getattr(self, field_name)
                if not current_file:
                    continue

                should_optimize = not getattr(current_file, '_committed', True)

                if should_optimize:
                    optimize_kwargs = dict(self.optimized_image_fields[field_name])
                    if getattr(settings, 'USE_CLOUDINARY_STORAGE', False):
                        optimize_kwargs['max_file_size'] = 9_500_000

                    optimized_file = optimize_uploaded_image_file(
                        current_file,
                        **optimize_kwargs,
                    )
                    if optimized_file:
                        setattr(self, field_name, optimized_file)

        super().save(*args, **kwargs)

        if replaced_files:
            transaction.on_commit(
                lambda: [
                    self._delete_file_if_unused(field_name, file_name)
                    for field_name, file_name in replaced_files
                ]
            )

    def delete(self, *args, **kwargs):
        files_to_delete = []
        for field_name in self._get_tracked_image_field_names():
            file_field = getattr(self, field_name, None)
            if file_field and file_field.name:
                files_to_delete.append((field_name, file_field.name))

        super().delete(*args, **kwargs)

        if files_to_delete:
            transaction.on_commit(
                lambda: [
                    self._delete_file_if_unused(field_name, file_name)
                    for field_name, file_name in files_to_delete
                ]
            )


class SingletonModel(models.Model):
    """Only one row is ever allowed. save() enforces pk=1."""

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


# ── Hero ─────────────────────────────────────────────────────────────────────

class HeroSlide(OptimizedImageModelMixin, models.Model):
    optimized_image_fields = {
        'image': {'max_width': 1920, 'max_height': 1280, 'quality': 76},
    }

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='hero/', blank=True, null=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


# ── Portfolio ─────────────────────────────────────────────────────────────────

class PortfolioCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name_plural = 'portfolio categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PortfolioImage(OptimizedImageModelMixin, models.Model):
    optimized_image_fields = {
        'image': {'max_width': 1800, 'max_height': 1800, 'quality': 78},
    }

    WEDDING_TYPE_HINDU = 'hindu'
    WEDDING_TYPE_CHRISTIAN = 'christian'
    WEDDING_TYPE_SINHALA = 'sinhala'
    WEDDING_TYPE_CHOICES = [
        (WEDDING_TYPE_HINDU, 'Hindu Wedding'),
        (WEDDING_TYPE_CHRISTIAN, 'Christian Wedding'),
        (WEDDING_TYPE_SINHALA, 'Sinhala Wedding'),
    ]
    SHOOT_PHASE_PRE_WEDDING = 'pre_wedding'
    SHOOT_PHASE_WEDDING_DAY = 'wedding_day'
    SHOOT_PHASE_POST_WEDDING = 'post_wedding'
    PUBERTY_PHASE_BEFORE_THE_BLESSING = 'before_the_blessing'
    PUBERTY_PHASE_THE_CELEBRATION = 'the_celebration'
    PUBERTY_PHASE_AFTER_GLOW_PORTRAITS = 'after_glow_portraits'
    SHOOT_PHASE_CHOICES = [
        (SHOOT_PHASE_PRE_WEDDING, 'Bridal Portraits'),
        (SHOOT_PHASE_WEDDING_DAY, 'Wedding Portraits'),
        (SHOOT_PHASE_POST_WEDDING, 'Post-Wedding Shoot'),
        (PUBERTY_PHASE_BEFORE_THE_BLESSING, 'Mehendi Moments'),
        (PUBERTY_PHASE_THE_CELEBRATION, 'The Celebration'),
        (PUBERTY_PHASE_AFTER_GLOW_PORTRAITS, 'After Glow Portraits'),
    ]

    category = models.ForeignKey(
        PortfolioCategory, on_delete=models.SET_NULL, null=True, related_name='images'
    )
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='gallery_images'
    )
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True, default='')
    image = models.ImageField(upload_to='portfolio/%Y/%m/', blank=True, null=True)
    description = models.TextField(blank=True)
    wedding_type = models.CharField(max_length=20, choices=WEDDING_TYPE_CHOICES, blank=True, default='')
    shoot_phase = models.CharField(max_length=20, choices=SHOOT_PHASE_CHOICES, blank=True, default='')
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title

    def delete(self, *args, **kwargs):
        # Delete child gallery images one by one so each file cleanup hook runs.
        if self.pk:
            for gallery_image in list(self.gallery_images.all()):
                gallery_image.delete()

        super().delete(*args, **kwargs)


class PackageCard(OptimizedImageModelMixin, models.Model):
    optimized_image_fields = {
        'image': {'max_width': 1600, 'max_height': 1600, 'quality': 78},
    }

    THEME_BRONZE = 'bronze'
    THEME_SILVER = 'silver'
    THEME_GOLD = 'gold'
    THEME_CHOICES = [
        (THEME_BRONZE, 'Bronze'),
        (THEME_SILVER, 'Silver'),
        (THEME_GOLD, 'Gold'),
    ]

    category = models.ForeignKey(
        PortfolioCategory, on_delete=models.CASCADE, related_name='package_cards'
    )
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='packages/', blank=True, null=True)
    price_prefix = models.CharField(max_length=40, blank=True, default='Rs')
    price_value = models.CharField(max_length=80)
    detail_1 = models.CharField(max_length=200, blank=True)
    detail_2 = models.CharField(max_length=200, blank=True)
    detail_3 = models.CharField(max_length=200, blank=True)
    theme = models.CharField(max_length=20, choices=THEME_CHOICES, default=THEME_BRONZE)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['category__order', 'order', 'id']

    def __str__(self):
        return f'{self.category.name} - {self.title}'


# ── About ─────────────────────────────────────────────────────────────────────

class AboutSection(OptimizedImageModelMixin, SingletonModel):
    optimized_image_fields = {
        'image': {'max_width': 1600, 'max_height': 1600, 'quality': 78},
    }

    heading = models.CharField(max_length=200)
    subheading = models.CharField(max_length=300, blank=True)
    body_text = models.TextField()
    image = models.ImageField(upload_to='about/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'About Section'


# ── Team ─────────────────────────────────────────────────────────────────────

class TeamMember(OptimizedImageModelMixin, models.Model):
    optimized_image_fields = {
        'photo': {'max_width': 1200, 'max_height': 1200, 'quality': 76},
    }

    name = models.CharField(max_length=150)
    role = models.CharField(max_length=150)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to='team/', blank=True, null=True)
    instagram_url = models.URLField(blank=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.name} — {self.role}'


# ── Testimonials ──────────────────────────────────────────────────────────────

class Testimonial(OptimizedImageModelMixin, models.Model):
    optimized_image_fields = {
        'client_photo': {'max_width': 900, 'max_height': 900, 'quality': 76},
    }

    client_name = models.CharField(max_length=150)
    client_photo = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    quote = models.TextField()
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.client_name} ({self.rating}★)'

    def update_approval(self, approved: bool):
        self.is_approved = approved
        self.save(update_fields=['is_approved'])


# ── Contact ───────────────────────────────────────────────────────────────────

class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=250)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.subject}'


# ── Site Settings ─────────────────────────────────────────────────────────────

class SiteSettings(SingletonModel):
    shop_name = models.CharField(max_length=200, default='Susi Photography')
    tagline = models.CharField(max_length=300, blank=True)
    captured_moments_count = models.PositiveIntegerField(default=1000)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    phone_secondary = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    instagram_url = models.URLField(blank=True)
    facebook_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    footer_text = models.TextField(blank=True)

    class Meta(SingletonModel.Meta):
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return self.shop_name
