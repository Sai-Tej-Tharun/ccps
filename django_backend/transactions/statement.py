"""
Monthly statement generation.

get_statement_data()   - queries only the requesting user's own data
render_statement_pdf() - turns that data into a PDF (ReportLab, in memory)

Card numbers are never available here in full - the database only holds the
masked form (e.g. "**** **** **** 1234") - so the PDF can only ever show
masked card details.
"""

import calendar
import io
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal
from xml.sax.saxutils import escape

from django.db.models import Count, Sum
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from cards.models import Card

from .models import Transaction

BRAND = colors.HexColor("#1F6F5C")
INK = colors.HexColor("#15231F")
MUTED = colors.HexColor("#5B6B66")
RULE = colors.HexColor("#D3E5DE")
ZEBRA = colors.HexColor("#F4F8F6")
STATUS_COLORS = {"FAILED": "#B3261E", "PENDING": "#9A6B00"}


# --------------------------------------------------------------------------
# Data
# --------------------------------------------------------------------------
def get_statement_data(user, year: int, month: int) -> dict:
    last_day = calendar.monthrange(year, month)[1]
    start = datetime(year, month, 1, tzinfo=dt_timezone.utc)
    end = (
        datetime(year + 1, 1, 1, tzinfo=dt_timezone.utc)
        if month == 12
        else datetime(year, month + 1, 1, tzinfo=dt_timezone.utc)
    )

    transactions = Transaction.objects.filter(user=user, created_at__gte=start, created_at__lt=end)

    spending = {
        row["currency"]: row["total"]
        for row in transactions.filter(status=Transaction.Status.SUCCESS)
        .values("currency")
        .annotate(total=Sum("amount"))
        .order_by("currency")
    }
    counts = {row["status"]: row["n"] for row in transactions.values("status").annotate(n=Count("id"))}

    return {
        "user": user,
        "year": year,
        "month": month,
        "period_start": start.date(),
        "period_end": datetime(year, month, last_day).date(),
        "generated_at": timezone.now(),
        "cards": list(Card.objects.filter(user=user).order_by("created_at")),
        "transactions": list(transactions.select_related("card").order_by("created_at", "id")),
        "spending_by_currency": spending,
        "counts": {
            "SUCCESS": counts.get(Transaction.Status.SUCCESS, 0),
            "FAILED": counts.get(Transaction.Status.FAILED, 0),
            "PENDING": counts.get(Transaction.Status.PENDING, 0),
        },
    }


# --------------------------------------------------------------------------
# PDF
# --------------------------------------------------------------------------
class _NumberedCanvas(canvas.Canvas):
    """Two-pass canvas so every page can print 'Page X of Y' plus a footer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_pages = []

    def showPage(self):
        self._saved_pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_pages)
        for state in self._saved_pages:
            self.__dict__.update(state)
            self._draw_footer(total)
            super().showPage()
        super().save()

    def _draw_footer(self, total):
        width, _ = A4
        self.setStrokeColor(RULE)
        self.setLineWidth(0.5)
        self.line(18 * mm, 16 * mm, width - 18 * mm, 16 * mm)
        self.setFont("Helvetica", 7.5)
        self.setFillColor(MUTED)
        self.drawString(18 * mm, 11.5 * mm, "Card numbers are masked. This statement was generated electronically.")
        self.drawRightString(width - 18 * mm, 11.5 * mm, f"Page {self._pageNumber} of {total}")


def _styles():
    base = getSampleStyleSheet()["Normal"]
    return {
        "brand": ParagraphStyle("brand", parent=base, fontName="Helvetica-Bold", fontSize=18, textColor=BRAND, leading=22),
        "title": ParagraphStyle("title", parent=base, fontName="Helvetica-Bold", fontSize=13, textColor=INK, leading=17),
        "period": ParagraphStyle("period", parent=base, fontSize=9.5, textColor=MUTED, leading=13, alignment=TA_RIGHT),
        "h2": ParagraphStyle("h2", parent=base, fontName="Helvetica-Bold", fontSize=10.5, textColor=BRAND, leading=14, spaceBefore=10, spaceAfter=4),
        "cell": ParagraphStyle("cell", parent=base, fontSize=8.5, textColor=INK, leading=11),
        "cell_r": ParagraphStyle("cell_r", parent=base, fontSize=8.5, textColor=INK, leading=11, alignment=TA_RIGHT),
        "label": ParagraphStyle("label", parent=base, fontSize=8.5, textColor=MUTED, leading=11),
        "head": ParagraphStyle("head", parent=base, fontName="Helvetica-Bold", fontSize=8, textColor=colors.white, leading=10),
        "head_r": ParagraphStyle("head_r", parent=base, fontName="Helvetica-Bold", fontSize=8, textColor=colors.white, leading=10, alignment=TA_RIGHT),
        "empty": ParagraphStyle("empty", parent=base, fontSize=9, textColor=MUTED, leading=12, spaceBefore=6),
    }


def _p(text, style, color=None):
    safe = escape(str(text))
    if color:
        safe = f'<font color="{color}">{safe}</font>'
    return Paragraph(safe, style)


def _money(amount, currency):
    return f"{currency} {Decimal(amount):,.2f}"


def _key_value_table(rows, styles, col_widths):
    table = Table([[_p(k, styles["label"]), _p(v, styles["cell"])] for k, v in rows], colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -1), 0.4, RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return table


def render_statement_pdf(data: dict) -> bytes:
    styles = _styles()
    user = data["user"]
    page_width, _ = A4
    usable = page_width - 36 * mm

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=22 * mm,
        title=f"Statement {data['year']}-{data['month']:02d}",
        author="LedgerPay",
    )
    story = []

    # Header
    month_name = calendar.month_name[data["month"]]
    header = Table(
        [[
            [Paragraph("LedgerPay", styles["brand"]), Paragraph("Monthly Card Statement", styles["title"])],
            Paragraph(
                f"{month_name} {data['year']}<br/>"
                f"{data['period_start']:%d %b %Y} - {data['period_end']:%d %b %Y}",
                styles["period"],
            ),
        ]],
        colWidths=[usable * 0.6, usable * 0.4],
    )
    header.setStyle(
        TableStyle([("VALIGN", (0, 0), (-1, -1), "BOTTOM"), ("LINEBELOW", (0, 0), (-1, 0), 1.2, BRAND), ("BOTTOMPADDING", (0, 0), (-1, -1), 8)])
    )
    story += [header, Spacer(1, 6)]

    # Account details
    full_name = f"{user.first_name} {user.last_name}".strip() or user.email
    story.append(Paragraph("Account details", styles["h2"]))
    story.append(
        _key_value_table(
            [
                ("Account holder", full_name),
                ("Email", user.email),
                ("Statement period", f"{data['period_start']:%d/%m/%Y} to {data['period_end']:%d/%m/%Y}"),
                ("Generated on", f"{data['generated_at']:%d/%m/%Y %H:%M} UTC"),
            ],
            styles,
            [usable * 0.28, usable * 0.72],
        )
    )

    # Summary
    story.append(Paragraph("Summary", styles["h2"]))
    summary_rows = []
    if data["spending_by_currency"]:
        for currency, total in data["spending_by_currency"].items():
            summary_rows.append((f"Total spending ({currency})", _money(total, currency)))
    else:
        summary_rows.append(("Total spending", "0.00"))
    counts = data["counts"]
    summary_rows += [
        ("Successful transactions", counts["SUCCESS"]),
        ("Failed transactions", counts["FAILED"]),
        ("Pending transactions", counts["PENDING"]),
        ("Total transactions", sum(counts.values())),
    ]
    story.append(_key_value_table(summary_rows, styles, [usable * 0.28, usable * 0.72]))
    story.append(Paragraph("Total spending counts successful payments only.", styles["label"]))

    # Cards (masked)
    story.append(Paragraph("Cards on file", styles["h2"]))
    if data["cards"]:
        card_rows = [[_p("Card", styles["head"]), _p("Cardholder", styles["head"]), _p("Expiry", styles["head"]), _p("Status", styles["head"]), _p("Credit limit", styles["head_r"])]]
        for card in data["cards"]:
            card_rows.append(
                [
                    _p(f"{card.brand}  {card.masked_number}", styles["cell"]),
                    _p(card.cardholder_name, styles["cell"]),
                    _p(f"{card.expiry_month:02d}/{card.expiry_year}", styles["cell"]),
                    _p("Blocked" if card.is_blocked else "Active", styles["cell"], "#B3261E" if card.is_blocked else None),
                    _p(f"{Decimal(card.credit_limit):,.2f}", styles["cell_r"]),
                ]
            )
        cards_table = Table(card_rows, colWidths=[usable * 0.34, usable * 0.26, usable * 0.12, usable * 0.12, usable * 0.16], repeatRows=1)
        cards_table.setStyle(_grid_style())
        story.append(cards_table)
    else:
        story.append(Paragraph("No cards on file.", styles["empty"]))

    # Transactions
    story.append(Paragraph("Transactions", styles["h2"]))
    if data["transactions"]:
        rows = [[_p("Date (UTC)", styles["head"]), _p("Reference", styles["head"]), _p("Card", styles["head"]), _p("Status", styles["head"]), _p("Amount", styles["head_r"])]]
        for txn in data["transactions"]:
            rows.append(
                [
                    _p(f"{txn.created_at:%d/%m/%Y %H:%M}", styles["cell"]),
                    _p(txn.reference[:12].upper(), styles["cell"]),
                    _p(txn.card.masked_number if txn.card else "Card removed", styles["cell"]),
                    _p(txn.status.title(), styles["cell"], STATUS_COLORS.get(txn.status)),
                    _p(_money(txn.amount, txn.currency), styles["cell_r"]),
                ]
            )
        table = Table(rows, colWidths=[usable * 0.19, usable * 0.17, usable * 0.28, usable * 0.12, usable * 0.24], repeatRows=1)
        table.setStyle(_grid_style())
        story.append(table)
    else:
        story.append(Paragraph("No transactions were recorded in this period.", styles["empty"]))

    doc.build(story, canvasmaker=_NumberedCanvas)
    return buffer.getvalue()


def _grid_style():
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), BRAND),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, ZEBRA]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.3, RULE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
    )