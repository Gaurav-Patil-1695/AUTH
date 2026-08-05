# auth-frontend

React + TypeScript frontend for the Auth Starter project. Provides email-based authentication flows: register, login, forgot password, reset password, and a protected profile page.

---

## Tech Stack

- **React 18** with function components
- **TypeScript 5** (strict mode)
- **Vite 5** (dev server + bundler)
- **React Router v6** (client-side routing)
- **Vitest** (unit tests)
- **ESLint** (React + hooks + TypeScript rules)

---

## Prerequisites

- Node.js >= 18
- npm >= 9
- The `auth-backend` service running on `http://localhost:8000` (see `../auth-backend/README.md`)

---

## Setup

1. **Clone the repository** (if you have not already):

   ```bash
   git clone <repo-url>
   cd auth-frontend
   ```

2. **Install dependencies**:

   ```bash
   npm install
   ```

3. **Configure environment variables**:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` as needed (see [Environment Variables](#environment-variables) below).

4. **Start the development server**:

   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:5173`.

   The Vite dev server proxies all `/api/v1` requests to `http://localhost:8000`, so no CORS configuration is needed during local development.

---

## Available Scripts

| Script          | Description                                          |
|-----------------|------------------------------------------------------|
| `npm run dev`   | Start the Vite development server with HMR           |
| `npm run build` | Type-check and produce a production build in `dist/` |
| `npm run test`  | Run unit tests with Vitest                           |
| `npm run lint`  | Run ESLint across `src/` (zero warnings policy)      |

---

## Environment Variables

All environment variables consumed by the frontend must be prefixed with `VITE_` so that Vite exposes them to the browser bundle.

Copy `.env.example` to `.env` and fill in the values:

```dotenv
# .env.example
VITE_API_BASE_URL=http://localhost:8000
```

### Variable Reference

| Variable             | Required | Default                   | Description                                                                                          |
|----------------------|----------|---------------------------|------------------------------------------------------------------------------------------------------|
| `VITE_API_BASE_URL`  | Yes      | `http://localhost:8000`   | Base URL of the `auth-backend` service. Used by the API client in `src/api/auth.ts` for all requests. In production, set this to your deployed backend URL (e.g. `https://api.example.com`). |

> **Note:** During local development the Vite proxy (`vite.config.ts`) forwards `/api/v1/*` to `http://localhost:8000`, so `VITE_API_BASE_URL` only needs to be set explicitly for production builds or when running the compiled `dist/` output outside of the Vite dev server.

---

## Project Structure

```
auth-frontend/
├── index.html                   # HTML entry point
├── vite.config.ts               # Vite configuration (proxy, plugins)
├── tsconfig.json                # TypeScript compiler options
├── package.json                 # Dependencies and scripts
├── .env.example                 # Environment variable template
└── src/
    ├── main.tsx                 # React app entry point
    ├── api/
    │   └── auth.ts              # Auth API client (login, register, me, logout, refresh, forgotPassword, resetPassword)
    ├── context/
    │   └── AuthContext.tsx      # AuthContext + AuthProvider (user, isAuthenticated, isLoading)
    ├── hooks/
    │   └── useAuthForm.ts       # Controlled form hook with client-side validation
    ├── features/
    │   └── auth/
    │       └── pages/
    │           ├── LoginPage.tsx          # /login
    │           ├── RegisterPage.tsx       # /register
    │           ├── ForgotPasswordPage.tsx # /forgot-password
    │           └── ResetPasswordPage.tsx  # /reset-password
    ├── pages/
    │   └── ProfilePage.tsx      # /profile (protected)
    ├── components/
    │   ├── RequireAuth.tsx      # Route guard — redirects unauthenticated users to /login
    │   └── RequireGuest.tsx     # Route guard — redirects authenticated users to /profile
    └── styles/
        └── tokens.css           # CSS custom properties from design tokens
```

---

## Authentication Flows

| Screen                  | Route              | Description                                                   |
|-------------------------|--------------------|---------------------------------------------------------------|
| Register                | `/register`        | Create a new account with full name, email, and password      |
| Login                   | `/login`           | Sign in with email and password; supports remember-me         |
| Forgot Password         | `/forgot-password` | Request a password-reset email                                |
| Reset Password          | `/reset-password`  | Set a new password using the token from the reset email       |
| Profile *(protected)*   | `/profile`         | View the authenticated user's profile; accessible via `GET /auth/me` |

All API calls go through `src/api/auth.ts` which maps to these backend endpoints:

| Function          | Method | Path                      |
|-------------------|--------|---------------------------|
| `login`           | POST   | `/auth/login`             |
| `register`        | POST   | `/auth/register`          |
| `forgotPassword`  | POST   | `/auth/forgot-password`   |
| `resetPassword`   | POST   | `/auth/reset-password`    |
| `me`              | GET    | `/auth/me`                |
| `logout`          | POST   | `/auth/logout`            |
| `refresh`         | POST   | `/auth/refresh`           |

---

## Production Build

```bash
npm run build
```

The optimised static files are output to `dist/`. Serve them with any static file host (Nginx, Caddy, S3 + CloudFront, Vercel, etc.).

Ensure `VITE_API_BASE_URL` is set to your production backend URL before building:

```bash
VITE_API_BASE_URL=https://api.example.com npm run build
```

---

## Running with Docker Compose

The easiest way to run the full stack (frontend + backend + database) together is via the root `docker-compose.yml`:

```bash
# from the repository root
docker compose up --build
```

See the root `README.md` and `docker-compose.yml` for full details.

---

## Linting and Type Checking

```bash
# Lint
npm run lint

# Type-check (no emit)
npx tsc --noEmit
```

The project enforces strict TypeScript (`strict: true`, `noImplicitAny`, `strictNullChecks`, etc.) and zero ESLint warnings.

---

## Testing

```bash
npm run test
```

Unit tests (Vitest) cover the client-side validation module and route guards. Tests are deterministic and do not depend on wall-clock time or random values.
