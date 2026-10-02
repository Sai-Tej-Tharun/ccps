from rest_framework import serializers

from .models import AdminActionLog


class AdminActionLogSerializer(serializers.ModelSerializer):
    admin_email = serializers.EmailField(source="admin_user.email", read_only=True)

    class Meta:
        model = AdminActionLog
        fields = ["id", "admin_email", "action", "details", "created_at"]
        read_only_fields = fields
