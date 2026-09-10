"""
api/urls.py
===========

Router-registered REST endpoints plus JWT token routes.

    POST /api/token/           -> obtain access + refresh token
    POST /api/token/refresh/   -> exchange refresh for new access
    GET  /api/articles/        -> paginated, filterable article list
    ...
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from . import views

app_name = "api"

router = DefaultRouter()
router.register(r"articles", views.ArticleViewSet, basename="article")
router.register(r"categories", views.CategoryViewSet, basename="category")
router.register(r"tags", views.TagViewSet, basename="tag")
router.register(r"comments", views.CommentViewSet, basename="comment")
router.register(r"reactions", views.ReactionViewSet, basename="reaction")

urlpatterns = [
    # JWT
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(),
         name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    # Browsable API auth (session login for the DRF web UI)
    path("auth/", include("rest_framework.urls")),

    path("", include(router.urls)),
]
