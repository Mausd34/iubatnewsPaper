"""Account signals.

* Editors/admins automatically gain Django staff access so they can reach
  the editorial dashboard (and, for admins, the Django admin).
* Newly registered students start unverified; faculty are pre-verified.
"""

from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .roles import CustomUserRole

STAFF_ROLES = {CustomUserRole.EDITOR, CustomUserRole.ADMIN}


@receiver(pre_save, sender=settings.AUTH_USER_MODEL)
def sync_staff_flag_with_role(sender, instance, **kwargs):
    """Keep ``is_staff`` / ``is_superuser`` consistent with the role."""
    if instance.role in STAFF_ROLES:
        instance.is_staff = True
    elif instance.role == CustomUserRole.ADMIN:
        instance.is_superuser = True

    if instance.role not in STAFF_ROLES and not instance.is_superuser:
        # Downgrading someone away from editor/admin removes staff access,
        # unless they are a plain superuser.
        instance.is_staff = False

    # Faculty authors are trusted by default.
    if instance.role == CustomUserRole.FACULTY:
        instance.is_verified = True
