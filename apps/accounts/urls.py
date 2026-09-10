"""accounts/urls.py — registration, login/logout and profiles."""

from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.IUBATLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    path("profile/edit/", views.ProfileUpdateView.as_view(),
         name="profile_edit"),
    path("profile/<slug:username>/", views.ProfileDetailView.as_view(),
         name="profile_detail"),
]
