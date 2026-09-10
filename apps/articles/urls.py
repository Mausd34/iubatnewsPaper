"""articles/urls.py"""

from django.urls import path

from . import views

app_name = "articles"

urlpatterns = [
    # Homepage is wired in core/urls.py (HomeView)
    path("news/", views.ArticleListView.as_view(), name="list"),
    path("news/search/", views.ArticleListView.as_view(), name="search"),
    path("category/<slug:slug>/",
         views.CategoryDetailView.as_view(), name="category_detail"),
    path("tag/<slug:slug>/", views.TagDetailView.as_view(), name="tag_detail"),

    # Article CRUD (nested under /news/)
    path("news/submit/", views.ArticleCreateView.as_view(), name="create"),
    path("news/my-articles/",
         views.MyArticlesView.as_view(), name="my_articles"),
    path("news/article/<slug:slug>/",
         views.ArticleDetailView.as_view(), name="detail"),
    path("news/article/<slug:slug>/edit/",
         views.ArticleUpdateView.as_view(), name="update"),
    path("news/article/<slug:slug>/delete/",
         views.ArticleDeleteView.as_view(), name="delete"),

    # Comments
    path("news/article/<slug:slug>/comment/",
         views.comment_create, name="comment_create"),
    path("dashboard/comments/<int:pk>/<str:action>/",
         views.CommentActionView.as_view(), name="comment_action"),

    # Reactions
    path("news/article/<slug:slug>/react/",
         views.react_to_article, name="react"),
]
