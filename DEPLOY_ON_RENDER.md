# Deploying Flight-Booking-Simulator on Render

This document explains two safe options to deploy the project on Render: (A) quick Docker-based deploys that match the repository layout, and (B) a recommended production approach using Render's managed Postgres database (requires small code changes or migration to SQLAlchemy).

Quick notes from the repository:
- Backend: Flask app in `backend/`, `backend/Dockerfile` starts the app with Gunicorn and runs `db_init.py` if needed. Uses SQLite by default (`flights.db`).
- Frontend: Vite + React in `frontend/`, `frontend/Dockerfile` builds and serves via nginx.
- `schema.sql` and `backend/db_init.py` create and populate the SQLite DB.

Option A — Fast (Docker) — good for demos
1. In Render, create a new **Web Service** and choose the Docker option.
2. Point the service to this GitHub repo and branch (e.g. `main`).
3. Set the **Dockerfile path** to `backend/Dockerfile` and the **root** to project root.
4. Add environment variables in Render (Settings → Environment):
   - `SECRET_KEY` — set a random secret for session cookies
   - `FRONTEND_ORIGIN` — your frontend origin if needed for CORS
   - SMTP settings (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`) if you want real emails
5. Deploy. The backend Dockerfile runs `python db_init.py || true` then starts gunicorn, so the SQLite DB will be initialized on the instance.

Notes for Option A:
- Using SQLite inside a Render Web Service is fine for demos, but the file is stored on the instance and may not persist through some redeploy workflows or scaling to multiple instances. For production, use a managed Postgres database.

Option B — Recommended (managed Postgres)
1. Create a new **Postgres** instance on Render (Dashboard → New → Database → PostgreSQL). Choose a plan (Starter is fine for testing).
2. After the database is created, copy its `DATABASE_URL` connection string.
3. Update the backend to use Postgres:
   - Short path: switch the backend to SQLAlchemy and read `DATABASE_URL` from env. This requires code changes—ask me and I can implement them.
   - Alternative (quick migration): keep using SQLite for now, but use Postgres for persistence later.
4. In Render, create a Web Service for the backend (Docker or Python environment). Add env var `DATABASE_URL` with the value from step 2 and `SECRET_KEY`.
5. Create a Web Service for the frontend (recommended as a Static Site or Docker):
   - If you want Render to build the frontend: create a **Static Site** service with `Root Directory` = `frontend`, Build Command: `npm ci && npm run build`, Publish Directory: `dist`. Set env var `VITE_API_URL` to your backend URL (e.g. `https://your-backend.onrender.com`).
   - Or use the `frontend/Dockerfile` in a Docker Web Service.

Sample render.yaml (illustrative, adapt in Render UI or use it as a starting point):
```yaml
services:
  - type: web
    name: flight-backend
    env: docker
    dockerfilePath: backend/Dockerfile
    branch: main
    envVars:
      - key: SECRET_KEY
        generator: secret
      - key: FRONTEND_ORIGIN
        value: https://<your-frontend-url>

  - type: static
    name: flight-frontend
    env: static
    root: frontend
    buildCommand: npm ci && npm run build
    staticPublishPath: dist
    branch: main

databases:
  - name: flight-db
    engine: postgresql
    plan: starter
```

Checklist of env vars to set on Render
- `SECRET_KEY` (required)
- `FRONTEND_ORIGIN` (optional)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` (optional)
- `DATABASE_URL` (if using Postgres)
- On the frontend service: `VITE_API_URL` pointing to the backend

Commands and verification
- After backend deploy (Docker/Gunicorn): visit `https://<backend-service>.onrender.com/` to see the API root JSON.
- If using SQLite: you can run `python backend/db_init.py` locally and push the generated `backend/flights.db` into the repo for a quick demo, but that is not recommended for source control.

Next steps I can take for you (choose one):
- Create a `render.yaml` in the repo exactly matching Render's schema and the services above.
- Modify the backend to support Postgres via SQLAlchemy and use `DATABASE_URL`.
- Add a small script / startup step that performs DB migrations on startup when Postgres is used.

If you'd like, tell me which option you prefer (A = fast Docker demo, B = Postgres production), and I'll implement the required repo changes.
