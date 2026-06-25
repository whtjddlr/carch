# CARCH Demo Runbook

This guide is for running the same demo scenario on another computer after cloning the Git repository.

## What Git Includes

Git contains:

- Django and Vue source code
- migrations
- demo seed source data
- curated frontend card images
- brand assets
- local setup docs

Git does not contain:

- `backend/db.sqlite3`
- `.env` files
- the full card catalog SQLite database
- the full card image bundle
- real API keys

## Required External Bundle

For the full card search, card images, and recommendation screens, copy this folder to the presentation computer:

```txt
pjt-08-db-bundle-20260529/
```

Recommended location:

```txt
finalpjt/pjt-08-db-bundle-20260529/
```

The folder should contain:

```txt
card_master_api.sqlite
card_images/
discontinued_card_images/
```

If it is stored elsewhere, set these values in `backend/.env`:

```env
CARD_DATA_BUNDLE_DIR=C:/path/to/pjt-08-db-bundle-20260529
CARD_MASTER_DB=C:/path/to/pjt-08-db-bundle-20260529/card_master_api.sqlite
CARD_IMAGE_DIR=C:/path/to/pjt-08-db-bundle-20260529/card_images
```

## One-Time Setup

From the repository root:

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

For a Nam Juhyun demo login, set these values in `backend/.env`:

```env
DEV_AUTO_LOGIN_ENABLED=true
DEV_ADMIN_EMAIL=demo@carch.local
DEV_ADMIN_NAME=남주현
```

Install dependencies:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo --strict-card-bundle
```

In another terminal:

```powershell
cd frontend
npm install
```

## Start The Demo

Terminal 1, backend:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python manage.py runserver 127.0.0.1:8000
```

Terminal 2, AI proxy:

```powershell
.\scripts\run_ai_proxy.ps1
```

Terminal 3, frontend:

```powershell
cd frontend
npm.cmd run dev
```

Open:

```txt
http://127.0.0.1:5173/cards
```

## Demo Account

If dev auto-login is unavailable, use email login:

```txt
email: demo@carch.local
password: Carchdemo123!
```

The password is set by:

```powershell
python manage.py seed_demo
```

To choose another password:

```powershell
python manage.py seed_demo --demo-password "YourPassword123!"
```

## Pre-Presentation Health Check

Run these before presenting:

```powershell
cd backend
python manage.py check
python manage.py seed_demo --strict-card-bundle
```

```powershell
cd frontend
npm.cmd run build
```

Then verify:

```txt
http://127.0.0.1:8000/api/health/
http://127.0.0.1:8100/health
http://127.0.0.1:5173/cards
```

## If The Full Card Bundle Is Missing

The app may still open with frontend curated images, but these parts can be incomplete:

- full card search
- card detail from the backend catalog
- backend-served card images
- recommendation output that depends on full catalog data

For an actual presentation, bring the card bundle separately through USB, shared drive, or Git LFS.
