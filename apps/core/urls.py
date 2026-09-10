"""core/urls.py"""

from django.urls import path

from apps.articles.views import HomeView

from . import views

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("robots.txt", views.robots_txt, name="robots"),
    path("health/", views.health_check, name="health_check"),
]
