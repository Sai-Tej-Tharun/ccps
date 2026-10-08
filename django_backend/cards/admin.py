from django.contrib import admin

from .models import Card


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "brand", "masked_number", "cardholder_name", "expiry_month", "expiry_year", "created_at")
    list_filter = ("brand", "is_blocked")
    search_fields = ("user__email", "cardholder_name", "last4")
    readonly_fields = ("brand", "masked_number", "last4", "cardholder_name", "expiry_month", "expiry_year", "created_at", "user", "is_blocked", "blocked_at")

    def has_add_permission(self, request):
        return False  # cards are only created through the API's validation/masking pipeline
