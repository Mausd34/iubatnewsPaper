"""
api/views.py
============

DRF viewsets: articles (full CRUD + workflow), categories, tags,
comments and reactions. JWT + session authentication are configured
globally in settings.REST_FRAMEWORK.
"""

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.articles.models import (
    Article,
    Category,
    Comment,
    Reaction,
    Tag,
)

from .filters import ArticleFilter, CommentFilter
from .permissions import (
    IsAuthorOrEditor,
    IsContributor,
    IsEditorOrAdmin,
    IsOwnerOrReadOnly,
)
from .serializers import (
    ArticleDetailSerializer,
    ArticleListSerializer,
    ArticleWriteSerializer,
    CategorySerializer,
    CommentSerializer,
    ReactionSerializer,
    TagSerializer,
)


class ArticleViewSet(viewsets.ModelViewSet):
    """
    list, retrieve, create, update, partial_update, destroy.

    Extra routes:
      GET  /api/articles/featured/   hero/featured stories
      GET  /api/articles/trending/   most viewed in the last 7 days
      POST /api/articles/{pk}/publish/   (editor/faculty)
    """

    filterset_class = ArticleFilter
    search_fields = ("title", "excerpt", "content",
                     "tags__name", "author__username")
    ordering_fields = ("published_at", "created_at", "views_count", "title")
    ordering = ("-published_at",)

    def get_queryset(self):
        user = self.request.user
        qs = (
            Article.objects
            .select_related("author", "category", "reviewed_by")
            .prefetch_related("tags")
        )
        if user.is_authenticated and (
            user.is_editor_role or user.is_superuser
        ):
            return qs  # staff see everything incl. drafts/pending
        if user.is_authenticated:
            # Contributors see their own work plus all published work.
            from django.db.models import Q

            return qs.filter(Q(status="published") | Q(author=user))
        return qs.published()

    def get_permissions(self):
        if self.action in ("create",):
            return [IsContributor()]
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAuthorOrEditor()]
        if self.action == "publish":
            return [IsEditorOrAdmin()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ArticleWriteSerializer
        if self.action == "retrieve":
            return ArticleDetailSerializer
        return ArticleListSerializer

    def perform_create(self, serializer):
        # Creation logic (workflow/author) lives in the serializer.
        serializer.save()

    def create(self, request, *args, **kwargs):
        write_serializer = self.get_serializer(data=request.data)
        write_serializer.is_valid(raise_exception=True)
        article = write_serializer.save()
        read = ArticleDetailSerializer(article, context={"request": request})
        return Response(read.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        write_serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        write_serializer.is_valid(raise_exception=True)
        article = write_serializer.save()
        read = ArticleDetailSerializer(article, context={"request": request})
        return Response(read.data)

    @action(detail=False, methods=["get"])
    def featured(self, request):
        articles = Article.objects.featured()[:10]
        page = self.paginate_queryset(articles)
        serializer = self.get_serializer(
            page or articles, many=True
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def trending(self, request):
        articles = Article.objects.trending()[:10]
        serializer = self.get_serializer(articles, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"],
            permission_classes=[IsEditorOrAdmin])
    def publish(self, request, pk=None):
        article = self.get_object()
        article.publish(reviewer=request.user)
        return Response(
            ArticleDetailSerializer(article, context={"request": request}).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"],
            permission_classes=[IsEditorOrAdmin])
    def reject(self, request, pk=None):
        article = self.get_object()
        reason = request.data.get("reason", "")
        if len(reason) < 10:
            return Response(
                {"reason": "A rejection reason of 10+ characters is "
                           "required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        article.reject(reason, reviewer=request.user)
        return Response({"status": "rejected", "reason": reason})


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.with_article_counts()
    serializer_class = CategorySerializer
    lookup_field = "slug"
    filterset_fields = ("is_active",)
    search_fields = ("name", "description")
    ordering_fields = ("order", "name", "created_at")

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update",
                           "destroy"):
            return [IsEditorOrAdmin()]
        return [permissions.AllowAny()]


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all().order_by("name")
    serializer_class = TagSerializer
    lookup_field = "slug"
    pagination_class = None
    filterset_fields = ("name",)
    search_fields = ("name",)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = (
        Comment.objects.approved()
        .filter(parent__isnull=True)
        .select_related("user", "article")
        .prefetch_related("replies__user")
    )
    serializer_class = CommentSerializer
    filterset_class = CommentFilter
    ordering_fields = ("created_at",)
    ordering = ("-created_at",)

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            return [IsOwnerOrReadOnly()]
        if self.action == "create":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        comment = serializer.save(user=self.request.user)
        # Auto-moderation signal sets is_approved; echo it back.
        return comment

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = self.perform_create(serializer)
        code = (status.HTTP_201_CREATED if comment.is_approved
                else status.HTTP_202_ACCEPTED)
        return Response(
            CommentSerializer(comment, context={"request": request}).data,
            status=code,
        )


class ReactionViewSet(viewsets.ModelViewSet):
    serializer_class = ReactionSerializer
    filterset_fields = ("article", "reaction_type")

    def get_queryset(self):
        return Reaction.objects.select_related("user", "article")

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update",
                           "destroy"):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        # Enforce one reaction per user per article (toggle behaviour).
        article = serializer.validated_data["article"]
        existing = Reaction.objects.filter(
            article=article, user=self.request.user
        ).first()
        if existing:
            existing.reaction_type = serializer.validated_data[
                "reaction_type"
            ]
            existing.save(update_fields=["reaction_type"])
            return existing
        return serializer.save(user=self.request.user)
