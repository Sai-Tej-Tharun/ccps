# Credit Card Payment System

A simulated (no real gateway) credit card payment platform built across two backends and one frontend:

- **Django + Django REST Framework** — user auth (JWT), card management, transaction history/filtering/CSV export, and the admin panel.
- **FastAPI** — payment processing only: creates a `PENDING` transaction and resolves it to `SUCCESS`/`FAILED` via a deterministic simulation (see [Payment Simulation Rules](#payment-simulation-rules)).
- **React + Tailwind CSS** — the UI for both.
- **MySQL** — single shared database; Django owns all migrations, FastAPI mirrors the tables it needs to read/write.

No real payment gateway, no CVV storage, no plain-text passwords — see [Security](#security).

---

## Architecture

```
┌─────────────┐      JWT (shared secret)      ┌──────────────────┐
│   React     │ ───────────────────────────── │  Django (8000)   │
│  frontend   │                                │  auth/cards/     │
│   (5173)    │                                │  transactions/   │
└──────┬──────┘                                │  admin           │
       │                                       └─────────┬────────┘
       │          JWT (same shared secret)                │ owns migrations
       └───────────────────────────────┐                  │
                                        ▼                  ▼
                                ┌──────────────────┐   ┌────────┐
                                │ FastAPI (8001)    │──▶│ MySQL  │
                                │ payment service   │   │ (3306) │
                                └──────────────────┘   └────────┘
```

Django issues JWTs (access + refresh) on login. FastAPI never issues tokens — it only verifies the same token (same `JWT_SHARED_SECRET`, same `HS256` algorithm, same `user_id` claim SimpleJWT puts on every access token) and reads/writes the `transactions_transaction` table directly via SQLAlchemy, mirroring Django's schema (see `fastapi_backend/models.py`'s docstring for the exact table/column mapping).

---

## Setup (Docker — recommended)

1. Copy the env file and adjust if needed (the defaults work out of the box for local use):
   ```bash
   cp .env.example .env
   ```
2. Build and start everything:
   ```bash
   docker compose up --build
   ```
3. Wait for `django_backend` to finish migrating (first boot only takes a few extra seconds) — it also seeds the demo admin automatically.
4. Open:
   - Frontend: http://localhost:5173
   - Django API docs (Swagger): http://localhost:8000/api/docs/
   - Django admin: http://localhost:8000/admin/
   - FastAPI docs (Swagger): http://localhost:8001/docs

**Demo admin credentials** (seeded automatically, change via `.env` before using this anywhere beyond local evaluation):
```
Email:    admin@example.com
Password: StrongPass123!
```

---

## Setup (without Docker)

**Django:**
```bash
cd django_backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export DB_HOST=127.0.0.1 DB_USER=ccps_user DB_PASSWORD=ccps_password DB_NAME=ccps_db
python manage.py migrate
python manage.py create_demo_admin
python manage.py runserver 0.0.0.0:8000
```

**FastAPI** (needs Django's migrations already applied against the same MySQL instance):
```bash
cd fastapi_backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
export DB_HOST=127.0.0.1 DB_USER=ccps_user DB_PASSWORD=ccps_password DB_NAME=ccps_db
export JWT_SHARED_SECRET=<same value as Django's>
uvicorn main:app --reload --port 8001
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Running tests without a live MySQL server

Both test suites run against SQLite/in-memory DBs in isolation — no MySQL needed:

```bash
# Django (29 tests, ~89% coverage)
cd django_backend
pip install -r requirements.txt
export DB_ENGINE=django.db.backends.sqlite3 DB_NAME=/tmp/test.sqlite3
coverage run manage.py test
coverage report

# FastAPI (14 tests, 94% coverage)
cd fastapi_backend
pip install -r requirements.txt
coverage run -m pytest
coverage report
```

---

## API Documentation

| Service | Swagger UI | Notes |
|---|---|---|
| Django | http://localhost:8000/api/docs/ | via drf-spectacular |
| FastAPI | http://localhost:8001/docs | built-in |

A ready-to-import Postman collection covering every endpoint (with a login request that auto-saves your access token for every other request) is at [`postman/Credit_Card_Payment_System.postman_collection.json`](postman/Credit_Card_Payment_System.postman_collection.json).

### Endpoint summary

**Django — `/api/auth/`**
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/register/` | Public | Create an account |
| POST | `/login/` | Public | Get access + refresh tokens |
| POST | `/refresh/` | Public | Rotate tokens |
| POST | `/logout/` | Required | Blacklist the refresh token |
| GET | `/me/` | Required | Current user's profile |

**Django — `/api/cards/`**
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/` | Required | List your own cards |
| POST | `/` | Required | Add a card (validates, masks, discards the raw number/CVV) |
| DELETE | `/<id>/` | Required (owner only) | Remove a card |

**FastAPI — `/payments/`**
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/pay` | Required | Make a payment — creates `PENDING`, resolves to `SUCCESS`/`FAILED` |
| GET | `/<id>` | Required (owner only) | Look up one payment |
| GET | `/` | Required | Your own payment history (last 100) |

**Django — `/api/transactions/`**
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/` | Required | Your history (admins see everyone's). Filters: `status`, `date_from`, `date_to`, `min_amount`, `max_amount` |
| GET | `/export/` | Admin only | CSV export, same filters |

**Django — `/api/adminpanel/`**
| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/daily-summary/?days=30` | Admin only | Per-day transaction counts/amounts |
| GET | `/logs/` | Admin only | Audit trail (e.g. CSV exports) |

---

## Payment Simulation Rules

No real gateway is used anywhere. Outcomes are **deterministic** (not random) so they're reliably demoable and testable:

| Trigger | Result |
|---|---|
| Card number ending in `0002` | `FAILED` — "Card declined by simulated issuer." |
| Card number ending in `0069` | `FAILED` — "Simulated expired card." |
| Card number ending in `0127` | `FAILED` — "Simulated incorrect CVC." |
| Amount > 5000.00 | `FAILED` — "Amount exceeds simulated processing limit." |
| Anything else | `SUCCESS` |

(This mirrors the same idea as Stripe's published test card numbers — pick a Luhn-valid number ending in one of the above to demo a decline.)

---

## Database Schema

Django owns every migration (`django_backend/*/migrations/`). Core tables:

| Table | Key columns |
|---|---|
| `auth_user` (built-in) | `id`, `username` (= email), `email`, `password` (hashed), `is_staff`, `is_superuser` |
| `cards_card` | `id`, `user_id`, `brand`, `masked_number`, `last4`, `cardholder_name`, `expiry_month`, `expiry_year`, `created_at` — **no raw number or CVV column exists anywhere** |
| `transactions_transaction` | `id`, `user_id`, `card_id`, `amount`, `currency`, `status`, `reference`, `failure_reason`, `created_at`, `updated_at` |
| `adminpanel_adminactionlog` | `id`, `admin_user_id`, `action`, `details`, `created_at` |

### Producing a database dump for submission

```bash
docker compose exec mysql mysqldump -u root -p$DB_ROOT_PASSWORD ccps_db > db/dump.sql
```

---

## Security

- **No raw card numbers or CVVs stored, ever** — `cards/serializers.py`'s `CardCreateSerializer` accepts them only to run Luhn validation and masking (`cards/validators.py`), then discards both; neither field exists on the `Card` model.
- **Passwords** are hashed via Django's PBKDF2 hasher (`set_password()`), never stored or logged in plain text.
- **JWT authentication** required on every endpoint except register/login/refresh; FastAPI independently verifies the same token rather than trusting the frontend.
- **Ownership checks** everywhere data is scoped: a card/payment/transaction ID belonging to another user 404s rather than 403ing (doesn't even confirm the ID exists).
- **Input validation**: DRF serializers (Django side) and Pydantic models (FastAPI side) reject malformed input before it reaches any business logic.
- **SQL injection protection**: both the Django ORM and SQLAlchemy ORM parameterize every query — no raw string-interpolated SQL anywhere in the codebase.
- **Rate limiting**: DRF throttling (20/min anonymous, 120/min authenticated) is active in all non-test environments.

---

## Testing

| Service | Tests | Coverage |
|---|---|---|
| Django | 31 | 94% |
| FastAPI | 14 | 94% |

Both exceed the 50% minimum requirement comfortably. See [Running tests without a live MySQL server](#running-tests-without-a-live-mysql-server) above for exact commands.

---

## Submission Checklist

- [ ] GitHub repository link — push this folder and link it
- [ ] Database dump — see [Producing a database dump](#producing-a-database-dump-for-submission) above
- [x] Postman collection — `postman/Credit_Card_Payment_System.postman_collection.json`
- [ ] UI screenshots — add to a `screenshots/` folder (register, login, dashboard, add card, make payment success, make payment decline, transaction history with filters, admin dashboard)
- [x] Admin credentials — see [Setup (Docker)](#setup-docker--recommended) above

## Project Structure

```
.
├── docker-compose.yml
├── .env.example
├── postman/
│   └── Credit_Card_Payment_System.postman_collection.json
├── django_backend/        # auth, cards, transactions, admin panel
│   ├── accounts/
│   ├── cards/
│   ├── transactions/
│   ├── adminpanel/
│   └── config/
├── fastapi_backend/        # payment processing only
│   ├── main.py
│   ├── payments.py
│   ├── simulation.py
│   └── tests/
└── frontend/                # React + Tailwind
    └── src/
        ├── api/
        ├── context/
        ├── components/
        └── pages/
```
