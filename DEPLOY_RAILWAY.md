# Railway Deploy — Repomind AI (One-Click Full Stack)
# Date: 2026-10-14
# Deploy backend + frontend + PostgreSQL from a single Railway project.

## Files Created / Updated

### 1. Backend deploy config
- backend/railway.toml  (updated with build + deploy + env)
- backend/Procfile      (updated: web / gunicorn or uvicorn)
- backend/nixpacks.toml (new — optional Python build config)
- backend/.env.production (new — production env template)

### 2. Database (SQLite -> PostgreSQL)
- backend/app/db/session.py  (conditional connect_args already present)
- backend/app/core/config.py (DATABASE_URL default updated to postgresql)
- Railway Variables: DATABASE_URL = postgresql://...

### 3. Frontend deploy
- frontend/railway.toml (updated for static site)
- frontend/index.html   (API_BASE updated to backend URL)

### 4. Root full-stack local deploy
- docker-compose.yml     (updated: backend + frontend + db)
- .env.production        (new root template)

---

## One-Click Railway Steps

1. Go to https://railway.app/new
2. Connect GitHub repo: Usama-Rasheed/lec_26/repomind-ai
3. Add PostgreSQL database service (Railway provides URL automatically)
4. Set backend Variables (copy from .env.production, fill secrets):
   - DATABASE_URL = <PostgreSQL URL from Railway>
   - JWT_SECRET_KEY = <32+ byte secret>
   - LLM_API_KEY = <your key>
   - FRONTEND_ORIGIN = https://repomind-frontend.railway.app
   - CORS_ALLOW_ORIGINS = https://repomind-frontend.railway.app
   - ENVIRONMENT = production
5. Deploy backend (Nixpacks, Python 3.11, requirements.txt)
6. Deploy frontend (static site, python -m http.server $PORT)
7. Update frontend/index.html API_BASE to match backend URL

---

## Key Settings Summary

| Service | File | Build | Deploy | Healthcheck |
|---------|------|-------|--------|-------------|
| backend | backend/railway.toml | nixpacks / pip | uvicorn app.main:app --host 0.0.0.0 --port $PORT | /api/health |
| frontend | frontend/railway.toml | nixpacks (static) | python -m http.server $PORT --directory . | / |
| db | Railway DB service | — | — | — |

For full-stack local: docker-compose up (postgreSQL + backend + frontend)
