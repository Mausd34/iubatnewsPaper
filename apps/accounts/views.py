"""Account views: register, login/logout (built-in), profile pages."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, UpdateView

from .forms import (
    IUBATAuthenticationForm,
    ProfileUpdateForm,
    RegisterForm,
)
from .models import CustomUser


class RegisterView(CreateView):
    template_name = "accounts/register.html"
    form_class = RegisterForm

    def form_valid(self, form):
        user = form.save()
        # Log the user straight in after a successful registration.
        login(self.request, user,
              backend="django.contrib.auth.backends.ModelBackend")
        messages.success(
            self.request,
            f"Welcome to IUBAT Campus News, {user.display_name}! "
            "Your account has been created.",
        )
        return redirect("core:home")


class IUBATLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = IUBATAuthenticationForm


class ProfileDetailView(DetailView):
    model = CustomUser
    template_name = "accounts/profile_detail.html"
    context_object_name = "profile_user"
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        articles = (
            self.object.articles.filter(status="published")
            .select_related("author", "category")
            .prefetch_related("tags")
        )
        ctx["articles"] = list(articles[:9])
        ctx["article_total"] = articles.count()
        return ctx


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileUpdateForm
    template_name = "accounts/profile_edit.html"

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            "accounts:profile_detail",
            kwargs={"username": self.request.user.username},
        )
