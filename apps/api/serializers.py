"""
api/serializers.py
==================

Nested author & category representation, read/write split for articles,
and workflow support (draft / submit / publish).
"""

from rest_framework import serializers

from apps.accounts.models import CustomUser
from apps.articles.models import (
    Article,
    Category,
    Comment,
    Reaction,
    Tag,
)


# ---------------------------------------------------------------------------
# Small / nested serializers
# ---------------------------------------------------------------------------
class AuthorSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)
    profile_url = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            "id", "username", "display_name", "role",
            "department", "is_verified", "profile_url",
        )

    def get_profile_url(self, obj):
        return obj.get_absolute_url()


class CategorySerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    article_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = (
            "id", "name", "slug", "description", "icon",
            "order", "is_active", "url", "article_count",
        )

    def get_url(self, obj):
        return obj.get_absolute_url()

    def get_article_count(self, obj):
        return getattr(obj, "article_count", None) or obj.published_count


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


# ---------------------------------------------------------------------------
# Articles
# ---------------------------------------------------------------------------
class ArticleListSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    url = serializers.SerializerMethodField()
    reading_time = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)

    # Write-only inputs keyed by slug for a friendly API.
    category_slug = serializers.SlugRelatedField(
        source="category", slug_field="slug",
        queryset=Category.objects.active(), write_only=True, required=False,
    )
    tag_slugs = serializers.SlugRelatedField(
        source="tags", slug_field="slug", many=True,
        queryset=Tag.objects.all(), write_only=True, required=False,
    )

    class Meta:
        model = Article
        fields = (
            "id", "title", "slug", "url",
            "author", "category", "tags",
            "category_slug", "tag_slugs",
            "excerpt", "featured_image",
            "status", "is_featured", "is_breaking",
            "views_count", "comment_count", "reading_time",
            "published_at", "created_at", "updated_at",
        )

    def get_url(self, obj):
        return obj.get_absolute_url()


class ArticleDetailSerializer(ArticleListSerializer):
    reaction_counts = serializers.SerializerMethodField()

    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + (
            "content", "image_caption", "rejection_reason",
            "submitted_at", "reviewed_by", "reaction_counts",
        )

    def get_reaction_counts(self, obj):
        return obj.reaction_counts()


class ArticleWriteSerializer(serializers.ModelSerializer):
    """Used for create/update; supports a ``workflow`` action."""

    category_slug = serializers.SlugRelatedField(
        source="category", slug_field="slug",
        queryset=Category.objects.active(),
    )
    tag_slugs = serializers.SlugRelatedField(
        source="tags", slug_field="slug", many=True,
        queryset=Tag.objects.all(), required=False,
    )
    workflow = serializers.ChoiceField(
        choices=["save_draft", "submit", "publish"],
        required=False, default="submit",
    )

    class Meta:
        model = Article
        fields = (
            "id", "title", "category_slug", "tag_slugs",
            "excerpt", "content", "featured_image", "image_caption",
            "is_featured", "workflow",
        )

    def create(self, validated_data):
        from django.utils import timezone

        tags = validated_data.pop("tags", [])
        workflow = validated_data.pop("workflow", "submit")
        request = self.context["request"]
        article = Article(**validated_data)
        article.author = request.user

        if workflow == "save_draft":
            article.status = Article.Status.DRAFT
        elif workflow == "publish" and request.user.can_auto_publish:
            article.status = Article.Status.PUBLISHED
            article.published_at = timezone.now()
        else:
            article.status = Article.Status.PENDING
            article.submitted_at = timezone.now()
        article.save()
        article.tags.set(tags)
        return article

    def update(self, instance, validated_data):
        from django.utils import timezone

        tags = validated_data.pop("tags", None)
        workflow = validated_data.pop("workflow", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if workflow == "save_draft":
            instance.status = Article.Status.DRAFT
        elif (workflow == "publish"
              and self.context["request"].user.can_auto_publish):
            instance.status = Article.Status.PUBLISHED
            instance.published_at = instance.published_at or timezone.now()
        elif workflow == "submit" and instance.status in (
            Article.Status.DRAFT, Article.Status.REJECTED
        ):
            instance.status = Article.Status.PENDING
            instance.submitted_at = timezone.now()
        instance.save()
        if tags is not None:
            instance.tags.set(tags)
        return instance


# ---------------------------------------------------------------------------
# Comments & reactions
# ---------------------------------------------------------------------------
class CommentSerializer(serializers.ModelSerializer):
    user = AuthorSerializer(read_only=True)
    article_slug = serializers.SlugRelatedField(
        source="article", slug_field="slug",
        queryset=Article.objects.all(), write_only=True,
    )
    parent_id = serializers.PrimaryKeyRelatedField(
        source="parent", queryset=Comment.objects.all(),
        required=False, allow_null=True, write_only=True,
    )
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = (
            "id", "article", "article_slug", "user",
            "body", "parent", "parent_id", "replies",
            "is_approved", "created_at", "updated_at",
        )
        read_only_fields = ("is_approved", "article", "parent")

    def get_replies(self, obj):
        if obj.parent_id is not None:
            return []
        replies = obj.replies.filter(is_approved=True).select_related("user")
        return CommentSerializer(replies, many=True,
                                 context=self.context).data

    def validate(self, attrs):
        parent = attrs.get("parent")
        if parent and parent.parent_id:
            raise serializers.ValidationError(
                {"parent_id": "Only one level of replies is supported."}
            )
        return attrs


class ReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reaction
        fields = ("id", "article", "user", "reaction_type", "created_at")
        read_only_fields = ("user",)
