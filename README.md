# Repo Mind AI

Repo Mind AI is a FastAPI-backed GitHub repository indexing and question-answering application. The frontend remains plain HTML, CSS, and vanilla JavaScript; there is no frontend framework or package-install step.

## Requirements

- Python 3.10 or newer and Git on the backend host.
- Node.js for the optional JavaScript syntax check.
- A configured embedding model/runtime from `backend/requirements.txt`.
- An LLM-compatible API key for generated answers. Repository retrieval without the key is not presented as a generated answer.

## Configure and run

1. From `backend/`, create a virtual environment and install the pinned/runtime requirements listed in `requirements.txt`.
2. Copy `.env.example` to `.env`. Set `JWT_SECRET_KEY` to a unique random secret of at least 32 bytes in production; for example, generate it with Python `secrets.token_urlsafe(48)`. Development can start without it, but uses an ephemeral key and existing sessions will expire on restart.
3. Set `LLM_API_KEY`, and set `LLM_BASE_URL`/`LLM_MODEL` if using a compatible provider other than the defaults. Keep credentials server-side.
4. Set `FRONTEND_ORIGIN` to the exact origin that serves the frontend (default `http://localhost:5173`). Additional exact origins may be listed in `CORS_ALLOW_ORIGINS`, comma-separated. Wildcard origins are rejected when credentialed CORS is enabled.
5. Start the API from `backend/`: `uvicorn main:app --reload` (API defaults to port 8000).
6. In another terminal, run `python -m http.server 5173` from `frontend/` and open `http://localhost:5173`.

The frontend uses `http://localhost:8000` when served on port 5173. For another deployment, set `window.REPOMIND_API_BASE` in `frontend/index.html` to the backend base URL and allow the frontend's exact origin in backend CORS settings. HTTPS is required in production; serve both sides over HTTPS and configure the deployment's trusted origin.

## Existing and added API contracts

All user/repository/chat operations require `Authorization: Bearer <access_token>` except signup, login, and health. Request/response shapes remain JSON.

- `GET /api/health`
- `POST /api/auth/signup` — `{ "username", "email", "password" }`
- `POST /api/auth/login` — `{ "email", "password" }` → `{ "access_token", "token_type" }`
- `GET /api/auth/me`
- `GET/POST /api/repositories` — create with `{ "repo_url", "branch" }`; indexing is synchronous and the response reports the actual indexing status and counts.
- `GET /api/repositories/{repo_id}`
- `POST /api/repositories/{repo_id}/reindex`
- `DELETE /api/repositories/{repo_id}`
- `POST /api/repositories/{repo_id}/ask` — `{ "question", "top_k": 1..10, "chat_id"? }` → answer, snippets, references, sources. A missing/unavailable LLM is returned as a service error, not fabricated answer text.
- `GET /api/chats?repository_id=<id>` — the current user's recent saved conversations (up to 100).
- `GET /api/chats/{chat_id}` — owner-checked message history and citations.
- `PATCH /api/chats/{chat_id}` — `{ "title": "..." }`.
- `DELETE /api/chats/{chat_id}`.
- `GET /api/users/stats` — authenticated counts; the dashboard uses this endpoint and never substitutes demo statistics.

The available GitHub workflow clones public HTTPS `github.com/owner/repository` URLs. This project does not include GitHub OAuth/private-repository authorization; do not enter GitHub tokens in the browser. Private-repository access would require a separate server-side GitHub App/OAuth implementation.

## Verification

- Frontend syntax: `node --check frontend/script.js` (or `npm run check` from `frontend/`; npm dependencies are not required).
- Backend tests: from `backend/`, `python -m pytest`.
- Backend startup provides OpenAPI documentation at `/docs`.

Indexing is currently synchronous, so repository create/reindex can take several minutes. The UI waits for the real endpoint result and never invents asynchronous progress. AI/GitHub end-to-end checks require valid server configuration, accessible repositories, installed model dependencies, and a running backend.


## Fast local indexing (CPU / open source)

The backend indexes only text-like files from an explicit source-extension allowlist; dependency/build directories, binary-looking files, lockfiles, empty files and files over 2 MiB are skipped safely. Chunks use `RecursiveCharacterTextSplitter` with 1,200-character size and 150-character overlap. Embeddings use FastEmbed's ONNX Runtime CPU backend with `sentence-transformers/all-MiniLM-L6-v2`; vectors are generated in batches of 64 and written to Chroma in batches of up to 300. The first run may download/cache the model. Indexing time depends on repository size, disk speed, CPU, and whether the model is already cached; no fixed 1–3 minute runtime is guaranteed for every machine/repository.

Install backend dependencies, then from `backend/` run:

```bash
pip install -r requirements.txt
python scripts/index_github_repo.py https://github.com/owner/repository --branch main
```

The script accepts public HTTPS GitHub repositories only and writes to the configured local Chroma store. Set `EMBEDDING_MODEL` or `CHROMA_DB_PATH` in the backend environment to override defaults. Stage timings for scan/filter, splitting, embeddings, and Chroma persistence are printed to the terminal. The FastAPI repository routes use the same indexing service.
