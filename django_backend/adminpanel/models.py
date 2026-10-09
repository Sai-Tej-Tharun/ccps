from django.conf import settings
from django.db import models
from django.utils import timezone


class AdminActionLog(models.Model):
    """Audit trail of notable admin actions (e.g. CSV exports)."""

    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin_actions")
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True, default="")
    # Audit-trail schema: who (role), what (action), on which record, old -> new values, from where.
    role = models.CharField(max_length=20, blank=True, default="")
    target_type = models.CharField(max_length=40, blank=True, default="")
    target_id = models.CharField(max_length=40, blank=True, default="")
    changes = models.JSONField(blank=True, default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.admin_user} — {self.action} @ {self.created_at:%Y-%m-%d %H:%M}"
class FraudLog(models.Model):
    """
    One row per fraud rule a transaction tripped. Written by the FastAPI payment
    service (fastapi_backend/fraud.py, which mirrors this table) and reviewed by
    staff through /api/adminpanel/fraud-logs/.
    """

    class Rule(models.TextChoices):
        HIGH_VALUE_BURST = "HIGH_VALUE_BURST", "Multiple high-value transactions in a short time"
        MULTI_SOURCE = "MULTI_SOURCE", "Rapid transactions from different devices or locations"

    class Resolution(models.TextChoices):
        CONFIRMED_FRAUD = "CONFIRMED_FRAUD", "Confirmed fraud"
        FALSE_POSITIVE = "FALSE_POSITIVE", "False positive"

    transaction = models.ForeignKey("transactions.Transaction", on_delete=models.CASCADE, related_name="fraud_logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="fraud_logs")
    card = models.ForeignKey("cards.Card", null=True, blank=True, on_delete=models.SET_NULL, related_name="fraud_logs")
    rule = models.CharField(max_length=30, choices=Rule.choices)
    severity = models.CharField(max_length=10, default="MEDIUM")
    details = models.TextField(blank=True, default="")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_hash = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    reviewed = models.BooleanField(default=False, db_index=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="fraud_reviews"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    resolution = models.CharField(max_length=20, blank=True, default="", choices=Resolution.choices)
    review_note = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.rule} on transaction {self.transaction_id}"

class RequestLog(models.Model):
    """API response-time and failure log, written by both services (see monitoring.py in each)."""

    service = models.CharField(max_length=10)  # "django" or "fastapi"
    method = models.CharField(max_length=8)
    path = models.CharField(max_length=200)  # the route pattern, so /cards/7/ and /cards/8/ group together
    status_code = models.PositiveSmallIntegerField()
    duration_ms = models.PositiveIntegerField()
    error = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["service", "created_at"])]

    def __str__(self):
        return f"{self.method} {self.path} {self.status_code} {self.duration_ms}ms"