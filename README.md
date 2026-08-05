# auth-starter

Email + password authentication starter — React + FastAPI + PostgreSQL, JWT strategy

> React (vite) | Fastapi | Postgres | JWT auth | Docker

## Features
- **Register an account**: Lets a new visitor create an account with name, email, and a policy-compliant password after accepting the Terms.
- **Log in**: Lets a registered user sign in with email and password.
- **Stay signed in**: Lets a returning user extend their session with a "Remember me" option.
- **Recover a forgotten password**: Lets a user request a reset link by email, enumeration-safely.
- **Set a new password**: Lets a user with a valid reset token choose a new password.
- **Log out**: Lets a logged-in user end their session on a device.
- **Access protected areas**: Keeps the user authenticated across protected pages, silently refreshing access tokens.
- **Trust the sign-in experience**: Provides a clean, branded, accessible sign-in experience across all auth screens.

### User roles
- **Visitor (Guest)**: An unauthenticated person. Can reach only the guest auth routes (login, register, forgot-password, reset-password) and can create an account or recover access.
- **Registered User**: A person with an account, identified uniquely by email. Can sign in, stay signed in via a refresh token, reach protected areas (e.g. /profile), and log out.

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | React + TypeScript (bundled with vite) |
| Backend | Fastapi |
| Database | Postgres |
| Auth | JWT (access + refresh tokens) |
| Container | Docker + Docker Compose |

## Project structure

### Backend

```text
auth-backend/
  requirements.txt - dependencies: fastapi, uvicorn[standard], pydantic, sqlalchemy, psycopg[binary], python-jose[cryp...
  Dockerfile - container image for the FastAPI app (docker.enabled=true)
  .env.example - environment template (DATABASE_URL, JWT_*, BCRYPT_ROUNDS, RESET_TOKEN_TTL_MINUTES, REFRESH_TOKEN_...
  README.md - project overview, setup, and env variable docs
  app/
    main.py - FastAPI app; global API_PREFIX (/api/v1); CORS from CORS_ORIGIN; mounts auth.router; registers th...
    config/
      settings.py - typed env loaded from .env.example (DATABASE_URL, JWT_*, BCRYPT_ROUNDS, RESET_TOKEN_TTL_MINUTES,...
    db/
      database.py - SQLAlchemy engine/session from DATABASE_URL; per-request session dependency
      schema.sql - authoritative DDL copied from the design pack (users, password_resets, refresh_tokens)
    core/
      security.py - bcrypt hash/verify; SHA-256 token hashing; JWT encode/decode helpers
      rate_limit.py - login and forgot-password limiters (NFR-08)
      dependencies.py - get_current_user: validate the Bearer access token and load the User (401 on failure)
    auth/
      router.py - endpoints: register (POST /auth/register), login (POST /auth/login), refresh (POST /auth/refresh)...
      service.py - register (uniqueness + hash + issue tokens), authenticate, rotate/revoke refresh, issue/consume r...
      repository.py - data access for users, password_resets, refresh_tokens (mirrors schema.sql)
      schemas.py - Pydantic models = openapi.yaml component schemas (RegisterRequest, LoginRequest, AuthResponse, Us...
      validators.py - password policy + field validators emitting the exact messages/order from validation-rules.md
      tokens.py - access/refresh/reset creation, hashing, TTL selection (extended when rememberMe), rotation, revoc...
      emailer.py - sends the reset email via SMTP_*; builds the APP_BASE_URL/reset-password?token=... link
    models/
      user.py - users row mapping
      password_reset.py - password_resets row mapping
      refresh_token.py - refresh_tokens row mapping
    common/
      errors.py - error codes (VALIDATION_ERROR, INVALID_CREDENTIALS, EMAIL_TAKEN, INVALID_TOKEN, UNAUTHORIZED, RAT...
      responses.py - ErrorResponse envelope shaper { error: { code, message, details } }
  tests/
    test_register.py - success; duplicate email (409 EMAIL_TAKEN); weak password; mismatch; terms not accepted
    test_login.py - success; wrong password / unknown email both -> INVALID_CREDENTIALS; rate limit
    test_refresh_logout.py - rotate on refresh; revoke on logout; reuse of a revoked token -> 401
    test_forgot_reset.py - generic 202 ack; valid reset consumes the token; expired/used token -> INVALID_TOKEN
```

### Frontend

```text
auth-frontend/
  package.json - dependencies, scripts (dev, build, test, lint); react, react-dom, react-router-dom, vite, typescr...
  index.html - Vite entry; mounts #root and loads /src/main.tsx
  vite.config.ts - React plugin; dev proxy /api/v1 -> http://localhost:8000
  tsconfig.json - TypeScript strict configuration
  .env.example - environment template (VITE_API_BASE_URL)
  README.md - project overview, setup, and env variable docs
  src/
    main.tsx - bootstrap: React root wrapped in BrowserRouter + AuthProvider; imports styles/tokens.css
    App.tsx - route table: guest routes (/login /register /forgot-password /reset-password) under RequireGuest;...
    api/
      client.ts - fetch wrapper: base URL, Bearer header injection, ErrorResponse -> ApiError normalisation, silent...
      types.ts - TS mirrors of openapi.yaml schemas (User, AuthTokens, AuthResponse, RegisterRequest, LoginRequest...
      auth.ts - one function per operationId: register, login, logout, me, refresh, forgotPassword, resetPassword
    auth/
      AuthContext.tsx - AuthProvider + useAuth(): { user, isAuthenticated, isLoading, login, register, logout, refresh }
      RequireAuth.tsx - guard: redirect unauthenticated -> /login?next=<path> (FR-10)
      RequireGuest.tsx - guard: redirect authenticated -> /profile (FR-11)
      tokenStore.ts - access token in memory; refresh token via httpOnly cookie
    features/
      auth/
        components/
          AuthCard.tsx - centered card shell (ui.layout=centered-card)
          Branding.tsx - logo + wordmark above the card (ui.branding=true)
          TextField.tsx - labeled text/email input + error/hint wired via aria-describedby
          PasswordField.tsx - password input with a show/hide toggle button (aria-label)
          PasswordStrengthMeter.tsx - live checklist for the 4 active rules (>= 8, upper, lower, number) - no special-char rule
          Checkbox.tsx - labeled checkbox (Remember me, Accept Terms)
          SubmitButton.tsx - primary button with loading spinner + disabled/aria-busy state
          AlertBanner.tsx - success/error banner in an aria-live region
        hooks/
          useAuthForm.ts - controlled-form hook: field state, blur/submit validation, submit lifecycle
        pages/
          LoginPage.tsx - route /login: email + password, remember me, links to Register and Forgot Password
          RegisterPage.tsx - route /register: full name, email, password + strength meter, confirm, accept Terms
          ForgotPasswordPage.tsx - route /forgot-password: email only; enumeration-safe acknowledgement
          ResetPasswordPage.tsx - route /reset-password: reads ?token=; new password + confirm + strength meter
        validation.ts - client mirror of validation-rules.md (exact messages, same order; password policy from config)
    pages/
      ProfilePage.tsx - route /profile: protected; loads GET /auth/me and offers Log out
    styles/
      tokens.css - CSS custom properties mirroring design-tokens.json / tokens.json
      auth.css - auth card, fields, buttons, alerts, strength meter, and responsive rules
  tests/
    validation.test.ts - asserts the exact messages + rule order from validation-rules.md
    guards.test.tsx - RequireAuth / RequireGuest redirect behavior
```

## Getting started

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Postgres
- Docker & Docker Compose (optional)

### Backend

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
npm install
npm run dev
npm run build
npm run test
```

### With Docker

```bash
docker compose up --build
```

### Environment variables

Copy `.env.example` to `.env` and set:

- `DATABASE_URL`
- `SECRET_KEY`

## API reference

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/auth/register` | Create an account and sign in |
| `POST` | `/auth/login` | Sign in with email and password |
| `POST` | `/auth/refresh` | Exchange a refresh token for a new access token |
| `POST` | `/auth/logout` | Revoke the current refresh token |
| `GET` | `/auth/me` | Get the current authenticated user |
| `POST` | `/auth/forgot-password` | Request a password-reset email |
| `POST` | `/auth/reset-password` | Set a new password using a reset token |

## Screens & routes

| Screen | Route |
| --- | --- |
| Login | `/login` |
| Register | `/register` |
| Forgot Password | `/forgot-password` |
| Reset Password | `/reset-password` |
| Profile | `/profile` |
| Logout | `/logout` |

## Data model

- `users`
- `password_resets`
- `refresh_tokens`

## Testing

```bash
pytest
```

```bash
npm test
```

## Notes

- Stack: FastAPI (Python 3.12) behind a global /api/v1 prefix, PostgreSQL 16, JWT strategy (HS256 access token, 15 min) + rotating refresh tokens stored hashed.
- Endpoints match openapi.yaml exactly - one handler per operationId, same paths/methods/status codes; no extra endpoints.
- schema.sql is authoritative; repository.py and any migrations are generated from it and must not diverge.
- Every failure is shaped into the ErrorResponse envelope { error: { code, message, details } } with codes from validation-rules.md.
- Passwords are bcrypt-hashed (BCRYPT_ROUNDS >= 12); reset and refresh tokens are stored as SHA-256 hashes, never raw.
- Login and forgot-password are enumeration-safe (NFR-03) and rate-limited (NFR-08).
- NOT generated for this configuration: models/email_verification_token.py (verify_email=false), models/session.py (strategy=jwt is stateless), an oauth/ package (allow_social_login=false), and any username field (login.identifier=email).
