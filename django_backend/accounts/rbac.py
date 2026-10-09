"""
Role-based access control.

Roles    : ADMIN, SUPPORT, READ_ONLY (staff) - customers have no role.
Rule     : a permission is granted only if the user's role lists it below.
Backward compatibility: a staff/superuser account that has no UserRole row is
treated as ADMIN, so accounts created before RBAC keep working.
"""


class Role:
    ADMIN = "ADMIN"
    SUPPORT = "SUPPORT"
    READ_ONLY = "READ_ONLY"
    ALL = (ADMIN, SUPPORT, READ_ONLY)


class Perm:
    CARDS_VIEW = "cards.view"
    CARDS_BLOCK = "cards.block"
    CARDS_UPDATE_LIMIT = "cards.update_limit"
    TRANSACTIONS_VIEW_ALL = "transactions.view_all"
    TRANSACTIONS_EXPORT = "transactions.export"
    ANALYTICS_VIEW = "analytics.view"
    ANALYTICS_EXPORT = "analytics.export"
    FRAUD_VIEW = "fraud.view"
    FRAUD_REVIEW = "fraud.review"
    AUDIT_VIEW = "audit.view"
    MONITORING_VIEW = "monitoring.view"
    ROLES_MANAGE = "roles.manage"


ALL_PERMISSIONS = frozenset(v for k, v in vars(Perm).items() if not k.startswith("_"))

ROLE_PERMISSIONS = {
    Role.ADMIN: ALL_PERMISSIONS,
    Role.SUPPORT: frozenset({
        Perm.CARDS_VIEW, Perm.CARDS_BLOCK,
        Perm.TRANSACTIONS_VIEW_ALL, Perm.TRANSACTIONS_EXPORT,
        Perm.ANALYTICS_VIEW, Perm.ANALYTICS_EXPORT,
        Perm.FRAUD_VIEW, Perm.FRAUD_REVIEW,
        Perm.MONITORING_VIEW,
    }),
    Role.READ_ONLY: frozenset({
        Perm.CARDS_VIEW,
        Perm.TRANSACTIONS_VIEW_ALL,
        Perm.ANALYTICS_VIEW, Perm.ANALYTICS_EXPORT,
        Perm.FRAUD_VIEW,
        Perm.MONITORING_VIEW,
    }),
}


def get_role(user):
    """The user's role name, or None for customers and anonymous users."""
    if user is None or not getattr(user, "is_authenticated", False) or not user.is_active:
        return None
    if user.is_superuser:
        return Role.ADMIN
    from .models import UserRole  # imported here to avoid an app-loading cycle

    assigned = UserRole.objects.filter(user_id=user.pk).values_list("role", flat=True).first()
    if assigned:
        return assigned
    return Role.ADMIN if user.is_staff else None  # legacy staff account


def permissions_for(user):
    return ROLE_PERMISSIONS.get(get_role(user), frozenset())


def has_permission(user, permission):
    return permission in permissions_for(user)