from django.db import transaction
from rest_framework import serializers
from .models import (
    HeroSlide, PortfolioCategory, PortfolioImage, PackageCard,
    AboutSection, TeamMember, Testimonial, ContactMessage, SiteSettings,
)
from .image_utils import get_public_image_url


# ── Helpers ───────────────────────────────────────────────────────────────────

class AbsoluteImageField(serializers.ImageField):
    """Returns a fully-qualified URL using the request context."""

    def to_representation(self, value):
        url = get_public_image_url(value)
        if not url:
            return None
        request = self.context.get('request')
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url


# ── Hero ──────────────────────────────────────────────────────────────────────

class HeroSlideSerializer(serializers.ModelSerializer):
    image = AbsoluteImageField()

    class Meta:
        model = HeroSlide
        fields = ['id', 'title', 'subtitle', 'image', 'order', 'is_active']


class HeroSlideWriteSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    class Meta:
        model = HeroSlide
        fields = ['id', 'title', 'subtitle', 'image', 'order', 'is_active']


# ── Portfolio ─────────────────────────────────────────────────────────────────

class PortfolioCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioCategory
        fields = ['id', 'name', 'slug', 'order', 'is_active']


class PortfolioCategoryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioCategory
        fields = ['id', 'name', 'slug', 'order', 'is_active']
        extra_kwargs = {'slug': {'required': False}}


class PortfolioGalleryImageSerializer(serializers.ModelSerializer):
    image = AbsoluteImageField()

    class Meta:
        model = PortfolioImage
        fields = ['id', 'title', 'subtitle', 'image', 'description', 'wedding_type', 'shoot_phase', 'order', 'created_at']


class PortfolioImageSerializer(serializers.ModelSerializer):
    image = AbsoluteImageField()
    category = PortfolioCategorySerializer(read_only=True)
    gallery_images = PortfolioGalleryImageSerializer(many=True, read_only=True)

    class Meta:
        model = PortfolioImage
        fields = ['id', 'category', 'title', 'subtitle', 'image', 'description', 'wedding_type', 'shoot_phase', 'is_featured', 'order', 'created_at', 'gallery_images']


class PortfolioImageWriteSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=PortfolioImage.objects.filter(parent__isnull=True),
        required=False,
        allow_null=True,
    )
    image = serializers.ImageField(required=False)
    gallery_uploads = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )
    gallery_upload_shoot_phases = serializers.ListField(
        child=serializers.CharField(allow_blank=True),
        write_only=True,
        required=False,
        allow_empty=True,
    )
    removed_gallery_image_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True,
    )

    class Meta:
        model = PortfolioImage
        fields = ['id', 'parent', 'category', 'title', 'subtitle', 'image', 'description', 'wedding_type', 'shoot_phase', 'is_featured', 'order', 'gallery_uploads', 'gallery_upload_shoot_phases', 'removed_gallery_image_ids']

    def validate(self, attrs):
        attrs = super().validate(attrs)
        category = attrs.get('category', getattr(self.instance, 'category', None))
        parent = attrs.get('parent', getattr(self.instance, 'parent', None))
        wedding_type = attrs.get('wedding_type', getattr(self.instance, 'wedding_type', '')) or ''
        shoot_phase = attrs.get('shoot_phase', getattr(self.instance, 'shoot_phase', '')) or ''
        category_slug = getattr(category, 'slug', '') or ''
        is_gallery_image = parent is not None
        is_puberty_category = category_slug == 'puberty-ceremony'

        if category_slug == 'wedding' and not wedding_type:
            raise serializers.ValidationError({'wedding_type': 'Wedding type is required for wedding photos.'})

        if category_slug == 'puberty-ceremony' and not shoot_phase:
            raise serializers.ValidationError({'shoot_phase': 'Type is required for puberty ceremony photos.'})

        if category_slug == 'wedding' and is_gallery_image and not shoot_phase:
            raise serializers.ValidationError({'shoot_phase': 'Shoot phase is required for wedding gallery images.'})

        if category_slug not in {'wedding', 'puberty-ceremony'}:
            attrs['wedding_type'] = ''
            attrs['shoot_phase'] = ''
        elif category_slug == 'wedding' and not is_gallery_image:
            attrs['shoot_phase'] = ''
        elif is_puberty_category:
            attrs['wedding_type'] = ''

        return attrs

    def create(self, validated_data):
        gallery_uploads = self._get_gallery_uploads(validated_data)
        gallery_upload_phases = self._get_gallery_upload_shoot_phases(validated_data)
        validated_data.pop('removed_gallery_image_ids', [])
        with transaction.atomic():
            instance = super().create(validated_data)
            self._create_gallery_images(instance, gallery_uploads, gallery_upload_phases)
        return instance

    def update(self, instance, validated_data):
        gallery_uploads = self._get_gallery_uploads(validated_data)
        gallery_upload_phases = self._get_gallery_upload_shoot_phases(validated_data)
        removed_gallery_image_ids = validated_data.pop('removed_gallery_image_ids', [])
        original_category_id = instance.category_id
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            gallery_updates = {
                'category': instance.category,
                'subtitle': instance.subtitle,
                'description': instance.description,
                'wedding_type': instance.wedding_type,
            }

            # Keep each gallery image's own shoot phase when editing the parent.
            # Only clear it when the parent category changes, because the old phase
            # value may no longer be valid for the new category.
            if instance.category_id != original_category_id:
                gallery_updates['shoot_phase'] = ''

            instance.gallery_images.update(**gallery_updates)
            if removed_gallery_image_ids:
                for gallery_image in instance.gallery_images.filter(id__in=removed_gallery_image_ids):
                    gallery_image.delete()
            self._create_gallery_images(instance, gallery_uploads, gallery_upload_phases)
        return instance

    def _create_gallery_images(self, parent, gallery_uploads, gallery_upload_phases=None):
        existing_count = parent.gallery_images.count()
        gallery_upload_phases = gallery_upload_phases or []
        for index, image in enumerate(gallery_uploads, start=1):
            gallery_shoot_phase = gallery_upload_phases[index - 1] if index - 1 < len(gallery_upload_phases) else ''
            if not gallery_shoot_phase:
                gallery_shoot_phase = parent.shoot_phase if parent.category and parent.category.slug == 'wedding' else ''
            PortfolioImage.objects.create(
                parent=parent,
                category=parent.category,
                title=f'{parent.title} Gallery {existing_count + index}',
                subtitle=parent.subtitle,
                image=image,
                description=parent.description,
                wedding_type=parent.wedding_type,
                shoot_phase=gallery_shoot_phase,
                order=existing_count + index,
            )

    def _get_gallery_uploads(self, validated_data):
        request = self.context.get('request')
        if request:
            uploads = []
            if hasattr(request, 'data') and hasattr(request.data, 'getlist'):
                uploads = request.data.getlist('gallery_uploads')
            if (not uploads) and hasattr(request, 'FILES'):
                uploads = request.FILES.getlist('gallery_uploads')
            if uploads:
                validated_data.pop('gallery_uploads', None)
                return uploads
        return validated_data.pop('gallery_uploads', [])

    def _get_gallery_upload_shoot_phases(self, validated_data):
        request = self.context.get('request')
        if request:
            phases = []
            if hasattr(request, 'data') and hasattr(request.data, 'getlist'):
                phases = request.data.getlist('gallery_upload_shoot_phases')
            if (not phases) and hasattr(request, 'data') and hasattr(request.data, 'get'):
                single_phase = request.data.get('gallery_upload_shoot_phases')
                if isinstance(single_phase, list):
                    phases = single_phase
            if phases:
                validated_data.pop('gallery_upload_shoot_phases', None)
                return phases
        return validated_data.pop('gallery_upload_shoot_phases', [])


class PackageCardSerializer(serializers.ModelSerializer):
    image = AbsoluteImageField()
    category = PortfolioCategorySerializer(read_only=True)

    class Meta:
        model = PackageCard
        fields = [
            'id', 'category', 'title', 'image', 'price_prefix', 'price_value',
            'detail_1', 'detail_2', 'detail_3', 'theme', 'order', 'is_active',
        ]


class PackageCardWriteSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)

    class Meta:
        model = PackageCard
        fields = [
            'id', 'category', 'title', 'image', 'price_prefix', 'price_value',
            'detail_1', 'detail_2', 'detail_3', 'theme', 'order', 'is_active',
        ]


# ── About ─────────────────────────────────────────────────────────────────────

class AboutSectionSerializer(serializers.ModelSerializer):
    image = AbsoluteImageField()

    class Meta:
        model = AboutSection
        fields = ['heading', 'subheading', 'body_text', 'image', 'updated_at']


class AboutSectionWriteSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(required=False)
    class Meta:
        model = AboutSection
        fields = ['heading', 'subheading', 'body_text', 'image']


# ── Team ─────────────────────────────────────────────────────────────────────

class TeamMemberSerializer(serializers.ModelSerializer):
    photo = AbsoluteImageField()

    class Meta:
        model = TeamMember
        fields = ['id', 'name', 'role', 'bio', 'photo', 'instagram_url', 'order', 'is_active']


class TeamMemberWriteSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(required=False)
    class Meta:
        model = TeamMember
        fields = ['id', 'name', 'role', 'bio', 'photo', 'instagram_url', 'order', 'is_active']


# ── Testimonials ──────────────────────────────────────────────────────────────

class TestimonialSerializer(serializers.ModelSerializer):
    client_photo = AbsoluteImageField()

    class Meta:
        model = Testimonial
        fields = ['id', 'client_name', 'client_photo', 'quote', 'rating', 'created_at']


class TestimonialWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = ['id', 'client_name', 'client_photo', 'quote', 'rating', 'is_approved']


# ── Contact ───────────────────────────────────────────────────────────────────

class ContactMessageSerializer(serializers.ModelSerializer):
    """Used for public POST submissions."""
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']


class ContactMessageAdminSerializer(serializers.ModelSerializer):
    """Used for admin GET — exposes is_read and created_at."""
    class Meta:
        model = ContactMessage
        fields = ['id', 'name', 'email', 'phone', 'subject', 'message', 'is_read', 'created_at']
        read_only_fields = ['name', 'email', 'phone', 'subject', 'message', 'created_at']


# ── Site Settings ─────────────────────────────────────────────────────────────

class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = [
            'shop_name', 'tagline', 'captured_moments_count', 'email', 'phone', 'phone_secondary',
            'address', 'instagram_url', 'facebook_url', 'tiktok_url', 'footer_text',
        ]
