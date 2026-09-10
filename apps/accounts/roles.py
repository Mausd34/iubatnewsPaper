"""Role definitions and role-based permission helpers.

Centralising the roles here keeps models, views, DRF permissions and the
admin in sync.
"""

from django.db import models


class CustomUserRole(models.TextChoices):
    READER = "reader", "Reader"
    STUDENT = "student", "Student Contributor"
    FACULTY = "faculty", "Faculty Author"
    EDITOR = "editor", "Editor"
    ADMIN = "admin", "Admin"


# Role hierarchy — higher number implies every permission of lower roles.
ROLE_LEVEL = {
    CustomUserRole.READER: 0,
    CustomUserRole.STUDENT: 1,
    CustomUserRole.FACULTY: 2,
    CustomUserRole.EDITOR: 3,
    CustomUserRole.ADMIN: 4,
}

# Which roles may submit articles at all
CONTRIBUTOR_ROLES = (
    CustomUserRole.STUDENT,
    CustomUserRole.FACULTY,
    CustomUserRole.EDITOR,
    CustomUserRole.ADMIN,
)

# Which roles bypass the editorial approval queue (auto-publish)
AUTO_PUBLISH_ROLES = (
    CustomUserRole.FACULTY,
    CustomUserRole.EDITOR,
    CustomUserRole.ADMIN,
)

# Which roles may review/approve/reject work
EDITORIAL_ROLES = (
    CustomUserRole.EDITOR,
    CustomUserRole.ADMIN,
)

ADMIN_ROLES = (CustomUserRole.ADMIN,)

# Moderation of comments
COMMENT_MODERATOR_ROLES = (
    CustomUserRole.EDITOR,
    CustomUserRole.ADMIN,
)


def role_at_least(user, role):
    """True if *user*'s role level is >= the given role level."""
    if not user or not user.is_authenticated:
        return False
    return ROLE_LEVEL.get(user.role, 0) >= ROLE_LEVEL[role]
