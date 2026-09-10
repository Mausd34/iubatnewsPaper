"""Tests for article models, workflow, views, comments and reactions."""

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import CustomUser
from apps.accounts.roles import CustomUserRole

from .models import (
    Article,
    ArticleView,
    Category,
    Comment,
    Reaction,
    Tag,
)


def make_user(username, role=CustomUserRole.STUDENT, password="pass12345"):
    return CustomUser.objects.create_user(
        username, f"{username}@iubat.edu", password, role=role
    )


def make_article(author, category, status="published", title=None,
                 days_ago=1):
    article = Article(
        title=title or f"Story about {category.name} by {author.username}",
        author=author,
        category=category,
        excerpt="This is a sufficiently long excerpt for validation "
                "purposes of the article model.",
        content="<p>Body content of the test article.</p>",
    )
    if status == "published":
        article.status = Article.Status.PUBLISHED
        article.published_at = timezone.now() - timezone.timedelta(
            days=days_ago
        )
    article.save()
    return article


class ModelTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Campus News", icon="📰")
        self.tag = Tag.objects.create(name="tech")
        self.author = make_user("writer", CustomUserRole.FACULTY)

    def test_slugs_auto_generated_and_unique(self):
        self.assertEqual(self.cat.slug, "campus-news")
        a1 = make_article(self.author, self.cat, title="Big Day on Campus")
        self.assertEqual(a1.slug, "big-day-on-campus")
        a2 = make_article(self.author, self.cat, title="Big Day on Campus")
        self.assertNotEqual(a1.slug, a2.slug)

    def test_published_manager_hides_drafts(self):
        make_article(self.author, self.cat)
        make_article(self.author, self.cat, status="draft",
                     title="A hidden draft article")
        self.assertEqual(Article.objects.count(), 2)
        self.assertEqual(Article.objects.published().count(), 1)

    def test_submit_publish_reject_workflow(self):
        editor = make_user("boss", CustomUserRole.EDITOR)
        article = make_article(self.author, self.cat, status="draft",
                               title="Pending student report")
        article.submit()
        self.assertEqual(article.status, "pending")
        self.assertIsNotNone(article.submitted_at)

        article.reject("Need two interviews.", reviewer=editor)
        self.assertEqual(article.status, "rejected")
        self.assertEqual(article.reviewed_by, editor)

        article.publish(reviewer=editor)
        self.assertEqual(article.status, "published")
        self.assertIsNotNone(article.published_at)

    def test_view_log_increments_counter(self):
        article = make_article(self.author, self.cat)
        self.assertEqual(article.views_count, 0)
        ArticleView.objects.create(article=article, ip="1.1.1.1")
        article.refresh_from_db()
        self.assertEqual(article.views_count, 1)

    def test_trending_ranks_by_recent_views(self):
        hot = make_article(self.author, self.cat, title="Hot story now")
        cold = make_article(self.author, self.cat, title="Old cold story")
        for i in range(5):
            ArticleView.objects.create(article=hot, ip=f"1.1.1.{i}")
        trending = list(Article.objects.trending())
        # Only articles with views in the trailing window are listed,
        # and the most-viewed one ranks first.
        self.assertEqual(trending[0], hot)
        self.assertNotIn(cold, trending)

    def test_unique_reaction_per_user(self):
        article = make_article(self.author, self.cat)
        reader = make_user("reader", CustomUserRole.READER)
        Reaction.objects.create(article=article, user=reader,
                                reaction_type="like")
        with self.assertRaises(Exception):
            Reaction.objects.create(article=article, user=reader,
                                    reaction_type="love")

    def test_comment_approved_for_verified_only(self):
        verified = make_user("ver", CustomUserRole.FACULTY)
        unverified = make_user("unver", CustomUserRole.READER)
        article = make_article(self.author, self.cat)
        ok = Comment.objects.create(article=article, user=verified,
                                    body="Great read!")
        held = Comment.objects.create(article=article, user=unverified,
                                      body="My first comment")
        self.assertTrue(ok.is_approved)
        self.assertFalse(held.is_approved)


class PublicViewTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Sports", icon="⚽")
        self.author = make_user("writer", CustomUserRole.FACULTY)
        self.article = make_article(self.author, self.cat,
                                    title="Football Final Coverage")

    def test_home_and_list(self):
        self.assertEqual(self.client.get("/").status_code, 200)
        self.assertEqual(self.client.get("/news/").status_code, 200)

    def test_detail_page(self):
        r = self.client.get(self.article.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Football Final Coverage")

    def test_search_finds_article(self):
        r = self.client.get("/news/", {"q": "football"})
        self.assertContains(r, "Football Final Coverage")

    def test_detail_logs_view_once_per_hour(self):
        url = self.article.get_absolute_url()
        self.client.get(url)
        self.client.get(url)  # throttled by IP for 1 hour
        self.assertEqual(ArticleView.objects.count(), 1)

    def test_draft_hidden_from_anonymous(self):
        draft = make_article(self.author, self.cat, status="draft",
                             title="Secret draft nobody sees")
        r = self.client.get(draft.get_absolute_url())
        self.assertEqual(r.status_code, 404)


class SubmissionWorkflowViewTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Clubs", icon="🎭")
        self.student = make_user("stu", CustomUserRole.STUDENT)
        self.faculty = make_user("fac", CustomUserRole.FACULTY)
        self.editor = make_user("ed", CustomUserRole.EDITOR)

    def article_payload(self, title="Students Organise Charity Show"):
        return {
            "title": title,
            "category": self.cat.pk,
            "excerpt": "Students at IUBAT organised a charity show for "
                       "a local community this week.",
            "content": "<p>The full story of the charity event.</p>",
            "action": "submit",
        }

    def test_anonymous_redirected_from_submit(self):
        r = self.client.get("/news/submit/")
        self.assertEqual(r.status_code, 302)
        self.assertIn("login", r.url)

    def test_student_submission_goes_pending(self):
        self.client.force_login(self.student)
        r = self.client.post("/news/submit/", self.article_payload())
        article = Article.objects.get(title="Students Organise Charity Show")
        self.assertEqual(article.status, "pending")
        self.assertEqual(article.author, self.student)

    def test_faculty_can_publish_immediately(self):
        self.client.force_login(self.faculty)
        payload = self.article_payload("Faculty Research Breakthrough")
        payload["action"] = "publish"
        self.client.post("/news/submit/", payload)
        article = Article.objects.get(
            title="Faculty Research Breakthrough"
        )
        self.assertEqual(article.status, "published")

    def test_student_cannot_edit_others_article(self):
        other = make_article(self.faculty, self.cat,
                             title="Faculty Owned Story Here")
        self.client.force_login(self.student)
        r = self.client.post(
            f"/news/article/{other.slug}/edit/",
            self.article_payload("Hijacked title attempt"),
        )
        # Non-author contributors get 404 (the object is hidden from their
        # queryset, so its existence is not leaked).
        self.assertEqual(r.status_code, 404)

    def test_editor_can_edit_any_article(self):
        article = make_article(self.faculty, self.cat,
                               title="Editable by editors too")
        self.client.force_login(self.editor)
        payload = self.article_payload("Editor revised headline")
        payload["action"] = "draft"
        r = self.client.post(f"/news/article/{article.slug}/edit/", payload)
        self.assertEqual(r.status_code, 302)
        article.refresh_from_db()
        self.assertEqual(article.title, "Editor revised headline")


class CommentReactionViewTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name="Events", icon="🎉")
        self.author = make_user("writer", CustomUserRole.FACULTY)
        self.article = make_article(self.author, self.cat,
                                    title="Commentable story")
        self.reader = make_user("reader", CustomUserRole.READER)

    def test_comment_requires_login(self):
        r = self.client.post(
            f"/news/article/{self.article.slug}/comment/",
            {"body": "Hello!"},
        )
        self.assertEqual(r.status_code, 302)

    def test_ajax_comment_returns_json(self):
        self.client.force_login(self.reader)
        r = self.client.post(
            f"/news/article/{self.article.slug}/comment/",
            {"body": "Nice reporting!"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        self.assertFalse(data["approved"])  # unverified reader → moderation
        self.assertIn("moderation", data["message"])

    def test_reaction_toggle(self):
        self.client.force_login(self.reader)
        url = f"/news/article/{self.article.slug}/react/"
        r = self.client.post(url, {"reaction_type": "like"})
        self.assertTrue(r.json()["success"])
        self.assertEqual(r.json()["counts"]["like"], 1)
        self.assertEqual(r.json()["user_reaction"], "like")
        # Same reaction toggles off.
        r2 = self.client.post(url, {"reaction_type": "like"})
        self.assertIsNone(r2.json()["user_reaction"])
        # Bad reaction type rejected.
        r3 = self.client.post(url, {"reaction_type": "nope"})
        self.assertEqual(r3.status_code, 400)
