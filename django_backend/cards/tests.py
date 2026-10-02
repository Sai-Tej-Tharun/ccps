from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Card
from .validators import luhn_is_valid, mask_card_number, validate_and_mask

User = get_user_model()

VALID_VISA = "4111111111111111"  # well-known Luhn-valid test number
INVALID_NUMBER = "4111111111111112"


class ValidatorTests(APITestCase):
    def test_luhn_valid_number_passes(self):
        self.assertTrue(luhn_is_valid(VALID_VISA))

    def test_luhn_invalid_number_fails(self):
        self.assertFalse(luhn_is_valid(INVALID_NUMBER))

    def test_masking_only_reveals_last_four(self):
        masked = mask_card_number(VALID_VISA)
        self.assertTrue(masked.endswith("1111"))
        self.assertNotIn(VALID_VISA[:12], masked)

    def test_validate_and_mask_detects_visa(self):
        result = validate_and_mask(VALID_VISA)
        self.assertEqual(result["brand"], "VISA")
        self.assertEqual(result["last4"], "1111")


class CardAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="a@example.com", email="a@example.com", password="StrongPass123")
        self.other_user = User.objects.create_user(username="b@example.com", email="b@example.com", password="StrongPass123")
        login = self.client.post("/api/auth/login/", {"email": "a@example.com", "password": "StrongPass123"}, format="json")
        self.access = login.data["access"]
        self.auth_header = {"HTTP_AUTHORIZATION": f"Bearer {self.access}"}

    def test_add_card_requires_authentication(self):
        response = self.client.post("/api/cards/", {"card_number": VALID_VISA})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_add_card_success_never_stores_raw_number_or_cvv(self):
        response = self.client.post(
            "/api/cards/",
            {
                "card_number": VALID_VISA,
                "cvv": "123",
                "cardholder_name": "Jane Doe",
                "expiry_month": 12,
                "expiry_year": 2030,
            },
            format="json",
            **self.auth_header,
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("card_number", response.data)
        self.assertNotIn("cvv", response.data)
        self.assertEqual(response.data["last4"], "1111")

        card = Card.objects.get(user=self.user)
        self.assertEqual(card.masked_number.count("*"), 12)
        # The raw number/cvv were never model fields, so there is nothing
        # on the row that could hold them — this asserts the schema itself.
        self.assertFalse(hasattr(card, "card_number"))
        self.assertFalse(hasattr(card, "cvv"))

    def test_add_card_with_invalid_number_rejected(self):
        response = self.client.post(
            "/api/cards/",
            {
                "card_number": INVALID_NUMBER,
                "cvv": "123",
                "cardholder_name": "Jane Doe",
                "expiry_month": 12,
                "expiry_year": 2030,
            },
            format="json",
            **self.auth_header,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_card_with_expired_date_rejected(self):
        response = self.client.post(
            "/api/cards/",
            {
                "card_number": VALID_VISA,
                "cvv": "123",
                "cardholder_name": "Jane Doe",
                "expiry_month": 1,
                "expiry_year": 2000,
            },
            format="json",
            **self.auth_header,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_cards_only_returns_own_cards(self):
        Card.objects.create(
            user=self.user, brand="VISA", masked_number="**** **** **** 1111",
            last4="1111", cardholder_name="Jane", expiry_month=12, expiry_year=2030,
        )
        Card.objects.create(
            user=self.other_user, brand="VISA", masked_number="**** **** **** 2222",
            last4="2222", cardholder_name="Bob", expiry_month=12, expiry_year=2030,
        )
        response = self.client.get("/api/cards/", **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["last4"], "1111")

    def test_cannot_delete_another_users_card(self):
        other_card = Card.objects.create(
            user=self.other_user, brand="VISA", masked_number="**** **** **** 2222",
            last4="2222", cardholder_name="Bob", expiry_month=12, expiry_year=2030,
        )
        response = self.client.delete(f"/api/cards/{other_card.id}/", **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Card.objects.filter(id=other_card.id).exists())

    def test_can_delete_own_card(self):
        own_card = Card.objects.create(
            user=self.user, brand="VISA", masked_number="**** **** **** 1111",
            last4="1111", cardholder_name="Jane", expiry_month=12, expiry_year=2030,
        )
        response = self.client.delete(f"/api/cards/{own_card.id}/", **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Card.objects.filter(id=own_card.id).exists())
