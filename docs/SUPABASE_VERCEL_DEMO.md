# Supabase + Vercel Demo Setup

This setup is for a shareable CARCH demo:

- Supabase Postgres stores Django app data and the full card catalog.
- Supabase Storage stores card image files.
- Vercel project 1 serves the Django API from `backend/`.
- Vercel project 2 serves the Vue app from `frontend/`.

## Supabase

Project:

```txt
dpagwiogflprfscztxzg
```

The project has these Supabase resources:

- Public schema card catalog tables.
- Public schema Django demo data tables.
- Public Storage bucket: `card-images`.

Supabase API keys do not replace the Postgres database password. If the Vercel
backend should use Django ORM directly against Supabase, copy the pooled
Postgres connection string from the Supabase dashboard and keep it secret.

## Seed Supabase Through SQL/REST

From `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:SUPABASE_URL="https://<project-ref>.supabase.co"
$env:SUPABASE_SECRET_KEY="<server-only-key>"
$env:CARD_CATALOG_SOURCE="supabase"
$env:CARD_IMAGE_BASE_URL="https://<project-ref>.supabase.co/storage/v1/object/public/card-images"

python manage.py sync_card_catalog_supabase --source "C:\Users\SSAFY\Desktop\pjt-08-db-bundle-20260529\card_master_api.sqlite"
python manage.py upload_card_images_supabase --source "C:\Users\SSAFY\Desktop\pjt-08-db-bundle-20260529\card_images" --source "C:\Users\SSAFY\Desktop\pjt-08-db-bundle-20260529\discontinued_card_images"
python manage.py sync_app_sqlite_supabase --source ".\db.sqlite3"
```

If the schema is missing, create it first from the Supabase SQL editor. The
commands above assume the tables and `card-images` bucket already exist.

Demo login:

```txt
id: skawngus
password: skawngus
```

## Vercel Backend

Create a Vercel project with root directory:

```txt
backend
```

Environment variables:

```txt
DATABASE_URL=<pooled Supabase Postgres URL required for Django auth/transactions/analytics>
DATABASE_SSL_REQUIRE=true
DATABASE_CONN_MAX_AGE=60
DJANGO_SECRET_KEY=<generate-a-secret>
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=<backend-vercel-domain>,127.0.0.1,localhost
CORS_ALLOWED_ORIGINS=https://<frontend-vercel-domain>
FRONTEND_URL=https://<frontend-vercel-domain>
BACKEND_URL=https://<backend-vercel-domain>
OAUTH_CALLBACK_BASE_URL=https://<backend-vercel-domain>

SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SECRET_KEY=<server-only-key, only needed when CARD_CATALOG_SOURCE=supabase>
SUPABASE_PUBLISHABLE_KEY=<publishable-key, only needed when CARD_CATALOG_SOURCE=supabase>
CARD_CATALOG_SOURCE=postgres
CARD_IMAGE_BASE_URL=https://<project-ref>.supabase.co/storage/v1/object/public/card-images

AI_MODE=gms
GMS_API_KEY=<secret>
GMS_BASE_URL=https://gms.ssafy.io/gmsapi/api.openai.com/v1
GMS_MODEL=gpt-5-mini
GMS_FALLBACK_MODEL=gpt-5.4-mini
GMS_TIMEOUT_SECONDS=45
GMS_MAX_OUTPUT_TOKENS=3000
AI_PROXY_URL=https://<ai-proxy-vercel-domain>
AI_PROXY_ENABLED=true

EMAIL_AUTH_ENABLED=true
DEV_AUTO_LOGIN_ENABLED=true
DEMO_LOGIN_ID=skawngus
DEMO_USER_PASSWORD=skawngus
```

## Vercel Frontend

Create a Vercel project with root directory:

```txt
frontend
```

Environment variables:

```txt
BACKEND_URL=https://<backend-vercel-domain>
VITE_API_BASE_URL=
VITE_USE_MOCK_API=false
VITE_DEV_AUTO_LOGIN=false
VITE_API_TIMEOUT_MS=8000
VITE_AI_TIMEOUT_MS=50000
```

Build command:

```txt
npm run build
```

Output directory:

```txt
dist
```

## Smoke Test

1. Open the frontend Vercel URL.
2. Log in with `skawngus / skawngus`.
3. Check:
   - `/cards` card carousel and category recommendations load images.
   - `/budget` shows Nam Ju Hyun demo spending.
   - `/analytics` loads real demo transactions.
   - `/chat` answers through GMS.
