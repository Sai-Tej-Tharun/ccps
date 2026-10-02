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
