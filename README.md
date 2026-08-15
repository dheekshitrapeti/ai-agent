# AI Workspace Assistant — Clean Phase 2

Phase 2 foundation for a Slack + Gmail + Google Drive activity dashboard.

## Stack

- Next.js + TypeScript + Tailwind CSS
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Docker Compose (optional)

## Backend without Docker

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Set `DATABASE_URL` in `backend/.env` to your PostgreSQL database.

Then:

```bash
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Check:

- http://127.0.0.1:8000/health
- http://127.0.0.1:8000/docs

## Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

Open http://localhost:3000

## Docker option

If Docker Desktop is installed:

```bash
docker compose up -d postgres
```

Then the default `DATABASE_URL` works.

## SQLAlchemy/Alembic

Models:

- `users`
- `integrations`
- `activities`

The schema uses timezone-aware `DateTime` fields and indexes.

Create a migration after model changes:

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## Phase 3

Add secure server-side OAuth for Slack, Gmail and Google Drive.
Provider tokens must never be exposed to the browser.
