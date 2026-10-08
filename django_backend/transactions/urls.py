from django.urls import path

from .views import MonthlyStatementView, TransactionExportCSVView, TransactionListView

urlpatterns = [
    path("", TransactionListView.as_view(), name="transaction-list"),
    path("export/", TransactionExportCSVView.as_view(), name="transaction-export-csv"),
    path("statement/", MonthlyStatementView.as_view(), name="transaction-statement"),
]
