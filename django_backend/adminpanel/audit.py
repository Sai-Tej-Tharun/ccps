"""One place that writes the admin audit trail (who did what, to which record, from where)."""

from accounts.rbac import get_role

from .models import AdminActionLog


def client_ip(request):
    return (request.META.get("REMOTE_ADDR") or "")[:45] or None


def log_admin_action(request, action, target_type="", target_id="", changes=None, details=""):
    """
    action      short label, e.g. "Blocked card"
    target_type "card", "user", "fraud_log" ...
    target_id   primary key of the record that was changed
    changes     {"credit_limit": {"old": "5000.00", "new": "7500.00"}}
    """
    return AdminActionLog.objects.create(
        admin_user=request.user,
        role=get_role(request.user) or "",
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        changes=changes or {},
        details=details,
        ip_address=client_ip(request),
    )