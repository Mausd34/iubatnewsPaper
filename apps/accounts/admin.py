"""accounts/admin.py — full user administration."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import CustomUser
from .roles import CustomUserRole


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = (
        "username",
        "email",
        "get_full_name",
        "role",
        "department",
        "batch",
        "is_verified",
        "is_staff",
        "is_active",
    )
    list_filter = ("role", "is_verified", "is_staff", "is_active",
                   "department")
    search_fields = ("username", "email", "first_name", "last_name",
                     "student_id")
    ordering = ("-date_joined",)
    list_editable = ("role", "is_verified", "is_active")
    list_per_page = 30

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Portal profile", {
            "fields": (
                "role",
                "student_id",
                "department",
                "batch",
                "phone",
                "bio",
                "profile_picture",
                "is_verified",
            ),
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("Portal profile", {
            "classes": ("wide",),
            "fields": ("role", "department", "batch"),
        }),
    )

    @admin.display(description="Full name")
    def get_full_name(self, obj):
        return obj.get_full_name() or "—"

    actions = ["verify_users", "promote_to_editor", "demote_to_reader"]

    @admin.action(description="Mark selected users as verified")
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f"{updated} user(s) verified.")

    @admin.action(description="Promote selected users to Editor")
    def promote_to_editor(self, request, queryset):
        updated = queryset.update(role=CustomUserRole.EDITOR, is_staff=True)
        self.message_user(request, f"{updated} user(s) promoted to editor.")

    @admin.action(description="Demote selected users to Reader")
    def demote_to_reader(self, request, queryset):
        updated = queryset.update(
            role=CustomUserRole.READER, is_staff=False, is_superuser=False
        )
        self.message_user(request, f"{updated} user(s) demoted to reader.")
