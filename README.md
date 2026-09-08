# Secure Content Portal

A secure full-stack content portal for sharing videos, PDFs,
and HTML training/reference content.

## Tech Stack

- React
- FastAPI
- PostgreSQL
- Google OAuth
- S3-compatible object storage
- PDF.js

## Project Structure

- `frontend/` - React frontend
- `backend/` - FastAPI backend

## Development

Frontend:

```bash
cd frontend
npm install
npm run dev

cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload


We'll expand this substantially near the end.

The assignment specifically requires the README to cover setup, environment variables, deployment, architecture and security trade-offs. :contentReference[oaicite:1]{index=1}

---

# Step 15 — First Git commit

Go to project root:

```bash
cd ..

