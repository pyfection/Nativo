# Deployment

Production stack: **Neon** (Postgres) + **Fly.io** (FastAPI backend) + **Cloudflare Pages** (React frontend). All on free tiers.

## 1. Database — Neon

1. Create a project at <https://console.neon.tech>. Pick the region nearest your Fly region (the backend ↔ DB round-trip dominates latency).
2. From the dashboard, grab **two** connection strings:
   - **Pooled** (`...-pooler...`) — for the backend's app traffic. Use this as `DATABASE_URL` in Fly secrets.
   - **Direct** (no pooler) — for one-shot tasks like `alembic upgrade head`. Pooled connections don't support prepared-statement-heavy workloads cleanly; migrations are safer over direct.
3. Create a `dev` branch for local work: `Branches → New branch → from main`. You get a separate connection string with its own data; resetting/dropping the branch never touches prod.

### Local dev against a Neon branch

```bash
# in backend/.env (gitignored)
DATABASE_URL=postgresql://...@ep-...-dev.eu-central-1.aws.neon.tech/nativo?sslmode=require
SECRET_KEY=...        # openssl rand -hex 32
```

Then `uv run alembic -c backend/alembic.ini upgrade head` and you're working against an isolated copy of prod schema (empty unless you seed it).

### Local dev with disposable Docker Postgres

Skip Neon entirely for offline work:

```bash
docker compose -f docker-compose.dev.yml up db   # just the postgres service
# backend/.env points at localhost:5432
```

## 2. Backend — Fly.io

Prerequisites: `flyctl` installed, `fly auth login` done.

```bash
# First time only — provisions the app from fly.toml
fly launch --copy-config --no-deploy

# Required secrets
fly secrets set \
  DATABASE_URL="postgresql://...@ep-...-pooler.../nativo?sslmode=require" \
  SECRET_KEY="$(openssl rand -hex 32)" \
  BACKEND_CORS_ORIGINS='["https://nativo.pages.dev","https://nativo.example"]'

# Deploy
fly deploy
```

Notes:
- `fly.toml` sets `release_command = "alembic ... upgrade head"`. It runs before traffic swaps, so a bad migration fails the deploy instead of half-applying.
- `auto_stop_machines = "stop"` + `min_machines_running = 0` is free-tier friendly: the VM idles to sleep, ~5–10s cold start on next request. Set `min_machines_running = 1` if that's painful.
- `shared-cpu-1x` / 256 MB is enough for low traffic; bump if you see OOMs.
- File uploads (`backend/uploads/`) are **ephemeral** without a Fly Volume. Either attach a volume (`fly volumes create nativo_uploads --size 1`) and mount it, or move uploads to object storage (R2, S3) before you ship audio at scale. Documented as TODO.

### CI deploy (optional)

`gh secret set FLY_API_TOKEN -b "$(fly auth token)"` then add `.github/workflows/fly.yml`:

```yaml
on:
  push:
    branches: [master]
    paths: ['backend/**', 'pyproject.toml', 'uv.lock', 'Dockerfile', 'fly.toml']
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        env: { FLY_API_TOKEN: '${{ secrets.FLY_API_TOKEN }}' }
```

## 3. Frontend — Cloudflare Pages

Dashboard → **Workers & Pages → Create → Connect to Git → pick this repo.**

Build settings:

| Field | Value |
| --- | --- |
| Production branch | `master` |
| Framework preset | Vite |
| Build command | `cd frontend && npm install && npm run build` |
| Build output directory | `frontend/dist` |
| Root directory | *(leave blank)* |
| Node version | `20` (set in **Environment variables** as `NODE_VERSION=20`) |

Environment variables (Production):

| Key | Value |
| --- | --- |
| `VITE_API_URL` | `https://nativo-backend.fly.dev` (your Fly hostname) |
| `NODE_VERSION` | `20` |

Pages will deploy on every push to `master`. PR previews work automatically with their own `*.pages.dev` URL — useful for reviewing UI changes.

### CORS

The Fly secret `BACKEND_CORS_ORIGINS` must list your Pages hostnames, including any preview branch you want to hit the API from. The simplest pattern early on is to include `https://*.nativo.pages.dev` once Cloudflare supports wildcards; until then, add each preview URL or keep `["*"]` and rely on JWT auth to gate writes.

## 4. Live URLs

| Service | URL |
| --- | --- |
| Backend (Fly) | <https://nativo-api.fly.dev> |
| Frontend (Cloudflare Pages) | <https://nativo-4z0.pages.dev> |
| DB (Neon, project `sparkling-wind-14855455`) | `ep-misty-star-ajtgmxpd.c-3.us-east-2.aws.neon.tech` |

End-to-end smoke:

```bash
curl -fsS https://nativo-api.fly.dev/health                  # {"status":"healthy"}
curl -fsS https://nativo-api.fly.dev/api/v1/languages/       # []  (empty until seeded)
```

Open <https://nativo-4z0.pages.dev> and confirm the page loads. The DB has no data yet — the languages list will be empty. Seed by either (a) running `seed_dev_postgres_db.py` against the prod Neon connection, or (b) creating entries via the admin UI at <https://nativo-api.fly.dev/admin> (needs a superuser; use `backend/create_admin.py`).

If the page errors with "Failed to load languages", check the browser console: usually wrong `VITE_API_URL` (rebuild Pages with the right value) or a CORS rejection (update `BACKEND_CORS_ORIGINS` via `fly secrets set`).

## 5. Costs as you grow

- Neon free tier: 0.5 GB storage, 1 project, 10 branches. Bump to the $19/mo plan around when storage or branch count gets tight.
- Fly free allowance: ~3 shared-cpu-1x VMs × 256 MB, 3 GB volume, 160 GB outbound. Audio at scale will hit outbound before anything else — front it with R2 + a CDN once that matters.
- Cloudflare Pages: free for most realistic traffic. No hard ceiling for a project like this.
