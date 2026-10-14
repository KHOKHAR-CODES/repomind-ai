# Repomind AI — One-Click Railway Deploy
# Source repo: Usama-Rasheed/lec_26/repomind-ai
# Date: 2026-10-14

## What this deploy does
- Deploys FastAPI backend (Python 3.11+) with PostgreSQL database
- Serves static frontend (HTML/CSS/JS) via backend or separate service
- Uses Railway's Nixpacks builder for zero-config Docker builds

## Quick deploy (single click from Railway)
1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Choose repository: `Usama-Rasheed` (or your repo name)
4. Select root directory: `lec_26/repomind-ai`
5. Click "Deploy"

## Railway Variables (add after deploy)
In Railway dashboard → Variables for backend service:

```
DATABASE_URL = postgresql://user:pass@host:5432/db  # Auto-provided by Railway DB
LLM_API_KEY = sk-...                              # Your OpenRouter / LLM key
LLM_BASE_URL = https://openrouter.ai/api/v1
LLM_MODEL = gpt-3.5-turbo
JWT_SECRET_KEY = <generate with: openssl rand -base64 48>
FRONTEND_ORIGIN = https://repomind-frontend.railway.app
CORS_ALLOW_ORIGINS = https://repomind-frontend.railway.app
ENVIRONMENT = production
PYTHONPATH = .
```

## Add PostgreSQL
In Railway dashboard:
- New → Database → Add PostgreSQL
- Wait for URL → copy to DATABASE_URL variable

## File changes made for deploy
- backend/Procfile — Railway process definition
- backend/railway.toml — build/deploy settings (updated)
- backend/app/core/config.py — default LLM settings + CORS
- backend/requirements.txt — added psycopg2-binary for PostgreSQL
- frontend/railway.toml — static site deploy config
- railway.toml (root) — multi-service config reference

## Database migration
Backend uses SQLAlchemy with conditional SQLite/PostgreSQL connect_args.
On first deploy with new DB, `Base.metadata.create_all()` creates tables.
No Alembic migration needed — schema is created automatically.

## Frontend integration options
A) Serve from backend (simplest):
   Add to backend/app/main.py:
   from fastapi.staticfiles import StaticFiles
   app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")

B) Separate Railway service (recommended for production):
   Add service from `frontend/` folder, set buildpack = Static
   Update frontend/index.html API base to backend URL

## Health check
After deploy: visit `https://YOUR-BACKEND.railway.app/api/health`
Expected: `{"status":"ok","service":"RepoMind AI"}`

## Security notes
- Do NOT commit `.env` with secrets — use Railway Variables only
- JWT_SECRET_KEY must be ≥32 bytes in production
- CORS origins must not contain wildcard `*`
- Rotate JWT_SECRET_KEY after first deploy if needed

## Troubleshooting
- `ModuleNotFoundError: app` → set PYTHONPATH=.
- `sqlite3.OperationalError` → DATABASE_URL not set to PostgreSQL
- `RuntimeError: JWT_SECRET_KEY must...` → add JWT_SECRET_KEY variable
- Frontend not loading → check FRONTEND_ORIGIN and CORS_ALLOW_ORIGINS