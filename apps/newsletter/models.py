"""newsletter/models.py — subscriptions and sent campaign emails."""

import uuid

from django.conf import settings
from django.core.validators import EmailValidator
from django.db import models
from django.utils.text import slugify


class Subscriber(models.Model):
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    full_name = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(
        default=True, help_text="Inactive subscribers are unsubscribed."
    )
    token = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True
    )
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-subscribed_at",)
        verbose_name = "subscriber"
        verbose_name_plural = "subscribers"
        indexes = [models.Index(fields=["is_active", "-subscribed_at"])]

    def __str__(self):
        state = "active" if self.is_active else "unsubscribed"
        return f"{self.email} ({state})"

    def get_unsubscribe_url(self):
        from django.urls import reverse
        return reverse("newsletter:unsubscribe",
                       kwargs={"token": self.token})


class NewsletterEmail(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent"

    subject = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    body = models.TextField(help_text="Plain text or simple HTML.")
    status = models.CharField(
        max_length=6, choices=Status.choices, default=Status.DRAFT
    )
    recipients_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="newsletter_emails",
    )
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "newsletter email"
        verbose_name_plural = "newsletter emails"

    def __str__(self):
        return f"{self.subject} ({self.get_status_display()})"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("newsletter:email_preview", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.subject)[:220] or "campaign"
        super().save(*args, **kwargs)

    def send(self, user=None):
        """Deliver the campaign to all active subscribers (BCC)."""
        from django.conf import settings as dj_settings
        from django.core.mail import EmailMultiAlternatives
        from django.utils import timezone

        recipients = list(
            Subscriber.objects.filter(is_active=True)
            .values_list("email", flat=True)
        )
        if recipients:
            message = EmailMultiAlternatives(
                subject=self.subject,
                body=self.body,
                from_email=dj_settings.DEFAULT_FROM_EMAIL,
                to=[dj_settings.DEFAULT_FROM_EMAIL],
                bcc=recipients,
            )
            message.attach_alternative(self.body, "text/html")
            message.send(fail_silently=False)

        self.status = self.Status.SENT
        self.sent_at = timezone.now()
        self.recipients_count = len(recipients)
        if user is not None:
            self.created_by = user
        self.save()
        return len(recipients)
