"""newsletter/admin.py"""

from django.contrib import admin

from .models import NewsletterEmail, Subscriber


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "full_name", "is_active", "subscribed_at")
    list_filter = ("is_active", "subscribed_at")
    search_fields = ("email", "full_name")
    readonly_fields = ("token", "subscribed_at", "unsubscribed_at")
    actions = ["activate", "deactivate"]

    @admin.action(description="Activate selected subscribers")
    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} activated.")

    @admin.action(description="Deactivate selected subscribers")
    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} deactivated.")


@admin.register(NewsletterEmail)
class NewsletterEmailAdmin(admin.ModelAdmin):
    list_display = ("subject", "status", "recipients_count",
                    "created_by", "sent_at", "created_at")
    list_filter = ("status", "created_at", "sent_at")
    search_fields = ("subject", "body")
    readonly_fields = ("slug", "recipients_count", "sent_at",
                       "created_at", "updated_at")
