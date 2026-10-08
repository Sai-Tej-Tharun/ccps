from decimal import Decimal

from rest_framework import serializers

from cards.models import Card

MIN_CREDIT_LIMIT = Decimal("1.00")
MAX_CREDIT_LIMIT = Decimal("10000000.00")


class AdminCardSerializer(serializers.ModelSerializer):
    """
    Everything an admin may see about a card. Only the masked number is ever
    available - the full number and CVV are never stored (see cards/models.py).
    `transaction_count`, `total_spent` and `last_activity` are annotated onto
    the queryset by card_views.annotated_cards().
    """

    owner_id = serializers.IntegerField(source="user_id", read_only=True)
    owner_email = serializers.EmailField(source="user.email", read_only=True)
    owner_name = serializers.SerializerMethodField()
    transaction_count = serializers.IntegerField(read_only=True)
    total_spent = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    last_activity = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Card
        fields = [
            "id", "owner_id", "owner_email", "owner_name",
            "brand", "masked_number", "last4", "cardholder_name",
            "expiry_month", "expiry_year", "credit_limit",
            "is_blocked", "blocked_at", "created_at",
            "transaction_count", "total_spent", "last_activity",
        ]
        read_only_fields = fields

    def get_owner_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip()


class CreditLimitUpdateSerializer(serializers.Serializer):
    credit_limit = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=MIN_CREDIT_LIMIT,
        max_value=MAX_CREDIT_LIMIT,
    )