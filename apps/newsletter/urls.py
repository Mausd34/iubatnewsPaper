"""newsletter/urls.py"""

from django.urls import path

from . import views

app_name = "newsletter"

urlpatterns = [
    path("subscribe/", views.subscribe, name="subscribe"),
    path("unsubscribe/<uuid:token>/",
         views.unsubscribe, name="unsubscribe"),

    # Staff composer
    path("dashboard/newsletters/",
         views.NewsletterListView.as_view(), name="list"),
    path("dashboard/newsletters/compose/",
         views.NewsletterComposeView.as_view(), name="compose"),
    path("dashboard/newsletters/<int:pk>/",
         views.NewsletterPreviewView.as_view(), name="email_preview"),
    path("dashboard/newsletters/<int:pk>/edit/",
         views.NewsletterComposeView.as_view(), name="edit"),
    path("dashboard/newsletters/<int:pk>/send/",
         views.newsletter_send, name="send"),
]
