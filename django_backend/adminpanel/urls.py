from django.urls import path

from .card_views import (
    AdminCardActivityView,
    AdminCardBlockView,
    AdminCardCreditLimitView,
    AdminCardListView,
    AdminCardUnblockView,
)
from .views import AdminActionLogListView, DailySummaryView

urlpatterns = [
    path("daily-summary/", DailySummaryView.as_view(), name="admin-daily-summary"),
    path("logs/", AdminActionLogListView.as_view(), name="admin-action-logs"),
    path("cards/", AdminCardListView.as_view(), name="admin-card-list"),
    path("cards/<int:pk>/block/", AdminCardBlockView.as_view(), name="admin-card-block"),
    path("cards/<int:pk>/unblock/", AdminCardUnblockView.as_view(), name="admin-card-unblock"),
    path("cards/<int:pk>/credit-limit/", AdminCardCreditLimitView.as_view(), name="admin-card-credit-limit"),
    path("cards/<int:pk>/activity/", AdminCardActivityView.as_view(), name="admin-card-activity"),
]
