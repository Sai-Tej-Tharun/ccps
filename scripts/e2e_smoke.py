"""
End-to-end smoke test against a RUNNING stack (docker-compose up).

    python scripts/e2e_smoke.py

Environment (all optional):
    DJANGO_API   default http://localhost:8000/api
    PAYMENTS_API default http://localhost:8001
    ADMIN_EMAIL / ADMIN_PASSWORD   default admin@example.com / StrongPass123!  (the demo admin)

It registers a throw-away customer, makes payments, trips the fraud rules, then checks
what an admin sees: fraud alerts, audit log, analytics, exports, role checks and health.
Exit code 0 = everything passed.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

DJANGO = os.environ.get("DJANGO_API", "http://localhost:8000/api").rstrip("/")
PAYMENTS = os.environ.get("PAYMENTS_API", "http://localhost:8001").rstrip("/")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "StrongPass123!")
PASSWORD = "SmokeTest-Pass-123!"

failures = []


def call(method, url, body=None, token=None, headers=None, raw=False):
    request = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None)
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=20) as reply:
            payload = reply.read()
            return reply.status, (payload if raw else json.loads(payload or "null"))
    except urllib.error.HTTPError as error:
        payload = error.read()
        try:
            return error.code, json.loads(payload or "null")
        except ValueError:
            return error.code, None


def check(label, condition, detail=""):
    print(f"{'PASS' if condition else 'FAIL'}  {label}{'  -> ' + str(detail) if detail and not condition else ''}")
    if not condition:
        failures.append(label)


def login(email, password):
    status, data = call("POST", f"{DJANGO}/auth/login/", {"email": email, "password": password})
    return data["access"] if status == 200 else None


def main():
    stamp = int(time.time())
    email = f"smoke{stamp}@example.com"
    device = {"X-Device-Id": f"smoke-device-{stamp}"}

    status, _ = call("POST", f"{DJANGO}/auth/register/", {"email": email, "password": PASSWORD, "first_name": "Smoke"})
    check("customer registers", status == 201, status)
    customer = login(email, PASSWORD)
    check("customer logs in", bool(customer))

    status, _ = call("POST", f"{DJANGO}/cards/", {"card_number": "4242424242424242", "cvv": "123", "cardholder_name": "Smoke Test", "expiry_month": 12, "expiry_year": 2035}, customer)
    check("card added", status == 201, status)
    card = call("GET", f"{DJANGO}/cards/", token=customer)[1]["results"][0]

    status, payment = call("POST", f"{PAYMENTS}/payments/pay", {"card_id": card["id"], "amount": "25.00", "category": "FOOD"}, customer, device)
    check("small payment succeeds", status == 201 and payment["status"] == "SUCCESS", payment)

    references = []
    for _ in range(3):
        status, payment = call("POST", f"{PAYMENTS}/payments/pay", {"card_id": card["id"], "amount": "2500.00", "category": "TRAVEL"}, customer, device)
        references.append(payment["reference"])
    check("high-value payments accepted", status == 201)

    admin = login(ADMIN_EMAIL, ADMIN_PASSWORD)
    check("admin logs in", bool(admin), "set ADMIN_EMAIL / ADMIN_PASSWORD")
    if not admin:
        return

    status, logs = call("GET", f"{DJANGO}/adminpanel/fraud-logs/?reviewed=false", token=admin)
    mine = [row for row in logs["results"] if row["reference"] == references[-1]] if status == 200 else []
    check("third high-value payment is flagged as fraud", len(mine) == 1 and mine[0]["rule"] == "HIGH_VALUE_BURST", logs)

    status, _ = call("GET", f"{DJANGO}/adminpanel/fraud-logs/", token=customer)
    check("customer cannot read fraud logs (403)", status == 403, status)

    if mine:
        status, reviewed = call("POST", f"{DJANGO}/adminpanel/fraud-logs/{mine[0]['id']}/review/", {"resolution": "FALSE_POSITIVE", "note": "smoke test"}, admin)
        check("admin reviews the alert", status == 200 and reviewed["fraud_status"] == "CLEARED", reviewed)

    status, mine_txns = call("GET", f"{DJANGO}/transactions/?card=4242&ordering=-amount&page_size=2", token=customer)
    check("search by masked card + sort + page size works", status == 200 and len(mine_txns["results"]) == 2 and mine_txns["results"][0]["amount"] == "2500.00", mine_txns)
    check("customers never see fraud_status", "fraud_status" not in mine_txns["results"][0])

    status, monthly = call("GET", f"{DJANGO}/transactions/analytics/monthly/?months=3", token=customer)
    check("monthly spending includes the payments", status == 200 and float(monthly[-1]["total_spent"]) >= 7525, monthly)
    status, categories = call("GET", f"{DJANGO}/transactions/analytics/categories/", token=customer)
    check("category data has TRAVEL", status == 200 and any(c["category"] == "TRAVEL" for c in categories), categories)
    status, usage = call("GET", f"{DJANGO}/transactions/analytics/utilization/", token=customer)
    check("credit utilization is reported", status == 200 and usage["utilization_percent"] > 0, usage)
    status, csv_bytes = call("GET", f"{DJANGO}/transactions/analytics/export/?type=csv", token=customer, raw=True)
    check("analytics CSV export", status == 200 and b"Monthly spending" in csv_bytes)
    status, pdf_bytes = call("GET", f"{DJANGO}/transactions/analytics/export/?type=pdf", token=customer, raw=True)
    check("analytics PDF export", status == 200 and pdf_bytes.startswith(b"%PDF"))
    status, _ = call("GET", f"{DJANGO}/transactions/analytics/monthly/?scope=all", token=customer)
    check("customer cannot read all-customer analytics (403)", status == 403, status)

    status, _ = call("POST", f"{DJANGO}/adminpanel/cards/{card['id']}/block/", token=customer)
    check("customer cannot block a card (403)", status == 403, status)
    status, _ = call("POST", f"{DJANGO}/adminpanel/cards/{card['id']}/block/", token=admin)
    check("admin blocks the card", status == 200, status)
    status, body = call("POST", f"{PAYMENTS}/payments/pay", {"card_id": card["id"], "amount": "5.00"}, customer, device)
    check("a blocked card cannot pay (403)", status == 403, body)
    status, _ = call("POST", f"{DJANGO}/adminpanel/cards/{card['id']}/unblock/", token=admin)
    check("admin unblocks the card", status == 200, status)

    status, audit = call("GET", f"{DJANGO}/adminpanel/logs/?action=card", token=admin)
    actions = {row["action"] for row in audit["results"]} if status == 200 else set()
    check("block and unblock are in the audit log", {"Blocked card", "Unblocked card"} <= actions, actions)

    status, health = call("GET", f"{DJANGO}/adminpanel/system-health/", token=admin)
    check("system health: database ok", status == 200 and health["services"]["database"]["status"] == "ok", health)
    check("system health: payment service reachable", status == 200 and health["services"]["payment_service"]["status"] == "ok", health)
    check("system health: requests are being logged", status == 200 and health["requests"]["total"] > 0, health)
    check("system health: both services reported", status == 200 and {s["service"] for s in health["by_service"]} == {"django", "fastapi"}, health)


if __name__ == "__main__":
    main()
    print(f"\n{len(failures)} failed" if failures else "\nAll checks passed")
    sys.exit(1 if failures else 0)