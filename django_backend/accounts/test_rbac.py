from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from adminpanel.models import AdminActionLog
from cards.models import Card
from transactions.models import Transaction

from .models import UserRole
from .rbac import ROLE_PERMISSIONS, Perm, Role, get_role, has_permission

User = get_user_model()


def make_user(email, role=None, **extra):
    user = User.objects.create_user(username=email, email=email, password="StrongPass123", **extra)
    if role:
        UserRole.objects.create(user=user, role=role)
        user.refresh_from_db()
    return user


class RoleMatrixTests(APITestCase):
    def test_roles_get_expected_permissions(self):
        admin, support, read_only = (ROLE_PERMISSIONS[r] for r in (Role.ADMIN, Role.SUPPORT, Role.READ_ONLY))
        self.assertIn(Perm.CARDS_UPDATE_LIMIT, admin)
        self.assertIn(Perm.CARDS_BLOCK, support)
        self.assertNotIn(Perm.CARDS_UPDATE_LIMIT, support)
        self.assertNotIn(Perm.AUDIT_VIEW, support)
        self.assertNotIn(Perm.CARDS_BLOCK, read_only)
        self.assertNotIn(Perm.TRANSACTIONS_EXPORT, read_only)
        self.assertIn(Perm.ANALYTICS_VIEW, read_only)

    def test_assigning_a_role_makes_the_user_staff_and_removing_it_reverts(self):
        user = make_user("a@example.com")
        self.assertFalse(user.is_staff)
        role = UserRole.objects.create(user=user, role=Role.SUPPORT)
        user.refresh_from_db()
        self.assertTrue(user.is_staff)
        role.delete()
        user.refresh_from_db()
        self.assertFalse(user.is_staff)

    def test_legacy_staff_without_role_is_admin_and_customer_has_none(self):
        self.assertEqual(get_role(make_user("s@example.com", is_staff=True)), Role.ADMIN)
        customer = make_user("c@example.com")
        self.assertIsNone(get_role(customer))
        self.assertFalse(has_permission(customer, Perm.CARDS_VIEW))

    def test_me_endpoint_reports_role_and_permissions(self):
        self.client.force_authenticate(make_user("r@example.com", Role.READ_ONLY))
        data = self.client.get("/api/auth/me/").data
        self.assertEqual(data["role"], "READ_ONLY")
        self.assertIn("cards.view", data["permissions"])
        self.assertNotIn("cards.block", data["permissions"])


class ApiRoleChecksTests(APITestCase):
    def setUp(self):
        self.customer = make_user("customer@example.com")
        self.admin = make_user("admin@example.com", Role.ADMIN)
        self.support = make_user("support@example.com", Role.SUPPORT)
        self.read_only = make_user("readonly@example.com", Role.READ_ONLY)
        self.card = Card.objects.create(
            user=self.customer, brand="VISA", masked_number="**** **** **** 4242", last4="4242",
            cardholder_name="Cus Tomer", expiry_month=12, expiry_year=2035,
        )
        Transaction.objects.create(user=self.customer, card=self.card, amount="10.00", status="SUCCESS", reference="t-1")

    def call(self, user, method, url, **kwargs):
        self.client.force_authenticate(user)
        return getattr(self.client, method)(url, **kwargs)

    def test_card_list_needs_cards_view(self):
        self.assertEqual(self.call(self.customer, "get", "/api/adminpanel/cards/").status_code, 403)
        for user in (self.read_only, self.support, self.admin):
            self.assertEqual(self.call(user, "get", "/api/adminpanel/cards/").status_code, 200)

    def test_block_and_unblock_allowed_for_admin_and_support_only(self):
        url = f"/api/adminpanel/cards/{self.card.id}/block/"
        self.assertEqual(self.call(self.read_only, "post", url).status_code, 403)
        self.assertEqual(self.call(self.customer, "post", url).status_code, 403)
        self.assertEqual(self.call(self.support, "post", url).status_code, 200)
        self.assertEqual(self.call(self.admin, "post", f"/api/adminpanel/cards/{self.card.id}/unblock/").status_code, 200)

    def test_credit_limit_is_admin_only(self):
        url = f"/api/adminpanel/cards/{self.card.id}/credit-limit/"
        body = {"credit_limit": "7500.00"}
        self.assertEqual(self.call(self.support, "patch", url, data=body, format="json").status_code, 403)
        self.assertEqual(self.call(self.read_only, "patch", url, data=body, format="json").status_code, 403)
        self.assertEqual(self.call(self.admin, "patch", url, data=body, format="json").status_code, 200)

    def test_audit_log_endpoint_is_admin_only(self):
        self.assertEqual(self.call(self.support, "get", "/api/adminpanel/logs/").status_code, 403)
        self.assertEqual(self.call(self.admin, "get", "/api/adminpanel/logs/").status_code, 200)

    def test_transaction_export_needs_export_permission(self):
        self.assertEqual(self.call(self.customer, "get", "/api/transactions/export/").status_code, 403)
        self.assertEqual(self.call(self.read_only, "get", "/api/transactions/export/").status_code, 403)
        self.assertEqual(self.call(self.support, "get", "/api/transactions/export/").status_code, 200)

    def test_daily_summary_needs_analytics_view(self):
        self.assertEqual(self.call(self.customer, "get", "/api/adminpanel/daily-summary/").status_code, 403)
        self.assertEqual(self.call(self.read_only, "get", "/api/adminpanel/daily-summary/").status_code, 200)

    def test_transaction_list_scope_follows_role(self):
        other = make_user("other@example.com")
        Transaction.objects.create(user=other, amount="5.00", status="SUCCESS", reference="t-2")
        self.assertEqual(self.call(self.customer, "get", "/api/transactions/").data["count"], 1)
        self.assertEqual(self.call(self.read_only, "get", "/api/transactions/").data["count"], 2)

    def test_unauthenticated_requests_are_rejected(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/adminpanel/cards/").status_code, 401)


class AuditLogSchemaTests(APITestCase):
    def test_block_and_limit_changes_are_recorded_with_who_what_where(self):
        admin = make_user("admin@example.com", Role.ADMIN)
        owner = make_user("owner@example.com")
        card = Card.objects.create(
            user=owner, brand="VISA", masked_number="**** **** **** 4242", last4="4242",
            cardholder_name="O", expiry_month=12, expiry_year=2035,
        )
        self.client.force_authenticate(admin)
        self.client.post(f"/api/adminpanel/cards/{card.id}/block/")
        self.client.patch(f"/api/adminpanel/cards/{card.id}/credit-limit/", {"credit_limit": "9000.00"}, format="json")

        blocked = AdminActionLog.objects.get(action="Blocked card")
        self.assertEqual((blocked.role, blocked.target_type, blocked.target_id), ("ADMIN", "card", str(card.id)))
        self.assertEqual(blocked.changes, {"is_blocked": {"old": False, "new": True}})
        self.assertEqual(blocked.admin_user, admin)
        self.assertTrue(blocked.ip_address)
        limit = AdminActionLog.objects.get(action="Updated card credit limit")
        self.assertEqual(limit.changes["credit_limit"]["new"], "9000.00")


class RoleAdministrationTests(APITestCase):
    def setUp(self):
        self.admin = make_user("admin@example.com", Role.ADMIN)
        self.target = make_user("target@example.com")

    def put(self, user, pk, role):
        self.client.force_authenticate(user)
        return self.client.put(f"/api/adminpanel/users/{pk}/role/", {"role": role}, format="json")

    def test_admin_can_assign_and_remove_roles_and_it_is_audited(self):
        response = self.put(self.admin, self.target.pk, "SUPPORT")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["role"], "SUPPORT")
        self.assertEqual(self.put(self.admin, self.target.pk, "NONE").data["role"], None)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_staff)
        self.assertEqual(AdminActionLog.objects.filter(action="Changed user role").count(), 2)

    def test_removing_role_from_legacy_staff_revokes_access(self):
        legacy = make_user("legacy@example.com", is_staff=True)
        self.put(self.admin, legacy.pk, "NONE")
        legacy.refresh_from_db()
        self.assertIsNone(get_role(legacy))

    def test_validation_and_protection(self):
        self.assertEqual(self.put(self.admin, self.target.pk, "ROOT").status_code, 400)
        self.assertEqual(self.put(self.admin, self.admin.pk, "READ_ONLY").status_code, 400)  # no self-demotion
        self.assertEqual(self.put(self.admin, 99999, "SUPPORT").status_code, 404)

    def test_only_admins_manage_roles(self):
        support = make_user("support@example.com", Role.SUPPORT)
        self.assertEqual(self.put(support, self.target.pk, "ADMIN").status_code, 403)
        self.client.force_authenticate(support)
        self.assertEqual(self.client.get("/api/adminpanel/roles/").status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get("/api/adminpanel/roles/").status_code, 200)
        staff = self.client.get("/api/adminpanel/staff-users/").data["results"]
        self.assertEqual(sorted(u["email"] for u in staff), ["admin@example.com", "support@example.com"])

    def test_user_search_covers_customers_only_with_three_characters(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get("/api/adminpanel/staff-users/?all=true&search=ta").data["count"], 0)
        found = self.client.get("/api/adminpanel/staff-users/?all=true&search=targ").data["results"]
        self.assertEqual([u["email"] for u in found], ["target@example.com"])


class LoginByEmailTests(APITestCase):
    def test_user_whose_username_differs_from_email_can_log_in_with_email(self):
        User.objects.create_superuser(username="admin", email="admin@example.com", password="StrongPass123!")
        response = self.client.post("/api/auth/login/", {"email": "Admin@Example.com", "password": "StrongPass123!"}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_wrong_password_and_unknown_email_are_rejected(self):
        make_user("a@example.com")
        self.assertEqual(self.client.post("/api/auth/login/", {"email": "a@example.com", "password": "nope"}, format="json").status_code, 401)
        self.assertEqual(self.client.post("/api/auth/login/", {"email": "ghost@example.com", "password": "x"}, format="json").status_code, 401)