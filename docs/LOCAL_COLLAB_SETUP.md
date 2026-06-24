# Local Collaboration Setup

## Environment Files

Do not commit real `.env` files. Copy the examples and fill secrets locally.

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

Required local URLs:

```env
# backend/.env
FRONTEND_URL=http://127.0.0.1:5173
BACKEND_URL=http://127.0.0.1:8000
OAUTH_CALLBACK_BASE_URL=http://127.0.0.1:8000
```

Provider callback URLs must exactly match the values registered in each developer console. Use explicit values when the console uses `localhost` instead of `127.0.0.1`.

```env
KAKAO_REDIRECT_URI=http://127.0.0.1:8000/api/auth/oauth/kakao/callback/
NAVER_REDIRECT_URI=http://127.0.0.1:8000/api/auth/oauth/naver/callback/
```

If Naver is registered with `localhost`, use this exact callback instead:

```env
NAVER_REDIRECT_URI=http://localhost:8000/api/auth/oauth/naver/callback/
```

## Database

Do not commit `backend/db.sqlite3`. It is a local development artifact and is ignored by Git.

Shared state should be reproducible from:

- Django migrations
- backend seed data
- frontend mock data
- committed card image and JSON assets

Local reset flow:

```powershell
cd backend
python manage.py migrate
```

The app seeds demo cards, transactions, plans, and community data from source-controlled files during API use.

## Card Data And Images

There are two card data layers.

Small demo assets are committed to Git:

- `frontend/src/data/mockData.js`
- `frontend/public/card-images/*.png`
- `backend/data/*.json`

Use this layer for demo screens, fallback data, and assets that the frontend needs without the backend card catalog.

The full card catalog is a local data bundle and should not be committed:

- `pjt-08-db-bundle-20260529/card_master_api.sqlite`
- `pjt-08-db-bundle-20260529/card_images/`
- `pjt-08-db-bundle-20260529/discontinued_card_images/`

The backend auto-detects this bundle in either location:

```txt
carch/pjt-08-db-bundle-20260529
finalpjt/pjt-08-db-bundle-20260529
```

If a teammate stores it elsewhere, set explicit paths in `backend/.env`:

```env
CARD_DATA_BUNDLE_DIR=C:/path/to/pjt-08-db-bundle-20260529
CARD_MASTER_DB=C:/path/to/pjt-08-db-bundle-20260529/card_master_api.sqlite
CARD_IMAGE_DIR=C:/path/to/pjt-08-db-bundle-20260529/card_images
```

Backend card image URLs are served from the local bundle through:

```txt
/api/card-images/<filename>
```

For a card used directly in frontend mock/demo data, copy its image into `frontend/public/card-images/` and reference it as:

```js
imageUrl: '/card-images/10106.png'
```

Rule of thumb:

- commit curated demo images and source JSON
- do not commit sqlite databases or full raw image bundles
- document any required external bundle path in `.env.example` or this file

## OAuth Checklist

For local social login, run both servers:

```powershell
cd backend
python manage.py runserver 127.0.0.1:8000
```

```powershell
cd frontend
npm.cmd run dev
```

Naver developer console should include:

- Service URL: `http://127.0.0.1:5173`
- Callback URL: the same value as `NAVER_REDIRECT_URI`
- Test account registered as an admin or tester while the app is in development mode
