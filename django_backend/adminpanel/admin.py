from django.contrib import admin

from .models import AdminActionLog, FraudLog, RequestLog


@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    list_display = ("id", "admin_user", "role", "action", "target_type", "target_id", "created_at")
    list_filter = ("role", "action")
    readonly_fields = ("admin_user", "role", "action", "target_type", "target_id", "changes", "details", "ip_address", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False  # an audit trail is append-only


@admin.register(FraudLog)
class FraudLogAdmin(admin.ModelAdmin):
    list_display = ("id", "rule", "severity", "user", "transaction", "reviewed", "created_at")
    list_filter = ("rule", "reviewed")
    readonly_fields = ("transaction", "user", "card", "rule", "severity", "details", "ip_address", "device_hash", "created_at")


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "service", "method", "path", "status_code", "duration_ms")
    list_filter = ("service", "status_code")

    def has_add_permission(self, request):
        return False
