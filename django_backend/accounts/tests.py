from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class CreateDemoAdminCommandTests(TestCase):
    def test_command_creates_superuser(self):
        call_command("create_demo_admin")
        admin = User.objects.get(username="admin")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_command_is_idempotent(self):
        call_command("create_demo_admin")
        call_command("create_demo_admin")
        self.assertEqual(User.objects.filter(username="admin").count(), 1)


class RegistrationTests(APITestCase):
    def test_register_success(self):
        response = self.client.post(
            "/api/auth/register/",
            {"email": "jane@example.com", "password": "StrongPass123", "first_name": "Jane", "last_name": "Doe"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="jane@example.com").exists())
        user = User.objects.get(email="jane@example.com")
        # Password must never be stored in plain text.
        self.assertNotEqual(user.password, "StrongPass123")
        self.assertTrue(user.password.startswith("pbkdf2_"))

    def test_register_duplicate_email_rejected(self):
        self.client.post(
            "/api/auth/register/",
            {"email": "dupe@example.com", "password": "StrongPass123", "first_name": "A"},
            format="json",
        )
        response = self.client.post(
            "/api/auth/register/",
            {"email": "dupe@example.com", "password": "AnotherPass123", "first_name": "B"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password_rejected(self):
        response = self.client.post(
            "/api/auth/register/",
            {"email": "weak@example.com", "password": "123", "first_name": "Weak"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="login@example.com", email="login@example.com", password="StrongPass123"
        )

    def test_login_success_returns_tokens(self):
        response = self.client.post(
            "/api/auth/login/", {"email": "login@example.com", "password": "StrongPass123"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password_rejected(self):
        response = self.client.post(
            "/api/auth/login/", {"email": "login@example.com", "password": "WrongPassword"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_unknown_email_rejected(self):
        response = self.client.post(
            "/api/auth/login/", {"email": "nobody@example.com", "password": "whatever"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProtectedRouteTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="me@example.com", email="me@example.com", password="StrongPass123"
        )

    def test_me_requires_authentication(self):
        response = self.client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_profile_when_authenticated(self):
        login = self.client.post(
            "/api/auth/login/", {"email": "me@example.com", "password": "StrongPass123"}, format="json"
        )
        access = login.data["access"]
        response = self.client.get("/api/auth/me/", HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "me@example.com")


class LogoutTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="out@example.com", email="out@example.com", password="StrongPass123"
        )
        login = self.client.post(
            "/api/auth/login/", {"email": "out@example.com", "password": "StrongPass123"}, format="json"
        )
        self.access = login.data["access"]
        self.refresh = login.data["refresh"]

    def test_logout_blacklists_refresh_token(self):
        response = self.client.post(
            "/api/auth/logout/",
            {"refresh": self.refresh},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {self.access}",
        )
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        # The same refresh token can no longer mint a new access token.
        refresh_attempt = self.client.post("/api/auth/refresh/", {"refresh": self.refresh}, format="json")
        self.assertEqual(refresh_attempt.status_code, status.HTTP_401_UNAUTHORIZED)
