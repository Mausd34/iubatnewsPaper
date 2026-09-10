"""articles/admin.py"""

from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from .models import (
    Article,
    ArticleView,
    Category,
    Comment,
    Reaction,
    Tag,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "order", "icon", "is_active",
                    "article_count")
    list_filter = ("is_active",)
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("order", "is_active", "icon")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(n=Count("articles"))

    @admin.display(ordering="n", description="Articles")
    def article_count(self, obj):
        return obj.n


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "article_count")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(n=Count("articles"))

    @admin.display(ordering="n", description="Articles")
    def article_count(self, obj):
        return obj.n


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    fields = ("user", "body", "parent", "is_approved", "created_at")
    readonly_fields = ("created_at",)
    show_change_link = True


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail",
        "title",
        "author",
        "category",
        "status",
        "is_featured",
        "views_count",
        "published_at",
    )
    list_filter = ("status", "is_featured", "is_breaking", "category",
                   "created_at")
    search_fields = ("title", "excerpt", "content",
                     "author__username", "tags__name")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "published_at"
    filter_horizontal = ("tags",)
    readonly_fields = ("views_count", "created_at", "updated_at",
                       "submitted_at", "reviewed_by")
    list_per_page = 25
    actions = ["publish_articles", "feature_articles", "unfeature_articles"]
    fieldsets = (
        (None, {
            "fields": ("title", "slug", "author", "category", "tags",
                       "status"),
        }),
        ("Content", {
            "fields": ("excerpt", "content", "featured_image",
                       "image_caption"),
        }),
        ("Promotion & workflow", {
            "fields": ("is_featured", "is_breaking", "rejection_reason",
                       "reviewed_by", "submitted_at", "published_at"),
        }),
        ("Meta", {
            "classes": ("collapse",),
            "fields": ("views_count", "created_at", "updated_at"),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "author", "category"
        )

    @admin.display(description="Image")
    def thumbnail(self, obj):
        if obj.featured_image:
            return format_html(
                '<img src="{}" style="height:40px;width:60px;object-fit:'
                'cover;border-radius:4px;"/>', obj.featured_image.url
            )
        return "—"

    @admin.action(description="Publish selected articles")
    def publish_articles(self, request, queryset):
        from django.utils import timezone
        updated = 0
        for article in queryset.exclude(status="published"):
            article.status = "published"
            article.published_at = article.published_at or timezone.now()
            article.reviewed_by = request.user
            article.save()
            updated += 1
        self.message_user(request, f"{updated} article(s) published.")

    @admin.action(description="Feature selected articles")
    def feature_articles(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} article(s) featured.")

    @admin.action(description="Remove featured flag")
    def unfeature_articles(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f"{updated} article(s) un-featured.")


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("__str__", "is_approved", "parent", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("body", "user__username", "article__title")
    actions = ["approve_comments", "remove_comments"]
    list_per_page = 30

    @admin.action(description="Approve selected comments")
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} comment(s) approved.")

    @admin.action(description="Un-approve selected comments")
    def remove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f"{updated} comment(s) hidden.")


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ("article", "user", "reaction_type", "created_at")
    list_filter = ("reaction_type", "created_at")
    search_fields = ("article__title", "user__username")


@admin.register(ArticleView)
class ArticleViewAdmin(admin.ModelAdmin):
    list_display = ("article", "user", "ip", "timestamp")
    list_filter = ("timestamp",)
    search_fields = ("article__title", "ip", "user__username", "user_agent")
    date_hierarchy = "timestamp"
    readonly_fields = ("timestamp",)

    def has_add_permission(self, request):
        return False
