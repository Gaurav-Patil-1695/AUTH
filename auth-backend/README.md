# auth-backend

FastAPI authentication service providing JWT-based login, registration, password reset, and token refresh.

---

## Features

- Email + password registration (`full_name`, `email`, `password`)
- JWT access tokens (short-lived) + rotating refresh tokens (httpOnly cookie)
- Bcrypt password hashing (configurable rounds)
- Password reset via email (token stored as SHA-256 hash)
- Enumeration-resistant responses on login and forgot-password
- Rate limiting on login and forgot-password endpoints
- CORS configured for the frontend origin

---

## Project structure

```
auth-backend/
├── app/
│   ├── main.py               # FastAPI application factory
│   ├── config.py             # Settings (pydantic-settings, reads .env)
│   ├── database.py           # SQLAlchemy engine & session
│   ├── dependencies.py       # Shared FastAPI dependencies
│   ├── auth/
│   │   ├── router.py         # /auth/* endpoints
│   │   ├── service.py        # Business logic
│   │   └── schemas.py        # Pydantic request/response models
│   └── models/
│       ├── user.py           # User ORM model
│       ├── refresh_token.py  # RefreshToken ORM model
│       └── password_reset.py # PasswordReset ORM model
├── tests/
│   └── test_auth.py          # pytest integration tests
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

---

## Quick start

### 1. Copy and configure environment variables

```bash
cp .env.example .env
# Edit .env — at minimum set DATABASE_URL, JWT_SECRET_KEY, and SMTP_* values
```

### 2. Run with Docker Compose (recommended)

From the repository root:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`.

Interactive docs: `http://localhost:8000/docs`

### 3. Run locally without Docker

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 4. Run tests

```bash
pytest
```

---

## Endpoints

| Method | Path                    | Description                          |
|--------|-------------------------|--------------------------------------|
| POST   | `/auth/register`        | Create a new account                 |
| POST   | `/auth/login`           | Obtain access + refresh tokens       |
| GET    | `/auth/me`              | Return the authenticated user        |
| POST   | `/auth/refresh`         | Rotate refresh token, issue new pair |
| POST   | `/auth/logout`          | Revoke the current refresh token     |
| POST   | `/auth/forgot-password` | Send a password-reset email          |
| POST   | `/auth/reset-password`  | Complete password reset              |

---

## Environment variables

All variables are read from `.env` (or from the real environment). Copy `.env.example` as a starting point.

### Database

| Variable       | Description                                 | Example                                                   |
|----------------|---------------------------------------------|-----------------------------------------------------------|
| `DATABASE_URL` | SQLAlchemy connection string (psycopg v3)   | `postgresql+psycopg://user:password@localhost:5432/auth_db` |

### JWT

| Variable                       | Description                                          | Default  |
|--------------------------------|------------------------------------------------------|----------|
| `JWT_SECRET_KEY`               | Secret used to sign access tokens — **change this**  | —        |
| `JWT_ALGORITHM`                | Signing algorithm                                    | `HS256`  |
| `JWT_ACCESS_TOKEN_TTL_MINUTES` | Access token lifetime in minutes                     | `15`     |

### Refresh tokens

| Variable                              | Description                                               | Default |
|---------------------------------------|-----------------------------------------------------------|---------|
| `REFRESH_TOKEN_TTL_DAYS`              | Refresh token lifetime (standard session)                 | `7`     |
| `REFRESH_TOKEN_TTL_REMEMBER_ME_DAYS`  | Refresh token lifetime when "remember me" is selected     | `30`    |

### Password hashing

| Variable        | Description                                   | Default |
|-----------------|-----------------------------------------------|---------|
| `BCRYPT_ROUNDS` | bcrypt cost factor (must be ≥ 12 per NFR-01)  | `12`    |

### Password reset

| Variable                    | Description                             | Default |
|-----------------------------|-----------------------------------------|---------|
| `RESET_TOKEN_TTL_MINUTES`   | Time before a reset link expires        | `60`    |

### SMTP

| Variable            | Description                               | Example                    |
|---------------------|-------------------------------------------|----------------------------|
| `SMTP_HOST`         | SMTP server hostname                      | `smtp.example.com`         |
| `SMTP_PORT`         | SMTP server port                          | `587`                      |
| `SMTP_USE_TLS`      | Enable STARTTLS (`true` / `false`)        | `true`                     |
| `SMTP_USERNAME`     | SMTP authentication username              | `no-reply@example.com`     |
| `SMTP_PASSWORD`     | SMTP authentication password              | —                          |
| `SMTP_FROM_ADDRESS` | Envelope / From address                   | `no-reply@example.com`     |
| `SMTP_FROM_NAME`    | Display name shown in the From header     | `Auth Starter`             |

### Rate limiting

| Variable                                   | Description                                        | Default |
|--------------------------------------------|----------------------------------------------------|---------|
| `RATE_LIMIT_LOGIN_MAX`                     | Maximum login attempts per window                  | `10`    |
| `RATE_LIMIT_LOGIN_WINDOW_SECONDS`          | Sliding window size for login rate limit (seconds) | `60`    |
| `RATE_LIMIT_FORGOT_PASSWORD_MAX`           | Maximum forgot-password requests per window        | `5`     |
| `RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS`| Sliding window size for forgot-password (seconds)  | `60`    |

### Application

| Variable       | Description                                                     | Example                   |
|----------------|-----------------------------------------------------------------|---------------------------|
| `APP_BASE_URL` | Public URL of the frontend (used to build password-reset links) | `http://localhost:3000`   |
| `CORS_ORIGIN`  | Allowed CORS origin for the frontend                            | `http://localhost:3000`   |

---

## Security notes

- Passwords are hashed with **bcrypt** at the configured round count; plaintext passwords are never stored or logged.
- Reset tokens and refresh tokens are stored as **SHA-256 hashes**; the raw token is sent only over the wire.
- Login errors always return `"Invalid email or password."` regardless of whether the email exists (enumeration resistance).
- Forgot-password always returns a generic 202 response regardless of whether the email is registered.
- Access tokens are short-lived JWTs; refresh tokens rotate on every use and are revoked on logout.
