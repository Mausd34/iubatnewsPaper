"""
accounts/models.py
==================

Custom user model for the IUBAT Campus Newspaper Portal.

``CustomUser`` extends Django's ``AbstractUser`` with the five portal
roles (reader, student contributor, faculty author, editor, admin) plus
student/profile metadata.

NOTE: the model is referenced by ``AUTH_USER_MODEL`` in settings and must
exist *before* the first migration is applied.
"""

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models
from django.templatetags.static import static
from django.urls import reverse

from .managers import CustomUserManager
from .roles import (
    ADMIN_ROLES,
    AUTO_PUBLISH_ROLES,
    COMMENT_MODERATOR_ROLES,
    CONTRIBUTOR_ROLES,
    EDITORIAL_ROLES,
    CustomUserRole,
)

student_id_validator = RegexValidator(
    regex=r"^\d{6,12}$",
    message="Student ID must be 6–12 digits (e.g. 02120345).",
)

DEPARTMENT_CHOICES = [
    ("", "—"),
    ("CSE", "Computer Science and Engineering"),
    ("EEE", "Electrical and Electronic Engineering"),
    ("CE", "Civil Engineering"),
    ("ME", "Mechanical Engineering"),
    ("BBA", "Business Administration"),
    ("MBA", "Master of Business Administration"),
    ("ECON", "Economics"),
    ("ENG", "English"),
    ("AGRI", "Agriculture"),
    ("NFS", "Nutrition and Food Science"),
    ("NUR", "Nursing"),
    ("OTHER", "Other"),
]


class CustomUser(AbstractUser):
    """Portal user with a role and academic profile data."""

    role = models.CharField(
        max_length=20,
        choices=CustomUserRole.choices,
        default=CustomUserRole.READER,
        help_text="Determines what the user can do in the portal.",
        db_index=True,
    )

    # --- Academic / profile metadata ------------------------------------
    student_id = models.CharField(
        max_length=12,
        blank=True,
        validators=[student_id_validator],
        help_text="Official IUBAT student ID (students only).",
    )
    department = models.CharField(
        max_length=10, blank=True, choices=DEPARTMENT_CHOICES
    )
    batch = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Admission year, e.g. 2024.",
    )
    profile_picture = models.ImageField(
        upload_to="profile_pictures/%Y/%m/",
        blank=True,
        null=True,
        help_text="Square image recommended (max 2 MB).",
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        help_text="Short author biography shown on your profile.",
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Verified accounts show a badge and are trusted.",
    )

    # Contact — make email required-ish at form level
    phone = models.CharField(max_length=20, blank=True)

    objects = CustomUserManager()

    class Meta:
        ordering = ("-date_joined",)
        verbose_name = "user"
        verbose_name_plural = "users"
        indexes = [
            models.Index(fields=["role", "is_active"]),
            models.Index(fields=["department"]),
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # ------------------------------------------------------------------
    # URLs
    # ------------------------------------------------------------------
    def get_absolute_url(self):
        return reverse("accounts:profile_detail", kwargs={"username": self.username})

    # ------------------------------------------------------------------
    # Role permission helpers (used across views, templates and the API)
    # ------------------------------------------------------------------
    @property
    def is_reader(self):
        return self.role == CustomUserRole.READER

    @property
    def is_student(self):
        return self.role == CustomUserRole.STUDENT

    @property
    def is_faculty(self):
        return self.role == CustomUserRole.FACULTY

    @property
    def is_editor_role(self):
        return self.role in EDITORIAL_ROLES

    @property
    def is_admin_role(self):
        return self.role in ADMIN_ROLES

    @property
    def can_submit_articles(self):
        return self.role in CONTRIBUTOR_ROLES

    @property
    def can_auto_publish(self):
        """Faculty, editors and admins skip the pending-approval queue."""
        return self.role in AUTO_PUBLISH_ROLES

    @property
    def can_moderate_comments(self):
        return self.role in COMMENT_MODERATOR_ROLES

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    def get_profile_picture(self):
        if self.profile_picture:
            return self.profile_picture.url
        return static("img/default-avatar.svg")

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------
    @property
    def article_count(self):
        return self.articles.filter(status="published").count()
