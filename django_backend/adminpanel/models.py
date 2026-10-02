from django.conf import settings
from django.db import models


class AdminActionLog(models.Model):
    """Audit trail of notable admin actions (e.g. CSV exports)."""

    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="admin_actions")
    action = models.CharField(max_length=255)
    details = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.admin_user} — {self.action} @ {self.created_at:%Y-%m-%d %H:%M}"
