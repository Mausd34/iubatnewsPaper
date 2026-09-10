"""dashboard/urls.py"""

from django.urls import path

from apps.articles.views import CommentModerationView

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardHomeView.as_view(), name="home"),

    # Editorial queue
    path("pending/",
         views.PendingArticlesView.as_view(), name="pending_articles"),
    path("review/<int:pk>/",
         views.ArticleReviewView.as_view(), name="article_review"),
    path("approve/<int:pk>/",
         views.ApproveArticleView.as_view(), name="approve_article"),
    path("reject/<int:pk>/",
         views.RejectArticleView.as_view(), name="reject_article"),

    # Comment moderation
    path("comments/",
         CommentModerationView.as_view(), name="comment_moderation"),
    path("comments/approved/",
         CommentModerationView.as_view(),
         {"queue": "approved"}, name="comment_moderation_approved"),

    # User management (admin)
    path("users/", views.UserManagementView.as_view(), name="users"),
    path("users/<int:pk>/edit/",
         views.UserEditView.as_view(), name="user_edit"),

    # Category management (editor+)
    path("categories/",
         views.CategoryManagementView.as_view(), name="categories"),
    path("categories/new/",
         views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/",
         views.CategoryUpdateView.as_view(), name="category_update"),
    path("categories/<int:pk>/delete/",
         views.CategoryDeleteView.as_view(), name="category_delete"),
]
