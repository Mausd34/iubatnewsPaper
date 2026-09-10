"""Expose IUBAT branding to every template."""

from django.conf import settings


def branding(request):
    return {"BRAND": settings.IUBAT_BRAND}
