from django.urls import path

from .analytics import CategoryBreakdownView, MonthlySummaryView, UtilizationView
from .analytics_export import AnalyticsExportView
from .views import MonthlyStatementView, TransactionExportCSVView, TransactionListView

urlpatterns = [
    path("", TransactionListView.as_view(), name="transaction-list"),
    path("export/", TransactionExportCSVView.as_view(), name="transaction-export-csv"),
    path("statement/", MonthlyStatementView.as_view(), name="transaction-statement"),
    path("analytics/monthly/", MonthlySummaryView.as_view(), name="analytics-monthly"),
    path("analytics/categories/", CategoryBreakdownView.as_view(), name="analytics-categories"),
    path("analytics/utilization/", UtilizationView.as_view(), name="analytics-utilization"),
    path("analytics/export/", AnalyticsExportView.as_view(), name="analytics-export"),
]
