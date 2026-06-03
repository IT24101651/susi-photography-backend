from django.contrib import admin
from django.utils.html import format_html
from .models import (
    HeroSlide, PortfolioCategory, PortfolioImage, PackageCard,
    AboutSection, TeamMember, Testimonial, ContactMessage, SiteSettings,
)
from .image_utils import get_public_image_url


class SingletonAdmin(admin.ModelAdmin):
    """Hides the 'Add' button and redirects the changelist to the single object."""

    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def changelist_view(self, request, extra_context=None):
        obj, _ = self.model.objects.get_or_create(pk=1)
        from django.http import HttpResponseRedirect
        from django.urls import reverse
        info = self.model._meta.app_label, self.model._meta.model_name
        return HttpResponseRedirect(reverse('admin:%s_%s_change' % info, args=[obj.pk]))


class FileCleanupAdminMixin:
    """Make bulk admin deletes run model-level cleanup hooks for media files."""

    def delete_queryset(self, request, queryset):
        selected_ids = set(queryset.values_list('pk', flat=True))

        if any(field.name == 'parent' for field in queryset.model._meta.fields):
            queryset = queryset.exclude(parent_id__in=selected_ids)

        for obj in queryset.iterator():
            obj.delete()


# ── Hero ──────────────────────────────────────────────────────────────────────

@admin.register(HeroSlide)
class HeroSlideAdmin(FileCleanupAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'order', 'is_active', 'preview', 'created_at']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']

    def preview(self, obj):
        url = get_public_image_url(obj.image)
        if url:
            return format_html('<img src="{}" height="50" />', url)
        return '—'
    preview.short_description = 'Preview'


# ── Portfolio ─────────────────────────────────────────────────────────────────

@admin.register(PortfolioCategory)
class PortfolioCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(PortfolioImage)
class PortfolioImageAdmin(FileCleanupAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'category', 'is_featured', 'order', 'preview', 'created_at']
    list_editable = ['is_featured', 'order']
    list_filter = ['category', 'is_featured']
    search_fields = ['title']

    def preview(self, obj):
        url = get_public_image_url(obj.image)
        if url:
            return format_html('<img src="{}" height="50" />', url)
        return '—'
    preview.short_description = 'Preview'


@admin.register(PackageCard)
class PackageCardAdmin(FileCleanupAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'category', 'price_value', 'theme', 'order', 'is_active', 'preview']
    list_editable = ['order', 'is_active']
    list_filter = ['category', 'theme', 'is_active']
    search_fields = ['title', 'category__name', 'price_value']

    def preview(self, obj):
        url = get_public_image_url(obj.image)
        if url:
            return format_html('<img src="{}" height="50" />', url)
        return 'â€”'
    preview.short_description = 'Preview'


# ── About ─────────────────────────────────────────────────────────────────────

@admin.register(AboutSection)
class AboutSectionAdmin(SingletonAdmin):
    pass


# ── Team ─────────────────────────────────────────────────────────────────────

@admin.register(TeamMember)
class TeamMemberAdmin(FileCleanupAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'role', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active']


# ── Testimonials ──────────────────────────────────────────────────────────────

@admin.register(Testimonial)
class TestimonialAdmin(FileCleanupAdminMixin, admin.ModelAdmin):
    list_display = ['client_name', 'rating', 'is_approved', 'created_at']
    list_editable = ['is_approved']
    list_filter = ['is_approved', 'rating']
    search_fields = ['client_name', 'quote']


# ── Contact ───────────────────────────────────────────────────────────────────

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'created_at']
    list_editable = ['is_read']
    list_filter = ['is_read']
    search_fields = ['name', 'email', 'subject']
    readonly_fields = ['name', 'email', 'phone', 'subject', 'message', 'created_at']

    def has_add_permission(self, request):
        return False


# ── Site Settings ─────────────────────────────────────────────────────────────

@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonAdmin):
    pass
