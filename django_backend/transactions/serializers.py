from django.utils import timezone
from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    card_last4 = serializers.CharField(source="card.last4", default=None, read_only=True)
    card_brand = serializers.CharField(source="card.brand", default=None, read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id", "reference", "user_email", "card_last4", "card_brand",
            "amount", "currency", "status", "failure_reason",
            "created_at", "updated_at",
        ]
        read_only_fields = fields
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