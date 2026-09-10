"""
config/urls.py
==============

Root URL configuration for the IUBAT Campus Newspaper Portal.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.core.sitemaps import (
    ArticleSitemap,
    CategorySitemap,
    StaticViewSitemap,
)

sitemaps = {
    "static": StaticViewSitemap,
    "articles": ArticleSitemap,
    "categories": CategorySitemap,
}

urlpatterns = [
    path("admin/", admin.site.urls),

    # TinyMCE rich-text editor
    path("tinymce/", include("tinymce.urls")),

    # Apps
    path("", include("apps.core.urls")),
    path("", include("apps.articles.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("newsletter/", include("apps.newsletter.urls")),

    # REST API
    path("api/", include("apps.api.urls")),

    # SEO
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": sitemaps},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]

# Development-only: serve media files through Django.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.BASE_DIR / "static"
    )

# Custom admin branding
admin.site.site_header = "IUBAT Campus News — Administration"
admin.site.site_title = "IUBAT News Admin"
admin.site.index_title = "Editorial control centre"
