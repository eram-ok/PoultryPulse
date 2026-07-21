# Stage 20B — Authentication and Live Dashboard

Stage 20B connects the Stage 20A interface to the committed FastAPI backend.

## Security architecture

- Next.js Route Handlers operate as a same-origin backend-for-frontend.
- Access and refresh tokens are stored in HttpOnly cookies.
- Browser JavaScript never reads or stores authentication tokens.
- Cookies use `SameSite=Lax`, an explicit path, and secure transport in
  production.
- State-changing Next.js API requests verify the browser origin.
- An expired access token triggers one refresh-token rotation and one retry.
- Invalid sessions clear both cookies and return the user to the login page.
- `src/proxy.ts` performs an optimistic cookie check before protected pages
  render.
- Protected layouts still validate the access token against FastAPI.

## User experience

- Modern responsive sign-in screen
- Required and voluntary password-change workflow
- Real user name, initials, role, and farm identity
- Permission-aware sidebar, mobile menu, command palette, and quick actions
- Secure logout
- Expired-session and backend-unavailable handling

## Live dashboard

The dashboard now reads:

- `GET /reports/dashboard`
- `GET /reports/trends`
- `GET /reports/alerts`
- `GET /alerts/counts`
- `GET /auth/me`
- `GET /farms/{farm_id}`

Demonstration values are no longer used by the dashboard. Cards, charts,
inventory balances, flock-health indicators, alerts, and operational summaries
are derived from authenticated farm data.

## Environment

```dotenv
POULTRYPULSE_API_BASE_URL=http://127.0.0.1:8000/api/v1
AUTH_COOKIE_SECURE=false
AUTH_REFRESH_COOKIE_MAX_AGE_SECONDS=2592000
AUTH_BACKEND_TIMEOUT_MS=10000
```

Use `AUTH_COOKIE_SECURE=true` only when the frontend is served over HTTPS.

## Validation

```powershell
npm run lint
npm run typecheck
npm run build
```

No backend migration or new npm dependency is required.
