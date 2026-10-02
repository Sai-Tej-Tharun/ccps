from django.urls import path

from .views import TransactionExportCSVView, TransactionListView

urlpatterns = [
    path("", TransactionListView.as_view(), name="transaction-list"),
    path("export/", TransactionExportCSVView.as_view(), name="transaction-export-csv"),
]
