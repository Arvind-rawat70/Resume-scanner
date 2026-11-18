# Resume Matcher

A full-stack resume matching application for extracting job requirements, comparing them with candidate profiles, and producing a hiring fit score.

## Current status

This project is now built around the real stack requested for the app:

- Frontend: React + Vite
- Backend: FastAPI + Python
- Database: PostgreSQL
- AI/NLP: semantic similarity with sentence-transformers and rule-based skill extraction

### Completed
- JD parsing from pasted text and uploaded PDF/DOCX/TXT files
- Section-aware requirement extraction
- Required vs preferred skill separation
- Education and eligibility parsing
- Semantic similarity API for JD vs candidate text
- PostgreSQL schema and Docker setup
- Frontend flow for JD input and review

### In progress / next steps
- Resume upload and extraction
- Candidate storage and scoring persistence
- Rank and shortlist dashboard
- Full end-to-end recruiter workflow

## Tech stack

- React 18 + Vite
- FastAPI
- Python 3.x
- PostgreSQL 16
- SQLAlchemy + psycopg2
- pypdf + python-docx
- sentence-transformers
- spaCy
- pytest

## Project structure

```text
resume-matcher/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── schemas.py
│   │   └── services/
│   │       ├── jd_parser.py
│   │       ├── skills_taxonomy.py
│   │       ├── semantic_match.py
│   │       └── text_extract.py
│   ├── tests/
│   └── requirements.txt
├── database/
│   ├── docker-compose.yml
│   └── schema.sql
├── frontend/
│   ├── src/
│   ├── package.json
│   └── vite.config.js
├── sample_data/
├── requirements.txt
├── README.md
└── .gitignore
```

## Run the project

### 1) Install Python dependencies

```bash
cd resume-matcher
python -m venv .venv
. .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2) Start PostgreSQL

```bash
cd resume-matcher/database
docker compose up -d
```

This starts PostgreSQL on port 5432 with the database name `resume_matcher`.

### 3) Start the backend

```bash
cd resume-matcher/backend
. .venv/bin/activate   # Windows: .venv\Scripts\activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API endpoints include:
- `GET /api/health`
- `POST /api/jd/parse`
- `POST /api/match/semantic`

### 4) Start the frontend

```bash
cd resume-matcher/frontend
npm install
npm run dev
```

Open the app in the browser at:
- http://localhost:5173

## How the NLP and matching works

### JD parsing
The backend text processing pipeline does the following:

1. Extract text from pasted content or uploaded PDF/DOCX/TXT files
2. Split the content into sections and sentences
3. Detect requirement-related areas such as responsibilities, required skills, education, and eligibility
4. Normalize skill phrases using the canonical taxonomy in `skills_taxonomy.py`
5. Distinguish required vs preferred requirements using wording and section context

This is a rule-based NLP layer designed to make JDs structured and explainable.

### Semantic matching
The semantic matching service compares JD text and candidate text using:

- SentenceTransformer embeddings when available
- cosine similarity for vector comparison
- lexical fallback when the model is not available or cannot load

The scoring logic rewards overlapping technical context, not just exact string equality.

Example:
- JD says: “Python FastAPI backend engineer with PostgreSQL and React”
- Candidate text says: “Built backend APIs with Python, FastAPI, PostgreSQL and React”

The similarity layer understands these are related even if the wording is not identical.

## Database design

The PostgreSQL schema includes tables for:
- jobs
- skills
- resumes
- candidates
- match results

The schema is stored in:
- [database/schema.sql](database/schema.sql)

## Testing

```bash
cd resume-matcher/backend
. .venv/bin/activate
python -m pytest -q
```

## Notes

- The project is designed for recruiter-facing job description review and AI-assisted matching.
- The current implementation is intentionally modular so resume upload, candidate ranking, and database-backed matching can be added without changing the core parsing flow.
- Skills are normalized through a shared taxonomy so the system can handle common aliases and naming variants consistently.
