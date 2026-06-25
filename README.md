# CARCH

CARCH is a card spending assistant that analyzes a user's owned cards, transactions, benefit conditions, and planned expenses to suggest better spending decisions.

The project separates two recommendation flows:

- Owned card usage: choose which existing card to use for upcoming spending.
- New card issuance: recommend a better card when historical spending shows a clear benefit gap.

## Stack

- Frontend: Vue 3, Vite
- Backend: Django
- AI proxy: FastAPI
- Local database: SQLite for app data
- Card catalog: external SQLite bundle plus card image folder

## Demo On Another Computer

For presentation setup, use:

- [docs/DEMO_RUNBOOK.md](docs/DEMO_RUNBOOK.md)
- [docs/LOCAL_COLLAB_SETUP.md](docs/LOCAL_COLLAB_SETUP.md)

The short version:

```powershell
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

Copy the external card bundle to:

```txt
finalpjt/pjt-08-db-bundle-20260529/
```

Then:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo --strict-card-bundle
python manage.py runserver 127.0.0.1:8000
```

In another terminal:

```powershell
cd frontend
npm install
npm.cmd run dev
```

Open:

```txt
http://127.0.0.1:5173/cards
```

## Demo Account

```txt
email: demo@carch.local
password: Carchdemo123!
```

`python manage.py seed_demo` creates this account and demo scenario data.

## Do Not Commit

- `.env`
- `backend/db.sqlite3`
- full card catalog SQLite DB
- full raw card image bundle
- API keys

Use a shared drive, USB, or Git LFS for the external card bundle.
