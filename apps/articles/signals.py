"""
articles/signals.py
===================

* Auto-generate unique slugs for Category, Tag and Article.
* Stamp ``published_at`` when an article transitions to published.
* Auto-hold comments from unverified users for moderation.
* Increment ``Article.views_count`` whenever an ``ArticleView`` is logged.
"""

from django.db.models import F
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify

from .models import Article, ArticleView, Category, Comment, Tag


# ---------------------------------------------------------------------------
# Slug generation
# ---------------------------------------------------------------------------
def _unique_slug(instance, value, slug_field="slug", max_length=220):
    """Build a slug that is unique in the model's table."""
    Model = instance.__class__
    base = slugify(value)[: max_length - 5] or "item"
    slug = base
    n = 1
    qs = Model.objects.exclude(pk=instance.pk)
    while qs.filter(**{slug_field: slug}).exists():
        suffix = f"-{n}"
        slug = base[: max_length - len(suffix)] + suffix
        n += 1
    return slug


@receiver(pre_save, sender=Category)
def category_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = _unique_slug(instance, instance.name, max_length=100)


@receiver(pre_save, sender=Tag)
def tag_slug(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = _unique_slug(instance, instance.name, max_length=60)


@receiver(pre_save, sender=Article)
def article_slug_and_timestamps(sender, instance, **kwargs):
    if not instance.slug:
        instance.slug = _unique_slug(instance, instance.title)

    if instance.status == Article.Status.PUBLISHED and not instance.published_at:
        instance.published_at = timezone.now()

    if instance.status in (Article.Status.DRAFT, Article.Status.PENDING):
        # Leaving the queue (e.g. sent back to draft) clears publication.
        if instance.pk and instance.status == Article.Status.DRAFT:
            old_status = Article.objects.filter(pk=instance.pk).values_list(
                "status", flat=True
            ).first()
            if old_status == Article.Status.PUBLISHED:
                instance.published_at = None


# ---------------------------------------------------------------------------
# Comment moderation
# ---------------------------------------------------------------------------
@receiver(pre_save, sender=Comment)
def auto_moderate_comment(sender, instance, **kwargs):
    """Verified users and staff post immediately; everyone else is queued."""
    user = instance.user
    if user and user.is_authenticated:
        trusted = user.is_verified or user.is_editor_role
        instance.is_approved = trusted


# ---------------------------------------------------------------------------
# View counting
# ---------------------------------------------------------------------------
@receiver(post_save, sender=ArticleView)
def increment_view_counter(sender, instance, created, **kwargs):
    """Each logged ArticleView atomically bumps the denormalised counter."""
    if created:
        Article.objects.filter(pk=instance.article_id).update(
            views_count=F("views_count") + 1
        )
