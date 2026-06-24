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
