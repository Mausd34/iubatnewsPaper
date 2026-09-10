"""Custom model managers for the articles app."""

from django.db import models
from django.db.models import Count
from django.utils import timezone


class CategoryManager(models.Manager):
    def active(self):
        return self.filter(is_active=True)

    def with_article_counts(self):
        # NOTE: the annotation is named ``article_count`` (the model
        # property ``published_count`` must not be shadowed).
        return (
            self.get_queryset()
            .annotate(article_count=Count(
                "articles",
                filter=models.Q(articles__status="published"),
            ))
            .order_by("order", "name")
        )


class ArticleQuerySet(models.QuerySet):
    def published(self):
        return self.filter(
            status="published",
            published_at__lte=timezone.now(),
        )

    def pending(self):
        return self.filter(status="pending")

    def drafts(self):
        return self.filter(status="draft")

    def rejected(self):
        return self.filter(status="rejected")

    def featured(self):
        return self.published().filter(is_featured=True)

    def by_author(self, user):
        return self.filter(author=user)

    def in_category(self, slug):
        return self.published().filter(category__slug=slug)

    def trending(self, days=7):
        """Most-viewed published articles within the trailing window."""
        since = timezone.now() - timezone.timedelta(days=days)
        return (
            self.published()
            .filter(article_views__timestamp__gte=since)
            .annotate(recent_views=Count("article_views"))
            .order_by("-recent_views", "-published_at")
            .distinct()
        )

    def popular(self):
        return self.published().order_by("-views_count", "-published_at")

    def search(self, query):
        """Simple Q-object search over title, excerpt, body and tags."""
        if not query:
            return self.none()
        return (
            self.published()
            .filter(
                models.Q(title__icontains=query)
                | models.Q(excerpt__icontains=query)
                | models.Q(content__icontains=query)
                | models.Q(tags__name__icontains=query)
                | models.Q(author__username__icontains=query)
            )
            .distinct()
        )


class ArticleManager(models.Manager.from_queryset(ArticleQuerySet)):
    pass


class CommentQuerySet(models.QuerySet):
    def approved(self):
        return self.filter(is_approved=True, article__status="published")

    def pending_moderation(self):
        return self.filter(is_approved=False)

    def top_level(self):
        return self.filter(parent__isnull=True)


class CommentManager(models.Manager.from_queryset(CommentQuerySet)):
    pass
