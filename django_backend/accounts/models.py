from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


class UserRole(models.Model):
    """
    Staff role of a user. Customers have NO row here.

    A user with a role is always staff (is_staff=True) so the frontend and the
    Django admin site treat them as back-office users; what they may actually DO
    is decided by accounts/rbac.py, never by is_staff alone.
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        SUPPORT = "SUPPORT", "Support"
        READ_ONLY = "READ_ONLY", "Read-Only"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="role_assignment")
    role = models.CharField(max_length=20, choices=Role.choices)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="roles_assigned"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user_id"]

    def __str__(self):
        return f"{self.user} - {self.get_role_display()}"


@receiver(post_save, sender=UserRole)
def _grant_staff_flag(sender, instance, **kwargs):
    type(instance.user)._default_manager.filter(pk=instance.user_id, is_staff=False).update(is_staff=True)


@receiver(post_delete, sender=UserRole)
def _revoke_staff_flag(sender, instance, **kwargs):
    # Superusers keep access; everyone else goes back to being a plain customer.
    type(instance.user)._default_manager.filter(pk=instance.user_id, is_superuser=False).update(is_staff=False)