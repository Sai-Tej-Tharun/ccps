from rest_framework.permissions import BasePermission

from .rbac import has_permission


def require(*permissions):
    """
    DRF permission class factory:  permission_classes = [require(Perm.CARDS_BLOCK)]
    The user must be logged in and hold EVERY listed permission. The check runs on
    the server for every request, so hiding a button in the UI is never the only guard.
    """

    class _HasPermissions(BasePermission):
        message = "Your role does not allow this action."

        def has_permission(self, request, view):
            user = request.user
            return bool(
                user and user.is_authenticated and all(has_permission(user, p) for p in permissions)
            )

    _HasPermissions.__name__ = "Requires_" + "_".join(p.replace(".", "_") for p in permissions)
    return _HasPermissions