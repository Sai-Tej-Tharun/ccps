from django.contrib import admin

from .models import UserRole


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    """Assign Admin / Support / Read-Only here (or with: python manage.py assign_role <email> <ROLE>)."""

    list_display = ("user", "role", "assigned_by", "updated_at")
    list_filter = ("role",)
    search_fields = ("user__email",)
    raw_id_fields = ("user", "assigned_by")

    def save_model(self, request, obj, form, change):
        obj.assigned_by = request.user
        super().save_model(request, obj, form, change)