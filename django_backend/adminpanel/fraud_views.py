"""    for alert in build_payment_alerts(db, current_user, card, txn):
        background_tasks.add_task(send_email, alert)

    # Fraud rules: flags the transaction, writes the fraud log, returns the alert e-mails.
    for alert in evaluate_and_record(db, current_user, card, txn):
        background_tasks.add_task(send_email, alert)
Fraud review (staff).

GET  /api/adminpanel/fraud-logs/                  ?reviewed=true|false  ?rule=HIGH_VALUE_BURST|MULTI_SOURCE
POST /api/adminpanel/fraud-logs/<id>/review/      body {"resolution": "CONFIRMED_FRAUD" | "FALSE_POSITIVE", "note": "..."}

The rows are created by the FastAPI payment service when a transaction trips a rule.
"""

from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import require
from accounts.rbac import Perm
from transactions.models import Transaction

from .audit import log_admin_action
from .models import FraudLog


class FraudLogSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source="user.email", read_only=True)
    card_last4 = serializers.CharField(source="card.last4", default=None, read_only=True)
    reference = serializers.CharField(source="transaction.reference", read_only=True)
    amount = serializers.DecimalField(source="transaction.amount", max_digits=12, decimal_places=2, read_only=True)
    currency = serializers.CharField(source="transaction.currency", read_only=True)
    fraud_status = serializers.CharField(source="transaction.fraud_status", read_only=True)
    reviewed_by_email = serializers.EmailField(source="reviewed_by.email", default=None, read_only=True)
    rule_label = serializers.CharField(source="get_rule_display", read_only=True)

    class Meta:
        model = FraudLog
        fields = [
            "id", "rule", "rule_label", "severity", "details", "user_email", "card_last4",
            "reference", "amount", "currency", "fraud_status", "ip_address", "created_at",
            "reviewed", "reviewed_by_email", "reviewed_at", "resolution", "review_note",
        ]
        read_only_fields = fields


class FraudReviewSerializer(serializers.Serializer):
    resolution = serializers.ChoiceField(choices=FraudLog.Resolution.choices)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")

    def validate_note(self, value):
        return " ".join(value.split())  # one clean line; never trusted as markup


class FraudLogListView(ListAPIView):
    permission_classes = [require(Perm.FRAUD_VIEW)]
    serializer_class = FraudLogSerializer

    def get_queryset(self):
        params = self.request.query_params
        qs = FraudLog.objects.select_related("user", "card", "transaction", "reviewed_by")

        reviewed = params.get("reviewed", "").strip().lower()
        if reviewed in ("true", "false"):
            qs = qs.filter(reviewed=(reviewed == "true"))
        elif reviewed:
            raise ValidationError({"reviewed": "Must be 'true' or 'false'."})

        rule = params.get("rule", "").strip()
        if rule:
            if rule not in FraudLog.Rule.values:
                raise ValidationError({"rule": "Unknown rule."})
            qs = qs.filter(rule=rule)
        return qs


class FraudLogReviewView(APIView):
    permission_classes = [require(Perm.FRAUD_REVIEW)]

    def post(self, request, pk):
        serializer = FraudReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        resolution = serializer.validated_data["resolution"]

        with db_transaction.atomic():
            log = get_object_or_404(FraudLog.objects.select_for_update(), pk=pk)
            if log.reviewed:
                return Response({"detail": "This alert has already been reviewed."}, status=409)

            log.reviewed = True
            log.reviewed_by = request.user
            log.reviewed_at = timezone.now()
            log.resolution = resolution
            log.review_note = serializer.validated_data["note"]
            log.save()

            new_status = (
                Transaction.FraudStatus.CONFIRMED
                if resolution == FraudLog.Resolution.CONFIRMED_FRAUD
                else Transaction.FraudStatus.CLEARED
            )
            Transaction.objects.filter(pk=log.transaction_id).update(fraud_status=new_status)

            log_admin_action(
                request,
                "Reviewed fraud alert",
                target_type="fraud_log",
                target_id=log.pk,
                changes={"resolution": {"old": None, "new": resolution}},
                details=f"transaction_id={log.transaction_id}, rule={log.rule}",
            )

        log = FraudLog.objects.select_related("user", "card", "transaction", "reviewed_by").get(pk=pk)
        return Response(FraudLogSerializer(log).data)