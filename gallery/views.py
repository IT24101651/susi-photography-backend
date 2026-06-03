from rest_framework import viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import (
    HeroSlide, PortfolioCategory, PortfolioImage, PackageCard,
    AboutSection, TeamMember, Testimonial, ContactMessage, SiteSettings,
)
from .serializers import (
    HeroSlideSerializer, HeroSlideWriteSerializer,
    PortfolioCategorySerializer, PortfolioCategoryWriteSerializer,
    PortfolioImageSerializer, PortfolioImageWriteSerializer,
    PackageCardSerializer, PackageCardWriteSerializer,
    AboutSectionSerializer, AboutSectionWriteSerializer,
    TeamMemberSerializer, TeamMemberWriteSerializer,
    TestimonialSerializer, TestimonialWriteSerializer,
    ContactMessageSerializer, ContactMessageAdminSerializer,
    SiteSettingsSerializer,
)


# ── Mixins ────────────────────────────────────────────────────────────────────

class AdminPermissionMixin:
    permission_classes = [permissions.IsAdminUser]


class ReadWriteSerializerMixin:
    """Switches serializer class based on request method."""
    read_serializer_class = None
    write_serializer_class = None

    def get_serializer_class(self):
        if self.request.method in ('POST', 'PUT', 'PATCH'):
            return self.write_serializer_class
        return self.read_serializer_class


# ══════════════════════════════════════════════════════════════════════════════
# PUBLIC VIEWS
# ══════════════════════════════════════════════════════════════════════════════

@extend_schema(tags=['Public'])
class HeroSlidePublicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HeroSlide.objects.filter(is_active=True)
    serializer_class = HeroSlideSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=['Public'])
class PortfolioCategoryPublicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PortfolioCategory.objects.filter(is_active=True)
    serializer_class = PortfolioCategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'


@extend_schema_view(
    list=extend_schema(
        tags=['Public'],
        parameters=[
            OpenApiParameter('category', str, description='Filter by category slug'),
            OpenApiParameter('featured', bool, description='Return only featured images'),
        ],
    ),
    retrieve=extend_schema(tags=['Public']),
)
class PortfolioImagePublicViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PortfolioImageSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = (
            PortfolioImage.objects
            .select_related('category')
            .prefetch_related('gallery_images')
            .filter(parent__isnull=True, category__is_active=True)
        )
        category = self.request.query_params.get('category')
        featured = self.request.query_params.get('featured')
        preview  = self.request.query_params.get('preview')

        if category:
            return qs.filter(category__slug=category)
        if featured:
            return qs.filter(is_featured=True)
        if preview:
            # Return up to 6 main images per active category for homepage sliders.
            ids = []
            for cat in PortfolioCategory.objects.filter(is_active=True).order_by('order'):
                ids += list(
                    qs.filter(category=cat).order_by('order', 'id').values_list('id', flat=True)[:6]
                )
            return (
                PortfolioImage.objects
                .select_related('category')
                .prefetch_related('gallery_images')
                .filter(id__in=ids)
                .order_by('category__order', 'order', 'id')
            )
        return qs


@extend_schema_view(
    list=extend_schema(
        tags=['Public'],
        parameters=[OpenApiParameter('category', str, description='Filter by category slug')],
    ),
    retrieve=extend_schema(tags=['Public']),
)
class PackageCardPublicViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PackageCardSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = PackageCard.objects.select_related('category').filter(is_active=True, category__is_active=True)
        category = self.request.query_params.get('category')
        if category:
            return qs.filter(category__slug=category)
        return qs


@extend_schema(tags=['Public'])
class AboutSectionPublicView(generics.RetrieveAPIView):
    serializer_class = AboutSectionSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        return AboutSection.load()


@extend_schema(tags=['Public'])
class TeamMemberPublicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TeamMember.objects.filter(is_active=True)
    serializer_class = TeamMemberSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=['Public'])
class TestimonialPublicViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Testimonial.objects.filter(is_approved=True)
    serializer_class = TestimonialSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=['Public'])
class ContactMessageCreateView(generics.CreateAPIView):
    serializer_class = ContactMessageSerializer
    permission_classes = [permissions.AllowAny]


@extend_schema(tags=['Public'])
class SiteSettingsPublicView(generics.RetrieveAPIView):
    serializer_class = SiteSettingsSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        return SiteSettings.load()


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN VIEWS  (JWT — IsAdminUser)
# ══════════════════════════════════════════════════════════════════════════════

@extend_schema(tags=['Admin'])
class HeroSlideAdminViewSet(AdminPermissionMixin, ReadWriteSerializerMixin, viewsets.ModelViewSet):
    queryset = HeroSlide.objects.all()
    read_serializer_class = HeroSlideSerializer
    write_serializer_class = HeroSlideWriteSerializer


@extend_schema(tags=['Admin'])
class PortfolioCategoryAdminViewSet(AdminPermissionMixin, ReadWriteSerializerMixin, viewsets.ModelViewSet):
    queryset = PortfolioCategory.objects.all()
    read_serializer_class = PortfolioCategorySerializer
    write_serializer_class = PortfolioCategoryWriteSerializer
    lookup_field = 'slug'


@extend_schema(tags=['Admin'])
class PortfolioImageAdminViewSet(AdminPermissionMixin, ReadWriteSerializerMixin, viewsets.ModelViewSet):
    queryset = PortfolioImage.objects.select_related('category').prefetch_related('gallery_images').filter(parent__isnull=True)
    read_serializer_class = PortfolioImageSerializer
    write_serializer_class = PortfolioImageWriteSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]


@extend_schema(tags=['Admin'])
class PackageCardAdminViewSet(AdminPermissionMixin, ReadWriteSerializerMixin, viewsets.ModelViewSet):
    queryset = PackageCard.objects.select_related('category')
    read_serializer_class = PackageCardSerializer
    write_serializer_class = PackageCardWriteSerializer


@extend_schema(tags=['Admin'])
class AboutSectionAdminView(AdminPermissionMixin, generics.RetrieveUpdateAPIView):
    serializer_class = AboutSectionWriteSerializer

    def get_object(self):
        return AboutSection.load()


@extend_schema(tags=['Admin'])
class TeamMemberAdminViewSet(AdminPermissionMixin, ReadWriteSerializerMixin, viewsets.ModelViewSet):
    queryset = TeamMember.objects.all()
    read_serializer_class = TeamMemberSerializer
    write_serializer_class = TeamMemberWriteSerializer


@extend_schema(tags=['Admin'])
class TestimonialAdminViewSet(AdminPermissionMixin, ReadWriteSerializerMixin, viewsets.ModelViewSet):
    queryset = Testimonial.objects.all()
    read_serializer_class = TestimonialSerializer
    write_serializer_class = TestimonialWriteSerializer

    @extend_schema(request=None, responses={200: TestimonialWriteSerializer})
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        self.get_object().update_approval(True)
        return Response({'status': 'approved'})

    @extend_schema(request=None, responses={200: TestimonialWriteSerializer})
    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        self.get_object().update_approval(False)
        return Response({'status': 'rejected'})


@extend_schema(tags=['Admin'])
class ContactMessageAdminViewSet(AdminPermissionMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ContactMessage.objects.all()
    serializer_class = ContactMessageAdminSerializer

    @extend_schema(request=None, responses={200: ContactMessageAdminSerializer})
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        msg = self.get_object()
        msg.is_read = True
        msg.save(update_fields=['is_read'])
        return Response({'status': 'marked as read'})


@extend_schema(tags=['Admin'])
class SiteSettingsAdminView(AdminPermissionMixin, generics.RetrieveUpdateAPIView):
    serializer_class = SiteSettingsSerializer

    def get_object(self):
        return SiteSettings.load()
