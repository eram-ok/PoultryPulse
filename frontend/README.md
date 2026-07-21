# PoultryPulse Frontend

Modern Next.js App Router frontend for PoultryPulse.

## Stack

- Next.js App Router
- TypeScript
- Tailwind CSS
- shadcn/ui with Radix primitives
- Geist typography
- Lucide icons
- Recharts
- next-themes

## Stage 20B security model

The browser communicates with same-origin Next.js Route Handlers. Access and
refresh tokens are stored only in HttpOnly cookies and are never written to
localStorage or exposed to client JavaScript.

The Next.js backend-for-frontend:

- signs users in through FastAPI
- rotates refresh tokens after an expired access token
- forwards authorized API requests
- rejects cross-origin state-changing requests
- clears cookies on logout or invalid sessions
- protects application routes through `src/proxy.ts`

## Local development

Create the local environment file:

```powershell
Copy-Item .env.example .env.local
```

Start FastAPI on port 8000, then run:

```powershell
npm run dev
```

Open `http://localhost:3000`.

## Validation

```powershell
npm run lint
npm run typecheck
npm run build
```
