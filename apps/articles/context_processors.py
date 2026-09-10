"""Expose active categories to every template (navbar/footer)."""

from .models import Category


def nav_categories(request):
    return {
        "nav_categories": Category.objects.active().order_by("order", "name"),
    }
