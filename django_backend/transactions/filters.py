import re

import django_filters

from .models import Transaction


class TransactionFilter(django_filters.FilterSet):
    """
    Supports, all combinable:
      ?status=SUCCESS
      ?date_from=2026-01-01&date_to=2026-01-31
      ?min_amount=10&max_amount=500
    """

    date_from = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    date_to = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")
    min_amount = django_filters.NumberFilter(field_name="amount", lookup_expr="gte")
    max_amount = django_filters.NumberFilter(field_name="amount", lookup_expr="lte")
    category = django_filters.ChoiceFilter(choices=Transaction.Category.choices)
    fraud_status = django_filters.ChoiceFilter(choices=Transaction.FraudStatus.choices)
    # Masked card number search: "4242", "**** 4242" and "**** **** **** 4242" all work.
    card = django_filters.CharFilter(method="filter_card")

    def filter_card(self, queryset, name, value):
        digits = re.sub(r"\D", "", value)[:19]  # only digits matter; the number is stored masked
        if not digits:
            return queryset.none()
        if len(digits) >= 4:
            return queryset.filter(card__last4=digits[-4:])
        return queryset.filter(card__last4__contains=digits)

    class Meta:
        model = Transaction
        fields = ["status", "date_from", "date_to", "min_amount", "max_amount", "category", "fraud_status", "card"]
