# Insight360 Dashboard

A data analytics app:
- **Upload**: drag-and-drop CSV/XLSX, clean, and generate a report.
- **Analysis**: KPIs, filters + slicer, preview table, column analyzer, charts, and insights.

## Frontend (Vite + React + Recharts)
1) Install & run
```bash
cd frontend
npm install
npm run dev
```
Open the URL Vite prints (usually http://localhost:5173).

2) API endpoint  
In `frontend/src/App.jsx`, set `API_BASE` to your backend URL (default http://localhost:8000).

## Backend (FastAPI)
1) Create venv and install deps (Python 3.11 recommended)
```bash
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install numpy==1.26.4 pandas==2.2.1 fastapi==0.109.2 uvicorn[standard]==0.27.1 python-multipart==0.0.9 matplotlib==3.8.4 openpyxl==3.1.2
```

2) Run API
```bash
python -m uvicorn backend.api:app --reload --port 8000
```

## Features
- Two pages: Upload (ingest) and Analysis (visuals)
- Data cleaning, KPIs, filters + slicer
- Column analyzer with top values
- Charts: distribution, correlation, categories (Recharts)
- Export cleaned CSV
- Light/dark mode toggle
