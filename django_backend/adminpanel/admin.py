from django.contrib import admin

from .models import AdminActionLog


@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    list_display = ("id", "admin_user", "action", "created_at")
    readonly_fields = ("admin_user", "action", "details", "created_at")

    def has_add_permission(self, request):
        return False
