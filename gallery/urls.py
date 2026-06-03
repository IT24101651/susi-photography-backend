from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # public
    HeroSlidePublicViewSet, PortfolioCategoryPublicViewSet, PortfolioImagePublicViewSet, PackageCardPublicViewSet,
    AboutSectionPublicView, TeamMemberPublicViewSet, TestimonialPublicViewSet,
    ContactMessageCreateView, SiteSettingsPublicView,
    # admin
    HeroSlideAdminViewSet, PortfolioCategoryAdminViewSet, PortfolioImageAdminViewSet, PackageCardAdminViewSet,
    AboutSectionAdminView, TeamMemberAdminViewSet, TestimonialAdminViewSet,
    ContactMessageAdminViewSet, SiteSettingsAdminView,
)

public_router = DefaultRouter()
public_router.register('slides',                HeroSlidePublicViewSet,         basename='public-slides')
public_router.register('portfolio/categories',  PortfolioCategoryPublicViewSet, basename='public-categories')
public_router.register('portfolio',             PortfolioImagePublicViewSet,    basename='public-portfolio')
public_router.register('packages',              PackageCardPublicViewSet,       basename='public-packages')
public_router.register('team',                  TeamMemberPublicViewSet,        basename='public-team')
public_router.register('testimonials',          TestimonialPublicViewSet,       basename='public-testimonials')

admin_router = DefaultRouter()
admin_router.register('slides',                HeroSlideAdminViewSet,          basename='admin-slides')
admin_router.register('portfolio/categories',  PortfolioCategoryAdminViewSet,  basename='admin-categories')
admin_router.register('portfolio',             PortfolioImageAdminViewSet,     basename='admin-portfolio')
admin_router.register('packages',              PackageCardAdminViewSet,        basename='admin-packages')
admin_router.register('team',                  TeamMemberAdminViewSet,         basename='admin-team')
admin_router.register('testimonials',          TestimonialAdminViewSet,        basename='admin-testimonials')
admin_router.register('messages',              ContactMessageAdminViewSet,     basename='admin-messages')

urlpatterns = [
    # ── Public ────────────────────────────────────────────────────────────────
    path('', include(public_router.urls)),
    path('about/',   AboutSectionPublicView.as_view()),
    path('contact/', ContactMessageCreateView.as_view()),
    path('settings/', SiteSettingsPublicView.as_view()),

    # ── Admin ─────────────────────────────────────────────────────────────────
    path('admin/', include(admin_router.urls)),
    path('admin/about/',    AboutSectionAdminView.as_view()),
    path('admin/settings/', SiteSettingsAdminView.as_view()),
]
