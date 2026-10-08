import datetime

from rest_framework import serializers

from .models import Card
from .validators import CardValidationError, validate_and_mask


class CardSerializer(serializers.ModelSerializer):
    """Output-only shape — exactly what's safe to show the user."""

    class Meta:
        model = Card
        fields = ["id", "brand", "masked_number", "last4", "cardholder_name", "expiry_month", "expiry_year", "is_blocked", "created_at"]
        read_only_fields = fields


class CardCreateSerializer(serializers.Serializer):
    """
    Input-only shape. `card_number` and `cvv` are accepted here purely to
    validate the card and are never referenced again after `create()`
    returns — they're not model fields, so there's nothing to accidentally
    persist or log via serializer.data on this class.
    """

    card_number = serializers.CharField(write_only=True, max_length=25)
    cvv = serializers.CharField(write_only=True, min_length=3, max_length=4)
    cardholder_name = serializers.CharField(max_length=150)
    expiry_month = serializers.IntegerField(min_value=1, max_value=12)
    expiry_year = serializers.IntegerField(min_value=2000, max_value=2100)

    def validate(self, attrs):
        now = datetime.date.today()
        if (attrs["expiry_year"], attrs["expiry_month"]) < (now.year, now.month):
            raise serializers.ValidationError({"expiry_month": "Card has already expired."})

        try:
            masked = validate_and_mask(attrs["card_number"])
        except CardValidationError as exc:
            raise serializers.ValidationError({"card_number": str(exc)})

        attrs["_masked"] = masked
        return attrs

    def create(self, validated_data):
        masked = validated_data.pop("_masked")
        validated_data.pop("card_number", None)
        validated_data.pop("cvv", None)  # CVV is validated (length/format) and then discarded — never stored
        user = self.context["request"].user
        return Card.objects.create(
            user=user,
            brand=masked["brand"],
            masked_number=masked["masked_number"],
            last4=masked["last4"],
            cardholder_name=validated_data["cardholder_name"],
            expiry_month=validated_data["expiry_month"],
            expiry_year=validated_data["expiry_year"],
        )
