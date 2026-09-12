# Secure Content Portal

Secure sharing of training videos, PDF documents, and HTML reference content.

## Phase 1 status

The initial React/Vite frontend and FastAPI backend are configured. PostgreSQL
access is provided through SQLAlchemy, and Alembic manages the initial `users`
and `content` schema migration.

## Local setup

1. Copy `.env.example` to `backend/.env` and set `DATABASE_URL`.
2. Install backend dependencies in a virtual environment:

	```powershell
	cd backend
	python -m venv .venv
	.\.venv\Scripts\Activate.ps1
	pip install -r requirements.txt
	.\.venv\Scripts\alembic.exe upgrade head
	```

3. Start the API:

	```powershell
	.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
	```

4. Start the frontend in a second terminal:

	```powershell
	cd frontend
	npm install
	npm run dev
	```

The API is available at `http://localhost:8000`, with interactive docs at
`http://localhost:8000/docs`. The frontend is available at
`http://localhost:5173`.

## Verification

Run `npm run build` and `npm run lint` from `frontend`. Run
`alembic check` from `backend` to confirm the database matches the models.

OAuth, private storage, authorization, protected content delivery, and the
remaining deployment documentation will be added in later phases.

