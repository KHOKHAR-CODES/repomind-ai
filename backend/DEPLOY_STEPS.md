# Railway Deploy — Repomind AI (Step-by-Step)
# Date: 2026-10-14

## STEP 1 — Prepare repo / commit
# Make sure backend/app/db/session.py uses conditional connect_args (done)
# Make sure .env uses correct LLM_BASE_URL (done: openrouter.ai/api/v1)
# Add railway.toml if missing (created at backend/railway.toml)
git add -A
git commit -m "deploy: railway config + sqlite/postgres fix + light-rays"

## STEP 2 — Create Railway project
# Go to https://railway.app/new
# Click "Deploy from GitHub repo"
# Connect GitHub account → select Usama-Rasheed repo
# Set root directory: lec_26/repomind-ai/backend (or repo root if backend at root)

## STEP 3 — Add PostgreSQL (critical — prevents data loss on redeploy)
# In Railway dashboard → "New" → "Database" → "Add PostgreSQL"
# Wait for connection URL (e.g. postgresql://user:pass@host/db)
# Go to Variables → add DATABASE_URL = <that URL>

## STEP 4 — Set backend environment variables
# In Railway Variables for the backend service:
LLM_API_KEY = <from Railway Variables — do not commit secrets>
LLM_BASE_URL = https://openrouter.ai/api/v1
LLM_MODEL = gpt-3.5-turbo
JWT_SECRET_KEY = <generate new 32-byte secret, e.g. openssl rand -base64 48>
DATABASE_URL = <from Step 3>
FRONTEND_ORIGIN = https://repomind-frontend.railway.app (or your frontend URL)
CORS_ALLOW_ORIGINS = https://repomind-frontend.railway.app
ENVIRONMENT = production

## STEP 5 — Confirm build / start command
# railway.toml should contain:
# [deploy] startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
# If using Nixpacks / Docker: ensure requirements.txt is at backend root
# Build should install: uvicorn, fastapi, sqlalchemy, chromadb, httpx, pydantic-settings

## STEP 6 — Deploy backend
# Click "Deploy" in Railway
# Wait for build (pip install) + start
# Check logs for errors: if "ModuleNotFoundError: app", set PYTHONPATH=.
# Healthcheck: /api/health should return {"status":"ok"}

## STEP 7 — Deploy frontend (static HTML/CSS/JS)
# Option A (easiest — serve from backend):
# In app/main.py, add: app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")
# Then frontend is at same domain: https://repomind-backend.railway.app/
# Option B (separate): add new Railway service from frontend/ folder, buildpack Static
# Then set frontend service Variables / CNAME accordingly

## STEP 8 — Update frontend API base
# In frontend/index.html: change window.REPOMIND_API_BASE to backend URL
# Or set in script.js: API_BASE = "https://repomind-backend.railway.app"

## STEP 9 — Verify
# Open backend URL → should show API
# Open frontend URL → welcome panel with light-rays, stats, ask AI
# Check ask question → answer returns from backend (LLM_API_KEY configured)
# Check auth → login/signup works with PostgreSQL users

## STEP 10 — Post-deploy security
# Do NOT commit .env with secrets — use Railway Variables only
# Rotate JWT_SECRET_KEY after first deploy if needed
# Add .gitignore: .env, repomind.db, data/chroma_db/
