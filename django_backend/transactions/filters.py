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

    class Meta:
        model = Transaction
        fields = ["status", "date_from", "date_to", "min_amount", "max_amount"]
