from decimal import Decimal
from smtplib import SMTPException
from unittest import mock

from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework import status
from rest_framework.test import APITestCase

from cards.models import Card
from transactions.models import Transaction

from .models import AdminActionLog

User = get_user_model()


class AdminCardManagementTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin@example.com", email="admin@example.com", password="StrongPass123", is_staff=True
        )
        self.owner = User.objects.create_user(
            username="owner@example.com", email="owner@example.com", password="StrongPass123", first_name="Olive"
        )
        self.card = self._make_card(self.owner, "4242")
        self.other_card = self._make_card(self.owner, "1111")

    @staticmethod
    def _make_card(user, last4):
        return Card.objects.create(
            user=user, brand="VISA", masked_number=f"**** **** **** {last4}", last4=last4,
            cardholder_name="Olive Owner", expiry_month=12, expiry_year=2035, credit_limit=Decimal("5000.00"),
        )

    def _txn(self, card, amount, ref, txn_status=Transaction.Status.SUCCESS):
        return Transaction.objects.create(user=card.user, card=card, amount=Decimal(amount), status=txn_status, reference=ref)

    # ---- access control -------------------------------------------------
    def test_anonymous_is_rejected(self):
        self.assertEqual(self.client.get("/api/adminpanel/cards/").status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_is_forbidden_everywhere(self):
        self.client.force_authenticate(self.owner)
        cid = self.card.pk
        self.assertEqual(self.client.get("/api/adminpanel/cards/").status_code, 403)
        self.assertEqual(self.client.post(f"/api/adminpanel/cards/{cid}/block/").status_code, 403)
        self.assertEqual(self.client.post(f"/api/adminpanel/cards/{cid}/unblock/").status_code, 403)
        self.assertEqual(self.client.patch(f"/api/adminpanel/cards/{cid}/credit-limit/", {"credit_limit": "9"}).status_code, 403)
        self.assertEqual(self.client.get(f"/api/adminpanel/cards/{cid}/activity/").status_code, 403)
        self.card.refresh_from_db()
        self.assertFalse(self.card.is_blocked)

    # ---- viewing --------------------------------------------------------
    def test_admin_sees_all_cards_with_masked_numbers_and_activity(self):
        self._txn(self.card, "100.00", "r1")
        self._txn(self.card, "50.00", "r2")
        self._txn(self.card, "900.00", "r3", Transaction.Status.FAILED)
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/adminpanel/cards/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        row = next(r for r in response.data["results"] if r["id"] == self.card.pk)
        self.assertEqual(row["owner_email"], "owner@example.com")
        self.assertEqual(row["masked_number"], "**** **** **** 4242")
        self.assertEqual(row["transaction_count"], 3)
        self.assertEqual(Decimal(row["total_spent"]), Decimal("150.00"))
        self.assertNotIn("card_number", row)
        self.assertNotIn("cvv", row)

    def test_filter_by_status_and_search(self):
        self.card.is_blocked = True
        self.card.save()
        self.client.force_authenticate(self.admin)
        blocked = self.client.get("/api/adminpanel/cards/?status=blocked")
        self.assertEqual([r["id"] for r in blocked.data["results"]], [self.card.pk])
        active = self.client.get("/api/adminpanel/cards/?status=active")
        self.assertEqual([r["id"] for r in active.data["results"]], [self.other_card.pk])
        found = self.client.get("/api/adminpanel/cards/?search=1111")
        self.assertEqual([r["id"] for r in found.data["results"]], [self.other_card.pk])
        self.assertEqual(self.client.get("/api/adminpanel/cards/?status=bogus").status_code, 400)

    # ---- block / unblock --------------------------------------------------
    def test_block_card_logs_action_and_emails_owner(self):
        self.client.force_authenticate(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(f"/api/adminpanel/cards/{self.card.pk}/block/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["is_blocked"])
        self.card.refresh_from_db()
        self.assertTrue(self.card.is_blocked)
        self.assertIsNotNone(self.card.blocked_at)
        self.assertTrue(AdminActionLog.objects.filter(action="Blocked card", admin_user=self.admin).exists())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["owner@example.com"])
        self.assertIn("4242", mail.outbox[0].subject)
        self.assertNotIn("4111", mail.outbox[0].body)

    def test_block_twice_returns_conflict_and_sends_one_email(self):
        self.client.force_authenticate(self.admin)
        with self.captureOnCommitCallbacks(execute=True):
            self.client.post(f"/api/adminpanel/cards/{self.card.pk}/block/")
            again = self.client.post(f"/api/adminpanel/cards/{self.card.pk}/block/")
        self.assertEqual(again.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(len(mail.outbox), 1)

    def test_unblock_card(self):
        self.card.is_blocked = True
        self.card.save()
        self.client.force_authenticate(self.admin)
        response = self.client.post(f"/api/adminpanel/cards/{self.card.pk}/unblock/")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["is_blocked"])
        self.assertTrue(AdminActionLog.objects.filter(action="Unblocked card").exists())
        self.assertEqual(self.client.post(f"/api/adminpanel/cards/{self.card.pk}/unblock/").status_code, 409)

    def test_mail_failure_does_not_break_blocking(self):
        self.client.force_authenticate(self.admin)
        with mock.patch("cards.emails.send_mail", side_effect=SMTPException("boom")):
            with self.captureOnCommitCallbacks(execute=True):
                response = self.client.post(f"/api/adminpanel/cards/{self.card.pk}/block/")
        self.assertEqual(response.status_code, 200)
        self.card.refresh_from_db()
        self.assertTrue(self.card.is_blocked)

    def test_unknown_card_404(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post("/api/adminpanel/cards/99999/block/").status_code, 404)

    # ---- credit limit -------------------------------------------------------
    def test_update_credit_limit(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(f"/api/adminpanel/cards/{self.card.pk}/credit-limit/", {"credit_limit": "7500.50"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.card.refresh_from_db()
        self.assertEqual(self.card.credit_limit, Decimal("7500.50"))
        log = AdminActionLog.objects.get(action="Updated card credit limit")
        self.assertIn("old=5000.00", log.details)
        self.assertIn("new=7500.50", log.details)

    def test_credit_limit_validation(self):
        self.client.force_authenticate(self.admin)
        url = f"/api/adminpanel/cards/{self.card.pk}/credit-limit/"
        for bad in ["0", "-5", "abc", "", "10000000.01", "12.345", "NaN", "Infinity"]:
            response = self.client.patch(url, {"credit_limit": bad}, format="json")
            self.assertEqual(response.status_code, 400, msg=bad)
        self.assertEqual(self.client.patch(url, {}, format="json").status_code, 400)
        self.card.refresh_from_db()
        self.assertEqual(self.card.credit_limit, Decimal("5000.00"))

    # ---- activity -----------------------------------------------------------
    def test_activity_only_lists_that_cards_transactions(self):
        self._txn(self.card, "10.00", "a1")
        self._txn(self.other_card, "20.00", "b1")
        self.client.force_authenticate(self.admin)
        response = self.client.get(f"/api/adminpanel/cards/{self.card.pk}/activity/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([r["reference"] for r in response.data["results"]], ["a1"])