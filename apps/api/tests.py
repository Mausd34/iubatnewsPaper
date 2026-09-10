"""Tests for the REST API: JWT, permissions, workflows."""

from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import CustomUser
from apps.accounts.roles import CustomUserRole
from apps.articles.models import Article, Category

from rest_framework_simplejwt.tokens import RefreshToken


def jwt_for(user):
    refresh = RefreshToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}


class ArticleApiTests(APITestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Academic", icon="🎓")
        self.editor = CustomUser.objects.create_user(
            "editor", "ed@iubat.edu", "pass12345",
            role=CustomUserRole.EDITOR,
        )
        self.student = CustomUser.objects.create_user(
            "student", "st@iubat.edu", "pass12345",
            role=CustomUserRole.STUDENT,
        )
        self.reader = CustomUser.objects.create_user(
            "reader", "rd@iubat.edu", "pass12345",
            role=CustomUserRole.READER,
        )
        self.article = Article.objects.create(
            title="Published Academic Story for the API tests",
            author=self.editor, category=self.cat,
            excerpt="A long enough excerpt for model validation here.",
            content="<p>Published body.</p>",
            status="published", published_at=timezone.now(),
        )

    def test_list_is_public(self):
        r = self.client.get("/api/articles/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["count"], 1)

    def test_token_obtain(self):
        r = self.client.post("/api/token/", {
            "username": "student", "password": "pass12345",
        }, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertIn("access", r.data)

    def test_reader_cannot_create(self):
        r = self.client.post(
            "/api/articles/",
            {"title": "Spam", "category_slug": self.cat.slug,
             "excerpt": "Readers should not be able to post articles here.",
             "content": "<p>x</p>"},
            format="json", **jwt_for(self.reader),
        )
        self.assertEqual(r.status_code, 403)

    def test_student_create_is_pending(self):
        payload = {
            "title": "Student API Submission Story",
            "category_slug": self.cat.slug,
            "excerpt": "Submitted through the REST API as JSON data.",
            "content": "<p>Hello API.</p>",
            "workflow": "submit",
        }
        r = self.client.post("/api/articles/", payload, format="json",
                             **jwt_for(self.student))
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["status"], "pending")

    def test_faculty_create_publishes(self):
        faculty = CustomUser.objects.create_user(
            "faculty", "fa@iubat.edu", "pass12345",
            role=CustomUserRole.FACULTY,
        )
        payload = {
            "title": "Faculty API Published Story",
            "category_slug": self.cat.slug,
            "excerpt": "Faculty workflow publishes immediately via API.",
            "content": "<p>Live now.</p>",
            "workflow": "publish",
        }
        r = self.client.post("/api/articles/", payload, format="json",
                             **jwt_for(faculty))
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["status"], "published")

    def test_student_cannot_edit_others(self):
        r = self.client.patch(
            f"/api/articles/{self.article.pk}/",
            {"title": "Hijacked"},
            format="json", **jwt_for(self.student),
        )
        self.assertEqual(r.status_code, 403)

    def test_editor_publish_action(self):
        pending = Article.objects.create(
            title="Queued for editorial review via API",
            author=self.student, category=self.cat,
            excerpt="Pending queue item used in the API tests.",
            content="<p>Review me.</p>", status="pending",
        )
        r = self.client.post(
            f"/api/articles/{pending.pk}/publish/", **jwt_for(self.editor)
        )
        self.assertEqual(r.status_code, 200)
        pending.refresh_from_db()
        self.assertEqual(pending.status, "published")

    def test_filter_and_search(self):
        r = self.client.get(
            "/api/articles/", {"category": "academic", "search": "api"}
        )
        self.assertEqual(r.status_code, 200)
        self.assertGreaterEqual(r.data["count"], 1)

    def test_nested_author_and_category(self):
        r = self.client.get(f"/api/articles/{self.article.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.data["author"]["username"], "editor")
        self.assertEqual(r.data["category"]["slug"], "academic")


class CategoryCommentApiTests(APITestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Notice Board", icon="📢")
        self.editor = CustomUser.objects.create_user(
            "ed", "ed2@iubat.edu", "pass12345",
            role=CustomUserRole.EDITOR,
        )
        self.article = Article.objects.create(
            title="Notice for comments API tests",
            author=self.editor, category=self.cat,
            excerpt="Notice board excerpt long enough to validate.",
            content="<p>Notice.</p>", status="published",
            published_at=timezone.now(),
        )

    def test_reader_cannot_create_category(self):
        reader = CustomUser.objects.create_user(
            "r", "r2@iubat.edu", "pass12345", role=CustomUserRole.READER
        )
        r = self.client.post(
            "/api/categories/",
            {"name": "Hack", "slug": "hack"},
            format="json", **jwt_for(reader),
        )
        self.assertEqual(r.status_code, 403)

    def test_editor_creates_category(self):
        r = self.client.post(
            "/api/categories/",
            {"name": "Opinion", "icon": "🗣", "order": 9},
            format="json", **jwt_for(self.editor),
        )
        self.assertEqual(r.status_code, 201, r.data)
        self.assertEqual(r.data["slug"], "opinion")

    def test_comment_create_authenticated(self):
        student = CustomUser.objects.create_user(
            "s", "s2@iubat.edu", "pass12345",
            role=CustomUserRole.STUDENT,
        )
        # student is unverified → 202 accepted (held for moderation)
        r = self.client.post(
            "/api/comments/",
            {"article_slug": self.article.slug, "body": "Well written!"},
            format="json", **jwt_for(student),
        )
        self.assertEqual(r.status_code, 202)
