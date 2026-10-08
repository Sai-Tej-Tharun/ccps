from django.conf import settings
from django.db import models


class Card(models.Model):
    """
    Deliberately has NO field for the full card number or CVV anywhere in
    this schema — those never exist past the request that adds the card
    (see serializers.py / validators.py). Only what's needed to display
    and reference a saved card is stored.
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cards")
    brand = models.CharField(max_length=20)  # VISA / MASTERCARD / AMEX / DISCOVER / CARD
    masked_number = models.CharField(max_length=32)  # e.g. "**** **** **** 1234"
    last4 = models.CharField(max_length=4)
    cardholder_name = models.CharField(max_length=150)
    expiry_month = models.PositiveSmallIntegerField()
    expiry_year = models.PositiveSmallIntegerField()
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=5000)
    is_blocked = models.BooleanField(default=False, db_index=True)
    blocked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.brand} ending in {self.last4} ({self.user})"
