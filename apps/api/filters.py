"""django-filter filtersets for the API."""

import django_filters

from apps.articles.models import Article, Comment


class ArticleFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(
        field_name="category__slug", label="Category slug"
    )
    tag = django_filters.CharFilter(field_name="tags__slug", label="Tag slug")
    author = django_filters.CharFilter(
        field_name="author__username", label="Author username"
    )
    status = django_filters.CharFilter(field_name="status")
    featured = django_filters.BooleanFilter(field_name="is_featured")
    created_after = django_filters.IsoDateTimeFilter(
        field_name="published_at", lookup_expr="gte"
    )
    created_before = django_filters.IsoDateTimeFilter(
        field_name="published_at", lookup_expr="lte"
    )
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = Article
        fields = ["category", "tag", "author", "status", "featured"]

    def filter_search(self, queryset, name, value):
        from django.db.models import Q

        return queryset.filter(
            Q(title__icontains=value)
            | Q(excerpt__icontains=value)
            | Q(content__icontains=value)
        ).distinct()


class CommentFilter(django_filters.FilterSet):
    article = django_filters.CharFilter(field_name="article__slug")
    approved = django_filters.BooleanFilter(field_name="is_approved")

    class Meta:
        model = Comment
        fields = ["article", "approved"]
