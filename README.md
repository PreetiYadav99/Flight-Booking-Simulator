# Flight Booking Simulator

A demo flight booking simulator (React + Tailwind frontend, Flask + SQLite backend) for experimenting with search, dynamic pricing, seat holds, booking flows and queued email delivery.

## Repository

Files of interest:
- `backend/` — Flask API, database scripts, email queue worker.
- `frontend/` — Vite + React + Tailwind UI (dev server on port 5173/5174).
- `schema.sql`, `backend/sample_data.csv` — DB schema and sample data used by `backend/db_init.py`.

## Quick start (Windows)

1. Backend setup

```powershell
cd D:\Flight-Booking-Simulator\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
# Initialize the database from the CSV (this creates flights.db)
python db_init.py
# Start the backend (default: http://127.0.0.1:5000)
python app.py
```

2. Frontend setup

```powershell
cd D:\Flight-Booking-Simulator\frontend
npm install
npm run dev
# Open the Local URL printed by Vite (e.g. http://localhost:5174)
```

3. Run quick auth tests (optional)

```powershell
python ..\backend\test_auth.py
```

## Environment variables (optional)

Create a `.env` file in `backend/` or set environment vars to customize behavior:
- `SECRET_KEY` — Flask session secret
- `FRONTEND_ORIGIN` — allowed origin used by CORS fallback
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS` — configure these to enable real email sending (otherwise emails are queued but skipped)

## Notes
- The `image/` folder is excluded from the repository via `.gitignore` per your request.
- `backend/db_init.py` reads `backend/sample_data.csv` to populate `flights.db` — re-run it after changing the CSV.
- If you see a `no such table: flights` error, re-run `python backend/db_init.py` to recreate the database.




## Deploy backend on Render Link:
https://flight-booking-simulator-3.onrender.com/


## Deploy frontend on Vercel
Link: https://flight-booking-simulator-rawy.vercel.app/

1. Go to https://vercel.com/new and select your GitHub repository `PreetiYadav99/Flight-Booking-Simulator`.
2. In project settings set:
	 - Framework Preset: `Other` or `Vite`
	 - Root Directory: `frontend`
	 - Build Command: `npm run build`
	 - Output Directory: `dist`
3. Add any env var your frontend needs (e.g., `VITE_API_URL=http://<your-backend-url>`).

We included `frontend/vercel.json` to help Vercel detect the build configuration automatically.


