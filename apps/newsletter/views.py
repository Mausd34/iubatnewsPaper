"""newsletter/views.py — public subscribe/unsubscribe + staff composer."""

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import (
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
)

from apps.accounts.decorators import editor_required
from apps.accounts.mixins import EditorRequiredMixin

from .forms import NewsletterComposeForm, SubscribeForm
from .models import NewsletterEmail, Subscriber


@require_POST
def subscribe(request):
    """Footer subscription form (works with and without JavaScript)."""
    form = SubscribeForm(request.POST)
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if not form.is_valid():
        if is_ajax:
            return JsonResponse(
                {"success": False, "errors": form.errors}, status=400
            )
        messages.error(request, "Please enter a valid email address.")
        return redirect("core:home")

    email = form.cleaned_data["email"]
    full_name = form.cleaned_data.get("full_name", "")
    subscriber, created = Subscriber.objects.get_or_create(
        email=email, defaults={"full_name": full_name}
    )

    if created:
        msg = "Thanks for subscribing to IUBAT Campus News!"
    elif subscriber.is_active:
        msg = "You are already subscribed — watch your inbox."
    else:
        # Re-subscribe an old address.
        subscriber.is_active = True
        subscriber.unsubscribed_at = None
        subscriber.save(update_fields=["is_active", "unsubscribed_at"])
        msg = "Welcome back — your subscription was renewed."

    if is_ajax:
        return JsonResponse({"success": True, "message": msg})
    messages.success(request, msg)
    return redirect("core:home")


def unsubscribe(request, token):
    subscriber = get_object_or_404(Subscriber, token=token)
    if subscriber.is_active:
        subscriber.is_active = False
        subscriber.unsubscribed_at = timezone.now()
        subscriber.save(update_fields=["is_active", "unsubscribed_at"])
        confirmed = True
    else:
        confirmed = False
    return TemplateView.as_view(
        template_name="newsletter/unsubscribe.html"
    )(request, subscriber=subscriber, confirmed=confirmed)


class NewsletterListView(EditorRequiredMixin, ListView):
    template_name = "newsletter/list.html"
    context_object_name = "emails"
    model = NewsletterEmail
    paginate_by = 20

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_subscribers"] = Subscriber.objects.filter(
            is_active=True
        ).count()
        return ctx


class NewsletterComposeView(EditorRequiredMixin, UpdateView):
    """Create a draft (GET form is rendered empty via /compose/) or edit."""

    template_name = "newsletter/compose.html"
    form_class = NewsletterComposeForm
    model = NewsletterEmail
    context_object_name = "email_obj"

    def get_object(self, queryset=None):
        pk = self.kwargs.get("pk")
        if pk:
            return super().get_object(queryset)
        return None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["active_subscribers"] = Subscriber.objects.filter(
            is_active=True
        ).count()
        return ctx

    def get_success_url(self):
        return self.object.get_absolute_url()

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            email_obj = form.save(commit=False)
            email_obj.created_by = request.user
            email_obj.save()
            if request.POST.get("action") == "send":
                count = email_obj.send(user=request.user)
                messages.success(
                    request,
                    f"Newsletter sent to {count} subscriber(s).",
                )
                return redirect("newsletter:list")
            messages.success(request, "Draft saved.")
            return redirect(email_obj.get_absolute_url())
        return self.form_invalid(form)


class NewsletterPreviewView(EditorRequiredMixin, DetailView):
    template_name = "newsletter/preview.html"
    model = NewsletterEmail
    context_object_name = "email_obj"


@editor_required
@require_POST
def newsletter_send(request, pk):
    email_obj = get_object_or_404(NewsletterEmail, pk=pk)
    count = email_obj.send(user=request.user)
    messages.success(
        request, f"Newsletter sent to {count} subscriber(s)."
    )
    return redirect("newsletter:list")
