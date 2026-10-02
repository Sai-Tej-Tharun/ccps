from django.urls import path

from .views import AdminActionLogListView, DailySummaryView

urlpatterns = [
    path("daily-summary/", DailySummaryView.as_view(), name="admin-daily-summary"),
    path("logs/", AdminActionLogListView.as_view(), name="admin-action-logs"),
]
