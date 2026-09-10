"""
dashboard/views.py
==================

Editorial dashboard: stats, the pending-article queue, approve/reject
workflow, comment moderation link, user management (admin) and category
management.
"""

from django.contrib import messages
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)
from django.views.generic.edit import DeleteView

from apps.accounts.forms import AdminUserEditForm
from apps.accounts.mixins import (
    AdminRequiredMixin,
    ContributorRequiredMixin,
    EditorRequiredMixin,
)
from apps.accounts.models import CustomUser
from apps.accounts.roles import CustomUserRole
from apps.articles.forms import RejectArticleForm
from apps.articles.models import (
    Article,
    ArticleView,
    Category,
    Comment,
    Reaction,
)
from apps.newsletter.models import Subscriber

from .forms import CategoryForm

import json
from django.http import JsonResponse


# ---------------------------------------------------------------------------
# Dashboard home with stats
# ---------------------------------------------------------------------------
class DashboardHomeView(ContributorRequiredMixin, TemplateView):
    template_name = "dashboard/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        is_staff = user.is_editor_role

        if is_staff:
            articles_qs = Article.objects.all()
        else:
            articles_qs = Article.objects.filter(author=user)

        ctx.update(
            total_articles=articles_qs.filter(
                status=Article.Status.PUBLISHED).count(),
            pending_count=Article.objects.pending().count()
            if is_staff
            else articles_qs.pending().count(),
            draft_count=articles_qs.filter(
                status=Article.Status.DRAFT).count(),
            rejected_count=articles_qs.filter(
                status=Article.Status.REJECTED).count(),
            total_users=CustomUser.objects.count() if is_staff else None,
            total_views=ArticleView.objects.count() if is_staff
            else ArticleView.objects.filter(
                article__author=user).count(),
            total_comments=Comment.objects.count() if is_staff
            else Comment.objects.filter(article__author=user).count(),
            subscriber_count=Subscriber.objects.filter(
                is_active=True).count() if is_staff else None,
            recent_articles=articles_qs.select_related("category",
                                                       "author")[:8],
            pending_articles=(
                Article.objects.pending().select_related(
                    "author", "category")[:8]
                if is_staff else []
            ),
        )
        if is_staff:
            ctx.update(
                views_by_day=self._views_by_day(),
                articles_by_category=self._articles_by_category(),
                users_by_role=self._users_by_role(),
            )
        return ctx

    # Chart.js data -------------------------------------------------------
    def _views_by_day(self, days=14):
        since = timezone.now() - timezone.timedelta(days=days)
        rows = (
            ArticleView.objects.filter(timestamp__gte=since)
            .annotate(day=TruncDate("timestamp"))
            .values("day")
            .annotate(n=Count("id"))
            .order_by("day")
        )
        # Fill missing days with zero for a clean chart.
        labels, data = [], []
        by_day = {r["day"]: r["n"] for r in rows}
        for i in range(days, -1, -1):
            day = (timezone.now() - timezone.timedelta(days=i)).date()
            labels.append(day.strftime("%b %d"))
            data.append(by_day.get(day, 0))
        return json.dumps({"labels": labels, "data": data})

    def _articles_by_category(self):
        rows = (
            Category.objects.filter(articles__status="published")
            .annotate(n=Count("articles"))
            .values_list("name", "n")
            .order_by("-n")
        )
        return json.dumps({
            "labels": [r[0] for r in rows],
            "data": [r[1] for r in rows],
        })

    def _users_by_role(self):
        rows = (
            CustomUser.objects.values("role")
            .annotate(n=Count("id"))
            .values_list("role", "n")
        )
        labels = dict(CustomUserRole.choices)
        return json.dumps({
            "labels": [labels.get(r, r) for r, _ in rows],
            "data": [n for _, n in rows],
        })


# ---------------------------------------------------------------------------
# Editorial queue
# ---------------------------------------------------------------------------
class PendingArticlesView(EditorRequiredMixin, ListView):
    template_name = "dashboard/pending_articles.html"
    context_object_name = "articles"
    paginate_by = 20

    def get_queryset(self):
        return (
            Article.objects.pending()
            .select_related("author", "category")
            .prefetch_related("tags")
            .order_by("submitted_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["pending_total"] = Article.objects.pending().count()
        return ctx


class ArticleReviewView(EditorRequiredMixin, DetailView):
    """Read a pending article + see reject form."""

    template_name = "dashboard/article_review.html"
    context_object_name = "article"
    model = Article

    def get_queryset(self):
        return Article.objects.select_related("author", "category",
                                              "reviewed_by")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["reject_form"] = RejectArticleForm()
        return ctx


class ApproveArticleView(EditorRequiredMixin, DetailView):
    model = Article
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        article = self.get_object()
        article.publish(reviewer=request.user)
        messages.success(request,
                         f"“{article.title}” is now published. ✅")
        return redirect("dashboard:pending_articles")


class RejectArticleView(EditorRequiredMixin, DetailView):
    model = Article
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        article = self.get_object()
        form = RejectArticleForm(request.POST)
        if form.is_valid():
            article.reject(form.cleaned_data["reason"],
                           reviewer=request.user)
            messages.warning(
                request, f"“{article.title}” was rejected with feedback."
            )
            return redirect("dashboard:pending_articles")
        messages.error(request, "A rejection reason (10+ characters) "
                                "is required.")
        return redirect("dashboard:article_review", pk=article.pk)


# ---------------------------------------------------------------------------
# User management (admin only)
# ---------------------------------------------------------------------------
class UserManagementView(AdminRequiredMixin, ListView):
    template_name = "dashboard/users.html"
    context_object_name = "users"
    model = CustomUser
    paginate_by = 30

    def get_queryset(self):
        qs = CustomUser.objects.all().order_by("-date_joined")
        role = self.request.GET.get("role")
        q = self.request.GET.get("q")
        if role:
            qs = qs.filter(role=role)
        if q:
            qs = qs.filter(
                Q(username__icontains=q)
                | Q(email__icontains=q)
                | Q(first_name__icontains=q)
                | Q(last_name__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["roles"] = CustomUserRole.choices
        ctx["active_role"] = self.request.GET.get("role", "")
        ctx["q"] = self.request.GET.get("q", "")
        return ctx


class UserEditView(AdminRequiredMixin, UpdateView):
    template_name = "dashboard/user_edit.html"
    model = CustomUser
    form_class = AdminUserEditForm
    context_object_name = "edited_user"
    success_url = reverse_lazy("dashboard:users")

    def form_valid(self, form):
        messages.success(self.request, "User updated.")
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Category management (editor+)
# ---------------------------------------------------------------------------
class CategoryManagementView(EditorRequiredMixin, ListView):
    template_name = "dashboard/categories.html"
    context_object_name = "categories"
    model = Category
    paginate_by = 25

    def get_queryset(self):
        return Category.objects.with_article_counts()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["form"] = CategoryForm()
        return ctx


class CategoryCreateView(EditorRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy("dashboard:categories")
    template_name = "dashboard/category_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Category created.")
        return super().form_valid(form)


class CategoryUpdateView(EditorRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    success_url = reverse_lazy("dashboard:categories")
    template_name = "dashboard/category_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Category updated.")
        return super().form_valid(form)


class CategoryDeleteView(EditorRequiredMixin, DeleteView):
    model = Category
    success_url = reverse_lazy("dashboard:categories")
    template_name = "dashboard/category_confirm_delete.html"

    def post(self, request, *args, **kwargs):
        category = self.get_object()
        if category.articles.exists():
            messages.error(
                request,
                f"“{category.name}” still has "
                f"{category.articles.count()} article(s). Move or delete "
                "them before removing the category.",
            )
            return redirect("dashboard:categories")
        messages.warning(request, "Category deleted.")
        return super().post(request, *args, **kwargs)
