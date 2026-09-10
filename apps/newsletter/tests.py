"""Tests for newsletter subscription and campaign sending."""

from django.core import mail
from django.test import TestCase

from apps.accounts.models import CustomUser
from apps.accounts.roles import CustomUserRole

from .models import NewsletterEmail, Subscriber


class SubscribeTests(TestCase):
    def test_subscribe_creates_subscriber(self):
        r = self.client.post(
            "/newsletter/subscribe/",
            {"email": "NewFan@Example.com"},
        )
        self.assertEqual(r.status_code, 302)
        sub = Subscriber.objects.get(email="newfan@example.com")
        self.assertTrue(sub.is_active)
        self.assertIsNotNone(sub.token)

    def test_ajax_subscribe_returns_json(self):
        r = self.client.post(
            "/newsletter/subscribe/",
            {"email": "ajax@example.com"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["success"])

    def test_resubscribe_reactivates(self):
        sub = Subscriber.objects.create(
            email="gone@example.com", is_active=False
        )
        self.client.post("/newsletter/subscribe/",
                         {"email": "gone@example.com"})
        sub.refresh_from_db()
        self.assertTrue(sub.is_active)

    def test_unsubscribe_token(self):
        sub = Subscriber.objects.create(email="bye@example.com")
        r = self.client.get(
            f"/newsletter/unsubscribe/{sub.token}/")
        self.assertEqual(r.status_code, 200)
        sub.refresh_from_db()
        self.assertFalse(sub.is_active)
        self.assertIsNotNone(sub.unsubscribed_at)

    def test_invalid_email_rejected(self):
        r = self.client.post("/newsletter/subscribe/",
                             {"email": "not-an-email"},
                             HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(r.status_code, 400)


class CampaignSendTests(TestCase):
    def test_send_bccs_active_subscribers(self):
        Subscriber.objects.create(email="a@example.com")
        Subscriber.objects.create(email="b@example.com")
        Subscriber.objects.create(email="inactive@example.com",
                                  is_active=False)
        editor = CustomUser.objects.create_user(
            "ed", "ed@iubat.edu", "pass12345",
            role=CustomUserRole.EDITOR,
        )
        campaign = NewsletterEmail.objects.create(
            subject="Weekly roundup",
            body="<h1>This week at IUBAT</h1><p>Great stories.</p>",
        )
        with self.settings(
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"
        ):
            count = campaign.send(user=editor)
        self.assertEqual(count, 2)
        self.assertEqual(campaign.status, "sent")
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("b@example.com", mail.outbox[0].bcc)
