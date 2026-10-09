from django.utils import timezone
from rest_framework import serializers

from accounts.rbac import Perm, has_permission

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    card_last4 = serializers.CharField(source="card.last4", default=None, read_only=True)
    card_brand = serializers.CharField(source="card.brand", default=None, read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id", "reference", "user_email", "card_last4", "card_brand",
            "amount", "currency", "status", "failure_reason", "category", "fraud_status",
            "created_at", "updated_at",
        ]
        read_only_fields = fields

    def _can_see_fraud_status(self):
        request = self.context.get("request")
        if request is None:
            return False
        if not hasattr(request, "_can_see_fraud"):  # one role lookup per request, not per row
            request._can_see_fraud = has_permission(request.user, Perm.FRAUD_VIEW)
        return request._can_see_fraud

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Customers never see the fraud flag: it would tell a fraudster which rule caught them.
        if not self._can_see_fraud_status():
            data.pop("fraud_status", None)
        return data
class StatementQuerySerializer(serializers.Serializer):
    """Validates ?year=&month= for the statement download. Both omitted = current month."""

    year = serializers.IntegerField(min_value=2000, max_value=2100, required=False)
    month = serializers.IntegerField(min_value=1, max_value=12, required=False)

    def validate(self, attrs):
        if ("year" in attrs) != ("month" in attrs):
            raise serializers.ValidationError("Provide both 'year' and 'month', or neither for the current month.")
        now = timezone.now()
        year = attrs.get("year", now.year)
        month = attrs.get("month", now.month)
        if (year, month) > (now.year, now.month):
            raise serializers.ValidationError("A statement cannot be generated for a future month.")
        return {"year": year, "month": month}