"""Tests for roles, the custom user manager and role signals."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from .roles import CustomUserRole

User = get_user_model()


class CustomUserTests(TestCase):
    def test_create_reader_defaults(self):
        user = User.objects.create_user("reader1", "r@iubat.edu", "pass12345")
        self.assertEqual(user.role, CustomUserRole.READER)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.can_submit_articles)
        self.assertEqual(str(user), f"{user.username} (Reader)")

    def test_create_student_contributor(self):
        user = User.objects.create_user(
            "stu", "s@iubat.edu", "pass12345",
            role=CustomUserRole.STUDENT,
        )
        self.assertTrue(user.can_submit_articles)
        self.assertFalse(user.can_auto_publish)

    def test_faculty_can_auto_publish_and_verified(self):
        user = User.objects.create_user(
            "fac", "f@iubat.edu", "pass12345",
            role=CustomUserRole.FACULTY,
        )
        # Signal auto-verifies faculty.
        self.assertTrue(user.can_auto_publish)
        self.assertTrue(user.is_verified)

    def test_editor_gets_staff_flag_via_signal(self):
        user = User.objects.create_user(
            "ed", "e@iubat.edu", "pass12345",
            role=CustomUserRole.EDITOR,
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_editor_role)
        self.assertTrue(user.can_moderate_comments)

    def test_superuser_is_admin(self):
        admin = User.objects.create_superuser(
            "root", "root@iubat.edu", "pass12345"
        )
        self.assertEqual(admin.role, CustomUserRole.ADMIN)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_admin_role)

    def test_downgrade_removes_staff(self):
        user = User.objects.create_user(
            "ed2", "e2@iubat.edu", "pass12345",
            role=CustomUserRole.EDITOR,
        )
        self.assertTrue(user.is_staff)
        user.role = CustomUserRole.READER
        user.save()
        user.refresh_from_db()
        self.assertFalse(user.is_staff)

    def test_profile_absolute_url(self):
        user = User.objects.create_user("me", "me@iubat.edu", "pass12345")
        self.assertEqual(user.get_absolute_url(), "/accounts/profile/me/")
