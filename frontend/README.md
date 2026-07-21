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

## Local development

```powershell
Copy-Item .env.example .env.local
npm run dev
```

Open `http://localhost:3000`.

The Stage 20A dashboard uses polished demonstration data while the
authentication and live API integration are added in Stage 20B.

## Backend development setting

The backend `.env` must allow the frontend origin:

```dotenv
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

Restart the FastAPI backend after changing its environment.

## Validation

```powershell
npm run lint
npm run typecheck
npm run build
```
