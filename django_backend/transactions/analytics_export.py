"""
GET /api/transactions/analytics/export/?type=csv|pdf&months=6&scope=own|all

The same three summaries the charts show (monthly spending, categories, credit
utilization), as a CSV or PDF download. scope=all needs the analytics.export
permission and is written to the audit log.
"""

import csv
import io

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from accounts.rbac import Perm, has_permission
from adminpanel.audit import log_admin_action

from .analytics import _params, category_breakdown, monthly_summary, utilization
from .views import StatementRateThrottle


def _csv(monthly, categories, usage):
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Monthly spending"])
    writer.writerow(["Month", "Total spent", "Successful", "Failed"])
    writer.writerows([[m["label"], m["total_spent"], m["success_count"], m["failed_count"]] for m in monthly])
    writer.writerow([])
    writer.writerow(["Spending by category"])
    writer.writerow(["Category", "Total", "Transactions", "Share %"])
    writer.writerows([[c["label"], c["total"], c["count"], c["percent"]] for c in categories])
    writer.writerow([])
    writer.writerow(["Credit utilization"])
    writer.writerow(["Total limit", "Spent this month", "Available", "Utilization %"])
    writer.writerow([usage["total_limit"], usage["total_spent"], usage["available"], usage["utilization_percent"]])
    return buffer.getvalue()


def _pdf(monthly, categories, usage, params):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    styles = getSampleStyleSheet()
    out = io.BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm, title="Analytics summary")

    def table(rows, widths):
        t = Table(rows, colWidths=widths, repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F5F4D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F6F4")]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#C9D6D1")),
        ]))
        return t

    category_rows = [[c["label"], c["total"], c["count"], f"{c['percent']}%"] for c in categories] or [["No spending", "", "", ""]]
    scope = "All customers" if params["scope"] == "all" else "My cards"
    story = [
        Paragraph("Analytics summary", styles["Title"]),
        Paragraph(f"{scope} - last {params['months']} month(s) - {params['currency']} - generated {timezone.now():%d/%m/%Y %H:%M} UTC", styles["Normal"]),
        Spacer(1, 8 * mm),
        Paragraph("Credit utilization", styles["Heading2"]),
        table([["Total limit", "Spent this month", "Available", "Utilization"],
               [usage["total_limit"], usage["total_spent"], usage["available"], f"{usage['utilization_percent']}%"]], [42 * mm] * 4),
        Spacer(1, 6 * mm),
        Paragraph("Monthly spending", styles["Heading2"]),
        table([["Month", "Total spent", "Successful", "Failed"]] + [[m["label"], m["total_spent"], m["success_count"], m["failed_count"]] for m in monthly], [42 * mm] * 4),
        Spacer(1, 6 * mm),
        Paragraph("Spending by category", styles["Heading2"]),
        table([["Category", "Total", "Transactions", "Share"]] + category_rows, [42 * mm] * 4),
    ]
    doc.build(story)
    return out.getvalue()


class AnalyticsExportView(APIView):

    permission_classes = [IsAuthenticated]
    throttle_classes = [] if settings.TESTING else [StatementRateThrottle]

    def get(self, request):
        params = _params(request)
        if params["scope"] == "all" and not has_permission(request.user, Perm.ANALYTICS_EXPORT):
            raise PermissionDenied("Your role cannot export analytics.")

        monthly = monthly_summary(request, params)
        categories = category_breakdown(request, params)
        usage = utilization(request, params)

        if params["type"] == "pdf":
            response = HttpResponse(_pdf(monthly, categories, usage, params), content_type="application/pdf")
            filename = "analytics_summary.pdf"
        else:
            response = HttpResponse(_csv(monthly, categories, usage), content_type="text/csv")
            filename = "analytics_summary.csv"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Cache-Control"] = "no-store"

        if params["scope"] == "all":
            log_admin_action(request, "Exported analytics summary", target_type="analytics", changes={"type": params["type"], "months": params["months"]})
        return response