# AI 3D Studio - Deployment & Operations Guide

## 1. Local Development Quickstart

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Blender 4.x or 5.x installed locally

### Step 1: Clone and Configure Environment
```bash
cp .env.example .env
```
Ensure `BLENDER_PATH` in `.env` points to your local Blender executable (e.g. `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe` or `/usr/bin/blender`).

### Step 2: Set Up Backend
```bash
# Install backend dependencies
pip install -r backend/requirements.txt

# Run automated tests to verify Blender & API readiness
$env:PYTHONPATH="." ; pytest backend/tests/test_api.py -v

# Start FastAPI server
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
The API docs will be live at `http://127.0.0.1:8000/docs`.

### Step 3: Set Up Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to launch the 3D Studio workspace.

---

## 2. Docker & Containerized Production Deployment

Run the complete multi-container stack:
```bash
docker-compose up -d --build
```
This deploys:
1. `postgres`: Managed PostgreSQL 16 database.
2. `redis`: Queue store for background workers.
3. `backend`: FastAPI backend and background task worker with Blender 4.2 LTS headless pre-installed.
4. `frontend`: High-performance Nginx web server hosting the compiled Vite/React application and reverse-proxying `/api` requests.

---

## 3. Production Environment Checklist

| Variable | Description | Production Setting |
| :--- | :--- | :--- |
| `ENV` | Environment identifier | `production` |
| `SECRET_KEY` | Key for auth token signing | Generate 64-char random string |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/ai_3d_studio` |
| `BLENDER_PATH` | Path to blender executable | `/usr/local/bin/blender` |
| `STORAGE_TYPE` | Storage backend (`local` or `s3`) | `s3` |
| `S3_BUCKET_NAME` | Dedicated S3 bucket for assets | e.g. `ai-3d-studio-prod-assets` |
| `AWS_ACCESS_KEY_ID` | AWS S3 access key | Secret manager |
| `AWS_SECRET_ACCESS_KEY` | AWS S3 secret key | Secret manager |
| `AI_3D_PROVIDER` | Default AI provider (`meshy` or `tripo`) | `meshy` |
| `MESHY_API_KEY` | Secret API key from Meshy | Secret manager |
| `DAILY_BUDGET_LIMIT_USD` | Maximum daily spend cap | e.g. `50.00` |
