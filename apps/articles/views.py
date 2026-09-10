"""
articles/views.py
=================

Class-based template views for the public newspaper plus JSON endpoints
for comments and reactions.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from apps.accounts.mixins import ContributorRequiredMixin, EditorRequiredMixin
from apps.accounts.roles import EDITORIAL_ROLES

from .forms import ArticleForm, CommentForm
from .models import (
    Article,
    ArticleView,
    Category,
    Comment,
    Reaction,
    Tag,
)
import json

from django.conf import settings


# ---------------------------------------------------------------------------
# Homepage
# ---------------------------------------------------------------------------
class HomeView(TemplateView):
    template_name = "articles/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        published = Article.objects.published().select_related(
            "author", "category"
        )

        featured = list(published.filter(is_featured=True)[:5])
        # Fall back to the newest stories if editors haven't featured any.
        if len(featured) < 3:
            ids = {a.pk for a in featured}
            featured += list(published.exclude(pk__in=ids)[: 5 - len(featured)])

        ctx["hero_article"] = featured[0] if featured else None
        ctx["featured_articles"] = featured[1:5]
        ctx["latest_articles"] = published[:9]
        ctx["trending_articles"] = (
            Article.objects.trending(settings.TRENDING_WINDOW_DAYS)[:5]
        )
        ctx["breaking"] = published.filter(is_breaking=True).first()

        # One mini-section per active category (cached for 5 minutes).
        sections = cache.get("home_category_sections")
        if sections is None:
            sections = []
            for category in Category.objects.active()[:6]:
                items = list(
                    published.filter(category=category)[:4]
                )
                if items:
                    sections.append((category, items))
            cache.set("home_category_sections", sections, 60 * 5)
        ctx["category_sections"] = sections
        return ctx


# ---------------------------------------------------------------------------
# Article list with filtering, search & pagination
# ---------------------------------------------------------------------------
class ArticleListView(ListView):
    template_name = "articles/article_list.html"
    context_object_name = "articles"
    paginate_by = settings.ARTICLES_PER_PAGE

    def get_queryset(self):
        qs = (
            Article.objects.published()
            .select_related("author", "category")
            .prefetch_related("tags")
        )
        params = self.request.GET

        # --- Free-text search -------------------------------------------
        self.query = params.get("q", "").strip()
        if self.query:
            qs = (
                qs.filter(
                    Q(title__icontains=self.query)
                    | Q(excerpt__icontains=self.query)
                    | Q(content__icontains=self.query)
                    | Q(tags__name__icontains=self.query)
                    | Q(author__username__icontains=self.query)
                    | Q(author__first_name__icontains=self.query)
                    | Q(author__last_name__icontains=self.query)
                )
                .distinct()
            )

        # --- Category / tag / author filters ----------------------------
        self.active_category = None
        category_slug = params.get("category")
        if category_slug:
            self.active_category = get_object_or_404(
                Category, slug=category_slug, is_active=True
            )
            qs = qs.filter(category=self.active_category)

        self.active_tag = None
        tag_slug = params.get("tag")
        if tag_slug:
            self.active_tag = get_object_or_404(Tag, slug=tag_slug)
            qs = qs.filter(tags=self.active_tag)

        author = params.get("author")
        if author:
            qs = qs.filter(author__username=author)

        # --- Date filters (year / year-month) ---------------------------
        self.year = params.get("year")
        self.month = params.get("month")
        if self.year and self.year.isdigit():
            qs = qs.filter(published_at__year=int(self.year))
        if self.month and self.month.isdigit():
            qs = qs.filter(published_at__month=int(self.month))

        # --- Featured only ----------------------------------------------
        if params.get("featured"):
            qs = qs.filter(is_featured=True)

        # --- Ordering ----------------------------------------------------
        sort = params.get("sort", "newest")
        self.sort = sort
        if sort == "popular":
            qs = qs.order_by("-views_count", "-published_at")
        elif sort == "oldest":
            qs = qs.order_by("published_at")
        else:
            qs = qs.order_by("-published_at", "-created_at")
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            query=self.query,
            sort=self.sort,
            active_category=self.active_category,
            active_tag=self.active_tag,
            year=self.year,
            month=self.month,
            page_title=self._page_title(),
            popular_tags=Tag.objects.annotate(
                n=Count("articles", filter=Q(
                    articles__status="published"))
            ).order_by("-n")[:15],
        )
        return ctx

    def _page_title(self):
        if self.query:
            return f"Search results for “{self.query}”"
        if self.active_category:
            return f"{self.active_category.icon} {self.active_category.name}"
        if self.active_tag:
            return f"#{self.active_tag.name}"
        if self.year and self.month:
            return f"Archive: {self.month}/{self.year}"
        if self.year:
            return f"Archive: {self.year}"
        return "All articles"


class CategoryDetailView(ArticleListView):
    """Article list pre-filtered by category (pretty URL)."""

    def get_queryset(self):
        # Call super() first (it resets the filter attributes), then set
        # the category from the URL path and apply the restriction.
        qs = super().get_queryset()
        self.active_category = get_object_or_404(
            Category, slug=self.kwargs["slug"], is_active=True
        )
        return qs.filter(category=self.active_category)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = (
            f"{self.active_category.icon} {self.active_category.name}"
        )
        ctx["category_description"] = self.active_category.description
        return ctx


class TagDetailView(ArticleListView):
    def get_queryset(self):
        qs = super().get_queryset()
        self.active_tag = get_object_or_404(Tag, slug=self.kwargs["slug"])
        return qs.filter(tags=self.active_tag)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["page_title"] = f"#{self.active_tag.name}"
        return ctx


# ---------------------------------------------------------------------------
# Article detail — view logging, comments, related stories
# ---------------------------------------------------------------------------
class ArticleDetailView(DetailView):
    template_name = "articles/article_detail.html"
    context_object_name = "article"

    def get_object(self, queryset=None):
        article = get_object_or_404(
            Article.objects.select_related("author", "category",
                                           "reviewed_by")
            .prefetch_related("tags"),
            slug=self.kwargs["slug"],
        )
        user = self.request.user
        # Unpublished articles are only visible to their author and staff.
        if not article.is_published:
            is_author = user.is_authenticated and user == article.author
            is_staff = (
                user.is_authenticated
                and (user.is_editor_role or user.is_superuser)
            )
            if not (is_author or is_staff):
                raise Http404("Article not found.")
        return article

    def get_client_ip(self, request):
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    def log_view(self, request, article):
        """Log one view per IP per article per hour (cache throttled)."""
        if not article.is_published:
            return
        ip = self.get_client_ip(request)
        key = f"article-view:{article.pk}:{ip}"
        if cache.get(key):
            return
        cache.set(key, True, 60 * 60)
        ArticleView.objects.create(
            article=article,
            user=request.user if request.user.is_authenticated else None,
            ip=ip,
            user_agent=request.META.get("HTTP_USER_AGENT", "")[:400],
            referrer=request.META.get("HTTP_REFERER", "")[:500],
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        article = self.object

        comments_qs = (
            article.comments.approved()
            .select_related("user", "parent", "parent__user")
        )
        top_level = [c for c in comments_qs if c.parent_id is None]
        # Attach replies in Python to avoid N+1 queries.
        replies = {}
        for c in comments_qs:
            if c.parent_id:
                replies.setdefault(c.parent_id, []).append(c)

        paginator = Paginator(top_level, 10)
        page = self.request.GET.get("comment_page")
        ctx["comments"] = paginator.get_page(page)
        ctx["comment_replies"] = replies
        ctx["comment_form"] = CommentForm()
        ctx["related_articles"] = article.related_articles(3)
        counts = article.reaction_counts()
        ctx["reaction_counts"] = counts
        ctx["reaction_counts_json"] = json.dumps(counts)
        ctx["user_reaction"] = self._user_reaction(article)
        return ctx

    def _user_reaction(self, article):
        user = self.request.user
        if not user.is_authenticated:
            return None
        r = article.reactions.filter(user=user).first()
        return r.reaction_type if r else None

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        self.log_view(request, self.object)
        return response


# ---------------------------------------------------------------------------
# Article CRUD (contributors)
# ---------------------------------------------------------------------------
class ArticleCreateView(ContributorRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    template_name = "articles/article_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["author"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Submit a new article"
        ctx["can_auto_publish"] = self.request.user.can_auto_publish
        return ctx

    def form_valid(self, form):
        article = form.save(commit=False)
        article.author = self.request.user
        action = self.request.POST.get("action", "submit")

        if action == "draft":
            article.status = Article.Status.DRAFT
            article.save()
            form.save_m2m()
            messages.info(self.request, "Draft saved.")
        elif action == "publish" and self.request.user.can_auto_publish:
            article.status = Article.Status.PUBLISHED
            article.published_at = timezone.now()
            article.save()
            form.save_m2m()
            messages.success(self.request,
                             "Article published successfully. 🎉")
        else:
            # Students (and faculty choosing review) enter the pending queue.
            article.status = Article.Status.PENDING
            article.submitted_at = timezone.now()
            article.save()
            form.save_m2m()
            messages.success(
                self.request,
                "Your article was submitted and is awaiting editorial "
                "approval.",
            )
        return redirect(article.get_absolute_url()
                        if article.is_published
                        else "articles:my_articles")


class ArticleUpdateView(ContributorRequiredMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    template_name = "articles/article_form.html"
    context_object_name = "article"

    def get_queryset(self):
        qs = Article.objects.select_related("author")
        if self.request.user.is_editor_role:
            return qs
        return qs.filter(author=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Edit: {self.object.title}"
        ctx["can_auto_publish"] = self.request.user.can_auto_publish
        return ctx

    def form_valid(self, form):
        article = form.save(commit=False)
        action = self.request.POST.get("action", "submit")

        if action == "draft":
            article.status = Article.Status.DRAFT
        elif action == "publish" and self.request.user.can_auto_publish:
            article.status = Article.Status.PUBLISHED
            if not article.published_at:
                article.published_at = timezone.now()
        elif article.status in (
            Article.Status.DRAFT, Article.Status.REJECTED
        ):
            # Re-submission goes back into the queue.
            article.status = Article.Status.PENDING
            article.submitted_at = timezone.now()
            article.rejection_reason = ""
        article.save()
        form.save_m2m()
        messages.success(self.request, "Article updated.")
        return redirect(article.get_absolute_url()
                        if article.is_published
                        else "articles:my_articles")


class ArticleDeleteView(ContributorRequiredMixin, DeleteView):
    model = Article
    template_name = "articles/article_confirm_delete.html"
    context_object_name = "article"
    success_url = "/news/my-articles/"

    def get_queryset(self):
        qs = Article.objects.all()
        if self.request.user.is_editor_role:
            return qs
        return qs.filter(author=self.request.user)

    def form_valid(self, form):
        messages.warning(self.request, "Article deleted.")
        return super().form_valid(form)


class MyArticlesView(ContributorRequiredMixin, ListView):
    template_name = "articles/my_articles.html"
    context_object_name = "articles"
    paginate_by = 15

    def get_queryset(self):
        return (
            Article.objects.filter(author=self.request.user)
            .select_related("category")
            .order_by("-updated_at")
        )


# ---------------------------------------------------------------------------
# Comments — AJAX-friendly JSON endpoint
# ---------------------------------------------------------------------------
@login_required
@require_POST
def comment_create(request, slug):
    article = get_object_or_404(Article, slug=slug)
    form = CommentForm(request.POST)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if form.is_valid():
        comment = form.save(commit=False)
        comment.article = article
        comment.user = request.user
        parent_id = request.POST.get("parent")
        if parent_id:
            comment.parent = get_object_or_404(
                Comment, pk=parent_id, article=article
            )
        comment.save()

        if is_ajax:
            return JsonResponse({
                "success": True,
                "id": comment.pk,
                "body": comment.body,
                "user": request.user.display_name,
                "approved": comment.is_approved,
                "message": (
                    "Your comment is live."
                    if comment.is_approved
                    else "Your comment is awaiting moderation."
                ),
                "created_at": timezone.localtime(comment.created_at)
                .strftime("%b %d, %Y, %I:%M %p"),
            })
        messages.success(
            request,
            "Comment posted."
            if comment.is_approved
            else "Your comment is awaiting moderation.",
        )
        return redirect(article.get_absolute_url())

    if is_ajax:
        return JsonResponse(
            {"success": False, "errors": form.errors}, status=400
        )
    messages.error(request, "Comment could not be posted.")
    return redirect(article.get_absolute_url())


class CommentModerationView(EditorRequiredMixin, ListView):
    template_name = "dashboard/comment_moderation.html"
    context_object_name = "comments"
    paginate_by = 25

    def get_queryset(self):
        qs = Comment.objects.select_related("article", "user")
        if self.kwargs.get("queue") == "approved":
            return qs.filter(is_approved=True).order_by("-created_at")
        return qs.filter(is_approved=False).order_by("created_at")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["queue"] = self.kwargs.get("queue", "pending")
        ctx["pending_count"] = Comment.objects.filter(
            is_approved=False
        ).count()
        return ctx


class CommentActionView(EditorRequiredMixin, View):
    """POST only: approve / hide / delete a comment."""

    def post(self, request, pk, action):
        comment = get_object_or_404(Comment, pk=pk)
        if action == "approve":
            comment.approve()
            messages.success(request, "Comment approved.")
        elif action == "hide":
            comment.is_approved = False
            comment.save(update_fields=["is_approved", "updated_at"])
            messages.warning(request, "Comment hidden.")
        elif action == "delete":
            comment.delete()
            messages.warning(request, "Comment deleted.")
        else:
            raise Http404("Unknown moderation action.")
        return redirect(request.META.get("HTTP_REFERER",
                                        "dashboard:comment_moderation"))


# ---------------------------------------------------------------------------
# Reactions (like / love / insightful) — JSON toggle endpoint
# ---------------------------------------------------------------------------
@login_required
@require_POST
def react_to_article(request, slug):
    article = get_object_or_404(
        Article.objects.published(), slug=slug
    )
    reaction_type = request.POST.get("reaction_type", "like")
    if reaction_type not in dict(Reaction.ReactionType.choices):
        return JsonResponse({"success": False, "error": "bad reaction"},
                            status=400)

    existing = Reaction.objects.filter(article=article,
                                       user=request.user).first()
    user_reaction = reaction_type
    if existing and existing.reaction_type == reaction_type:
        # Toggle off when clicking the same reaction.
        existing.delete()
        user_reaction = None
    elif existing:
        existing.reaction_type = reaction_type
        existing.save(update_fields=["reaction_type"])
    else:
        Reaction.objects.create(
            article=article, user=request.user,
            reaction_type=reaction_type
        )

    return JsonResponse({
        "success": True,
        "counts": article.reaction_counts(),
        "user_reaction": user_reaction,
    })
