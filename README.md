# 🎟️ Coupon Marketplace

A production-ready full-stack digital coupon marketplace supporting two sales channels:
- **Direct customers** via a web frontend
- **External resellers** via a REST API

Built with Python/FastAPI, PostgreSQL, and Docker.

---

## 📸 Screenshots

### Customer Shop
Browse and purchase coupons instantly. Coupon code is revealed only after purchase.

### Admin Dashboard
Full CRUD management with real-time pricing preview and sales statistics.

---

## 🏗️ Architecture
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Customer UI   │     │   Reseller API  │     │   Admin UI      │
│  localhost:3000 │     │  Bearer Token   │     │  localhost:3000 │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                        │
         └───────────────────────┼────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   FastAPI Backend        │
                    │   localhost:8000         │
                    │                          │
                    │  Routes → Controllers    │
                    │  → Services → Repos      │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   PostgreSQL Database    │
                    │   localhost:5432         │
                    └─────────────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | Python 3.11, FastAPI | Fast, modern, auto-docs |
| Database | PostgreSQL 16 | ACID compliance, computed columns |
| Frontend | HTML/CSS/JavaScript | No build step needed |
| Auth | JWT + bcrypt | Secure, stateless |
| Infrastructure | Docker, Docker Compose | One-command setup |

---

## 🚀 Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Git

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/coupon-marketplace.git
cd coupon-marketplace
```

### 2. Create environment file
Create `backend/.env`:
```env
DB_HOST=postgres
DB_PORT=5432
DB_NAME=coupon_marketplace
DB_USER=postgres
DB_PASSWORD=postgres
JWT_SECRET=your-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password
RESELLER_TOKEN=your-reseller-token
```

### 3. Start everything
```bash
docker compose up --build
```

### 4. Open the app

| Service | URL |
|---------|-----|
| 🛍️ Customer Shop | http://localhost:3000 |
| ⚙️ Admin Dashboard | http://localhost:3000 (click Admin) |
| 📡 API Docs | http://localhost:8000/docs |

---

## 📁 Project Structure
```
coupon-marketplace/
├── backend/
│   ├── app/
│   │   ├── config/
│   │   │   ├── database.py      # DB connection
│   │   │   └── migrate.py       # Schema + seeding
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic models
│   │   ├── repositories/
│   │   │   ├── product_repository.py  # SQL queries
│   │   │   └── auth_repository.py     # Auth queries
│   │   ├── services/
│   │   │   └── product_service.py     # Business logic
│   │   ├── middleware/
│   │   │   └── auth.py          # JWT + Bearer auth
│   │   ├── routes/
│   │   │   ├── admin.py         # Admin endpoints
│   │   │   └── reseller.py      # Reseller endpoints
│   │   └── main.py              # FastAPI entry point
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── requirements.txt
├── frontend/
│   └── index.html               # Single-page app
├── docker-compose.yml
└── README.md
```

---

## 💰 Pricing System

Minimum sell price is enforced at the **database level** using a PostgreSQL computed column:
```sql
minimum_sell_price NUMERIC GENERATED ALWAYS AS
    (cost_price * (1 + margin_percentage / 100)) STORED
```

This means:
- ✅ Cannot be overridden by application code
- ✅ Cannot be overridden even by direct SQL
- ✅ Always mathematically correct

### Example
| cost_price | margin_percentage | minimum_sell_price |
|-----------|------------------|-------------------|
| $80.00 | 25% | $100.00 |
| $50.00 | 20% | $60.00 |
| $10.00 | 50% | $15.00 |

---

## 🔐 Authentication

### Admin (JWT)
- Login via `POST /api/admin/auth/login`
- Returns a JWT token valid for 8 hours
- Required for all admin operations

### Resellers (Bearer Token)
- Long-lived API keys stored as bcrypt hashes
- Passed as `Authorization: Bearer <token>`
- Created by admin via `POST /api/admin/reseller-tokens`

---

## 🛒 User Flows

### Customer
1. Visit `http://localhost:3000`
2. Browse available coupons
3. Click **Buy Now**
4. Coupon code revealed instantly ✅

### Reseller
```bash
# 1. Get available products
curl http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. Purchase a product (price must be >= minimum_sell_price)
curl -X POST http://localhost:8000/api/v1/products/{id}/purchase \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"reseller_price": 25.00}'
```

### Admin
1. Visit `http://localhost:3000` → click **Admin**
2. Login with credentials from `.env`
3. Create/edit/delete coupons
4. Monitor sales statistics

---

## 📡 API Reference

### Public
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/public/products` | List available products (no auth) |

### Reseller API (Bearer token)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/products` | List available products |
| GET | `/api/v1/products/{id}` | Get single product |
| POST | `/api/v1/products/{id}/purchase` | Purchase a product |

### Admin API (JWT)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/admin/auth/login` | Login, get JWT |
| GET | `/api/admin/products` | List all products |
| POST | `/api/admin/products` | Create coupon |
| PATCH | `/api/admin/products/{id}` | Update coupon |
| DELETE | `/api/admin/products/{id}` | Delete coupon |
| POST | `/api/admin/products/{id}/purchase` | Direct purchase |
| GET | `/api/admin/reseller-tokens` | List tokens |
| POST | `/api/admin/reseller-tokens` | Create token |

---

## 🔒 Security Features

- **Bcrypt hashing** — passwords and API tokens never stored in plain text
- **JWT expiry** — admin sessions expire after 8 hours
- **Price enforcement** — database-level computed columns prevent price manipulation
- **Atomic purchases** — `SELECT FOR UPDATE` row locking prevents race conditions/double selling
- **Data isolation** — resellers never see cost price or margin percentage

---

## 🗄️ Database Schema
```
products          coupons              admin_users
─────────         ───────              ───────────
id (UUID)    ←── product_id (FK)      id (UUID)
name              cost_price           username
description       margin_percentage    password_hash
type              minimum_sell_price*
image_url         is_sold              reseller_tokens
created_at        value_type           ───────────────
updated_at        coupon_value         id (UUID)
                                       name
purchase_log                           token_hash
────────────                           is_active
id (UUID)
product_id (FK)   * GENERATED ALWAYS AS computed column
channel
final_price
purchased_at
```

---

## 🐳 Docker Services

| Service | Image | Port |
|---------|-------|------|
| frontend | nginx:alpine | 3000 |
| backend | python:3.11-slim | 8000 |
| postgres | postgres:16-alpine | 5432 |
