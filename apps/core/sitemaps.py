"""Sitemap classes for SEO."""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.articles.models import Article, Category


class ArticleSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8
    limit = 500

    def items(self):
        return (
            Article.objects.published()
            .select_related("category")
            .order_by("-published_at")
        )

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class CategorySitemap(Sitemap):
    changefreq = "daily"
    priority = 0.5

    def items(self):
        return Category.objects.active()

    def location(self, obj):
        return obj.get_absolute_url()


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.3

    def items(self):
        return ["core:home", "articles:list", "core:about",
                "core:contact"]

    def location(self, item):
        return reverse(item)
