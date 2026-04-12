# AI aprangos asistentas - React Version

This folder contains a React-based version of the project that keeps the same core workflow and AI logic as the original Django template app:

- upload a clothing photo
- choose season / occasion / style from DB-backed reference data
- save original + optimized image files
- run asynchronous OpenAI styling analysis
- poll request status
- show detected items, 3 outfit options, purchase suggestions, advice, and the generated outfit image

## Architecture

This version uses:

- `frontend/`: React + Vite + TypeScript
- `backend/`: Django API + Django admin
- `backend/stylist/tasks.py`: DB-backed async worker logic
- `backend/stylist/management/commands/run_worker.py`: long-running worker process
- `backend/stylist/management/commands/cleanup_media.py`: manual cleanup command

Important difference from the original Django version:

- No `Celery`
- No `Redis`
- Async processing is handled by a Django worker process that polls queued DB rows

That makes the project easier to run from a terminal on macOS and easier to package for Windows.

## Folder Layout

```text
react_version/
  README.md
  docker-compose.yml
  frontend/
  backend/
  infra/
```

## Runtime Modes

There are two supported ways to run this version:

1. macOS native terminal mode, no Docker required
2. Windows Docker mode, recommended when Docker is available

## 1) macOS Setup, No Docker

### 1.1 Install system tools

If needed:

```bash
brew install python@3.11 node
```

SQLite is used by default on macOS in this React version, so PostgreSQL is not required for the first local run.

### 1.2 Configure backend environment

```bash
cd react_version/backend
cp .env.example .env
```

Edit `.env` and set at least:

- `OPENAI_API_KEY=...`
- `DJANGO_SECRET_KEY=...`

Important:

- after creating or changing `backend/.env`, restart both Django processes
- that means restarting `python3 manage.py runserver` and `python3 manage.py run_worker`
- `npm run dev` does not read backend secrets and does not reload backend environment variables

Generate a Django secret key if needed:

```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 1.3 Install backend dependencies

```bash
cd react_version/backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

### 1.4 Prepare the database and admin

```bash
cd react_version/backend
source .venv/bin/activate
python3 manage.py migrate
python3 manage.py createsuperuser
```

### 1.5 Run the backend API

Terminal 1:

```bash
cd react_version/backend
source .venv/bin/activate
python3 manage.py runserver
```

### 1.6 Run the async worker

Terminal 2:

```bash
cd react_version/backend
source .venv/bin/activate
python3 manage.py run_worker
```

Notes:

- This worker continuously polls for `QUEUED` requests.
- It also runs media cleanup periodically.
- No Celery or Redis process is needed.

### 1.7 Run the React frontend

Terminal 3:

```bash
cd react_version/frontend
npm install
npm run dev
```

### 1.8 Open the app

- React app: `http://127.0.0.1:5173/`
- Django admin: `http://127.0.0.1:8000/admin/`
- API health: `http://127.0.0.1:8000/api/health/`

## 2) Windows Setup, Docker Mode

This is the recommended Windows path when Docker is allowed.

### 2.1 Install Docker Desktop

Install Docker Desktop for Windows and make sure it is running.

### 2.2 Configure backend environment

In `react_version/backend` create `.env`:

PowerShell:

```powershell
Copy-Item .env.example .env
```

Then edit `react_version/backend/.env` and set:

- `OPENAI_API_KEY=...`
- `DJANGO_SECRET_KEY=...`

You do not need to set PostgreSQL host manually for Docker mode. `docker-compose.yml` overrides that to use the Postgres container.

Important for Docker on Windows:

- if `DJANGO_SECRET_KEY` contains the `$` character, replace each `$` with `$$` inside `backend/.env`
- otherwise Docker Compose may try to interpret part of the secret as an environment variable and show warnings like `variable is not set`

### 2.3 Start the full stack

From the `react_version` folder:

```powershell
docker compose up --build
```

This starts:

- React frontend
- Django backend API
- DB-backed worker
- PostgreSQL

### 2.4 Create an admin user

In a second PowerShell window:

```powershell
cd react_version
docker compose exec backend python manage.py createsuperuser
```

### 2.5 Open the app

- React app: `http://127.0.0.1:5173/`
- Django admin: `http://127.0.0.1:8000/admin/`
- API health: `http://127.0.0.1:8000/api/health/`

## 3) Workflow Summary

The runtime flow stays the same as the original solution:

1. User uploads image and submits preferences
2. Backend validates and stores the original image
3. Backend creates an optimized image copy
4. Request row is created with status `QUEUED`
5. Worker claims the request and marks it `RUNNING`
6. OpenAI styling analysis runs
7. OpenAI outfit image generation runs
8. Request is stored as `DONE` or `FAILED`
9. React frontend polls and renders the final result

## 4) Reference Data and Admin

Season / Occasion / Style remain editable in Django admin:

- `Season`
- `Occasion`
- `StyleTag`

Open:

- `http://127.0.0.1:8000/admin/`

Seeded values still come from migrations in `backend/stylist/migrations/`.

## 5) Cleanup

Manual cleanup:

macOS or Docker container:

```bash
python3 manage.py cleanup_media --days 7
```

If using Docker:

```powershell
docker compose exec backend python manage.py cleanup_media --days 7
```

The worker also performs periodic cleanup automatically based on:

- `MEDIA_CLEANUP_DAYS`
- `WORKER_CLEANUP_INTERVAL_HOURS`

## 6) Optional PostgreSQL on macOS

If you want macOS local development to use PostgreSQL instead of SQLite:

1. Install PostgreSQL locally
2. Create a database and user
3. Update `backend/.env`:

```env
USE_SQLITE=False
POSTGRES_DB=ai_aprangos_asistentas
POSTGRES_USER=ai_aprangos_asistentas
POSTGRES_PASSWORD=change_me
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

Then run:

```bash
cd react_version/backend
source .venv/bin/activate
python3 manage.py migrate
```

## 7) Notes

- The React app talks to Django through `/api/...`
- In local development, Vite proxies `/api`, `/admin`, and `/media` to Django
- The generated outfit image still uses the uploaded clothing photo as a reference input when possible
- If the worker is not running, requests will remain in `QUEUED`
