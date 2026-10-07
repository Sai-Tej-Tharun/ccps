"""
Credit Card Payment System — FastAPI payment service.

Owns Module 3 (Payment Processing) only. Auth, cards, and transaction
history/admin views are Django's responsibility (see django_backend/) —
this service shares the same MySQL database and mirrors the tables it
needs (see models.py), authenticating requests with the same JWT Django
issues (see auth.py).

Swagger UI: /docs   ReDoc: /redoc
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dashboard import router as dashboard_router
from payments import router as payments_router

app = FastAPI(
    title="Credit Card Payment System — Payment Service",
    description="Simulated payment processing (no real gateway). See /payments/pay.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(payments_router)
app.include_router(dashboard_router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
