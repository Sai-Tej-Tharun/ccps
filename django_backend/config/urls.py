"""
Root URL configuration.

/admin/              Django admin (users, cards, transactions, admin logs)
/api/auth/           accounts app — register, login (JWT), refresh, logout
/api/cards/          cards app
/api/transactions/   transactions app (history, filters, CSV export)
/api/adminpanel/     adminpanel app (daily summary, action logs)
/api/schema/, /api/docs/   drf-spectacular OpenAPI schema + Swagger UI
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/cards/", include("cards.urls")),
    path("api/transactions/", include("transactions.urls")),
    path("api/adminpanel/", include("adminpanel.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
