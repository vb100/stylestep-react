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
3. Linux VPS production mode

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

## 8) GitHub Checklist Before Deployment

Recommended repository scope:

- create a private GitHub repository for `react_version/`

Do not commit:

- `backend/.env`
- `backend/.venv/`
- `backend/db.sqlite3`
- `backend/media/`
- `backend/staticfiles/`
- `frontend/node_modules/`
- `frontend/dist/`

The project already includes:

- `react_version/.gitignore`
- `react_version/.dockerignore`
- `react_version/.env.example`
- `react_version/backend/.env.example`

## 9) Linux VPS Production Deployment

Production deployment uses:

- `docker-compose.prod.yml`
- `gunicorn` for Django
- `Caddy` as reverse proxy and static frontend server
- automatic HTTPS when `APP_DOMAIN` points to your VPS

This variant is intended for a plain Linux VPS where ports `80` and `443` are free.

### 9.1 Prepare DNS

In Hostinger DNS, point your domain to the VPS:

- `A` record for `@` -> your VPS public IP
- `A` record for `www` -> your VPS public IP

### 9.2 Open firewall ports

Public:

- `22`
- `80`
- `443`

Do not expose publicly:

- `5432`
- `8000`

If needed:

```bash
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
ufw status
```

### 9.3 Connect to the server

```bash
ssh root@YOUR_SERVER_IP
```

### 9.4 Install git if needed

```bash
apt update && apt install -y git
```

### 9.5 Clone the repository

```bash
mkdir -p /opt/stylestep
cd /opt/stylestep
git clone https://github.com/vb100/stylestep-react.git .
```

### 9.6 Create the root Compose environment file

This file is used by `docker-compose.prod.yml` for the public domain:

```bash
cd /opt/stylestep
cp .env.example .env
```

Edit `.env`:

```env
APP_DOMAIN=your-domain.lt
```

If DNS is not ready yet, use a temporary HTTP-only test value:

```env
APP_DOMAIN=http://YOUR_SERVER_IP
```

After DNS starts resolving correctly, change it back to:

```env
APP_DOMAIN=your-domain.lt
```

### 9.7 Create the Django backend environment file

```bash
cd /opt/stylestep/backend
cp .env.example .env
```

Edit `backend/.env` and set at least:

```env
DJANGO_SECRET_KEY=replace_with_a_long_random_secret_key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=your-domain.lt,www.your-domain.lt
DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.lt,https://www.your-domain.lt
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
TIME_ZONE=Europe/Vilnius

USE_SQLITE=False
POSTGRES_DB=ai_aprangos_asistentas
POSTGRES_USER=ai_aprangos_asistentas
POSTGRES_PASSWORD=replace_with_a_strong_db_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-mini
OPENAI_ENABLE_OUTFIT_IMAGE=True
OPENAI_IMAGE_MODEL=gpt-image-1
OPENAI_IMAGE_SIZE=1024x1024
```

Important:

- if a secret contains the `$` character, write it as `$$` inside `.env`
- `DJANGO_ALLOWED_HOSTS` must include the real public domain
- `DJANGO_CSRF_TRUSTED_ORIGINS` must include the HTTPS domain

### 9.8 Start the production stack

```bash
cd /opt/stylestep
docker compose -f docker-compose.prod.yml up -d --build
```

This starts:

- `db`
- `backend`
- `worker`
- `web`

### 9.9 Create the admin user

```bash
cd /opt/stylestep
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

### 9.10 Check logs and container state

```bash
cd /opt/stylestep
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs -f backend worker web
```

### 9.11 Open the site

If DNS is already pointing to the VPS:

- `https://your-domain.lt`
- `https://your-domain.lt/admin/`

If you are still testing by IP:

- `http://YOUR_SERVER_IP`

### 9.12 Update after a new GitHub push

```bash
cd /opt/stylestep
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## 10) Hostinger Docker + Traefik Deployment

If your Hostinger VPS was created from the `Docker and Traefik` template, do not use `docker-compose.prod.yml` directly.

Reason:

- Hostinger Traefik already listens on host ports `80` and `443`
- only one reverse proxy can own those ports
- your application should join the shared Traefik network instead of binding those ports itself

Hostinger documents this exact pattern for multiple Compose projects on one VPS:

- Traefik remains the single entry point on `80/443`
- your app is exposed through Docker labels
- your project joins the external `traefik-proxy` network

Source:

- https://www.hostinger.com/support/connecting-multiple-docker-compose-projects-using-traefik-in-hostinger-docker-manager/

### 10.1 Files to use on Hostinger

Use:

- `docker-compose.hostinger.yml`
- `deploy/caddy/Caddyfile.hostinger`
- `deploy/caddy/Dockerfile.hostinger`

### 10.2 Required DNS

Point both:

- `stylestep.lt`
- `www.stylestep.lt`

to your actual VPS IP.

### 10.3 Check that the Traefik network exists

```bash
docker network ls | grep traefik
```

Expected:

- `traefik-proxy`

If it does not exist, deploy the default Traefik project from Hostinger Docker Manager first.

### 10.4 Prepare environment files

Root compose env:

```bash
cd /opt/stylestep
cp .env.example .env
```

Set:

```env
APP_DOMAIN=stylestep.lt
```

Backend env:

```bash
cd /opt/stylestep/backend
cp .env.example .env
```

Set at least:

```env
DJANGO_SECRET_KEY=replace_with_a_long_random_secret_key
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=stylestep.lt,www.stylestep.lt
DJANGO_CSRF_TRUSTED_ORIGINS=https://stylestep.lt,https://www.stylestep.lt
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
TIME_ZONE=Europe/Vilnius

USE_SQLITE=False
POSTGRES_DB=ai_aprangos_asistentas
POSTGRES_USER=ai_aprangos_asistentas
POSTGRES_PASSWORD=replace_with_a_strong_db_password
POSTGRES_HOST=db
POSTGRES_PORT=5432

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-5-mini
OPENAI_ENABLE_OUTFIT_IMAGE=True
OPENAI_IMAGE_MODEL=gpt-image-1
OPENAI_IMAGE_SIZE=1024x1024
```

### 10.5 Start on Hostinger

```bash
cd /opt/stylestep
docker compose -f docker-compose.hostinger.yml up -d --build
```

### 10.6 Create the admin user

```bash
cd /opt/stylestep
docker compose -f docker-compose.hostinger.yml exec backend python manage.py createsuperuser
```

### 10.7 Check logs

```bash
cd /opt/stylestep
docker compose -f docker-compose.hostinger.yml ps
docker compose -f docker-compose.hostinger.yml logs -f backend worker web
```

### 10.8 Update after a new GitHub push

```bash
cd /opt/stylestep
git pull
docker compose -f docker-compose.hostinger.yml up -d --build
```

## 11) Production Notes

- local development still uses `docker-compose.yml`
- plain Linux VPS deployment uses `docker-compose.prod.yml`
- Hostinger `Docker and Traefik` template uses `docker-compose.hostinger.yml`
- `Caddy` serves the built React frontend and handles HTTPS automatically when the domain resolves to the VPS
- Django runs behind `gunicorn`
- uploaded files are stored in the Docker volume `backend_media`
- PostgreSQL data is stored in the Docker volume `postgres_data`
