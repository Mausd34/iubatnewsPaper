"""Model managers for the accounts app."""

from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    """Manager that uses email as an optional-but-encouraged identifier and
    supports CLI creation via ``manage.py createsuperuser``."""

    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError("Users must have a username.")
        email = self.normalize_email(email) if email else ""
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email="", password=None, **extra_fields):
        extra_fields.setdefault("role", CustomUserRole.READER)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email="", password=None,
                         **extra_fields):
        extra_fields.setdefault("role", CustomUserRole.ADMIN)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(username, email, password, **extra_fields)

    # Convenience querysets ------------------------------------------------
    def staff(self):
        """Editors and admins (Django staff flag)."""
        return self.filter(is_staff=True)

    def contributors(self):
        """Users allowed to submit articles."""
        return self.filter(
            role__in=[
                CustomUserRole.STUDENT,
                CustomUserRole.FACULTY,
                CustomUserRole.EDITOR,
                CustomUserRole.ADMIN,
            ]
        )


# Imported here (and re-exported) to avoid a circular import in models.py.
from .roles import CustomUserRole  # noqa: E402
