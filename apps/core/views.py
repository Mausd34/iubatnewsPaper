"""core/views.py — static-ish pages and contact."""

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import HttpResponse
from django.template import TemplateDoesNotExist, loader
from django.urls import reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from .forms import ContactForm


class AboutView(TemplateView):
    template_name = "core/about.html"


class ContactView(FormView):
    template_name = "core/contact.html"
    form_class = ContactForm
    success_url = reverse_lazy("core:contact")

    def form_valid(self, form):
        data = form.cleaned_data
        try:
            send_mail(
                subject=f"[IUBAT News contact] {data['subject']}",
                message=(
                    f"From: {data['name']} <{data['email']}>\n\n"
                    f"{data['message']}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
            messages.success(
                self.request,
                "Thanks for reaching out! We'll get back to you soon.",
            )
        except Exception:  # pragma: no cover - mail server not configured
            messages.success(
                self.request,
                "Thanks! Your message was recorded (email delivery is "
                "not configured in development).",
            )
        return super().form_valid(form)


def robots_txt(request):
    """Serve /robots.txt (sitemap is wired in config/urls.py)."""
    try:
        template = loader.get_template("robots.txt")
    except TemplateDoesNotExist:  # pragma: no cover
        return HttpResponse("User-agent: *\nAllow: /\n",
                            content_type="text/plain")
    return HttpResponse(template.render({"request": request}),
                        content_type="text/plain")


def health_check(request):
    """Tiny deployment health-check endpoint."""
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return HttpResponse("ok", content_type="text/plain")
    except Exception:  # pragma: no cover
        return HttpResponse("db-error", status=503,
                            content_type="text/plain")
