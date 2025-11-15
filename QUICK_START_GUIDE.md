# Wordloom v3 Quick Start Guide

## Database Connection

```bash
# Connect to wordloom database
psql postgresql://postgres:pgpass@127.0.0.1:5433/wordloom

# Or via Python
python -c "import psycopg; conn = psycopg.connect('postgresql://postgres:pgpass@127.0.0.1:5433/wordloom'); print('Connected')"
```

## Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Start dev server
npm run dev
# Runs on http://localhost:30001

# Build for production
npm run build
npm start
```

## Backend Setup

```bash
# Install dependencies
cd backend/api
pip install -r requirements.txt

# Start dev server
python -m uvicorn app.main:app --reload --port 8000
# Runs on http://localhost:8000

# Run tests
pytest

# Run with specific test file
pytest tests/test_auth.py -v
```

## Database Operations

### Check Database Status
```sql
-- Connect to wordloom
\c wordloom

-- List all tables
\dt

-- Check table structure
\d libraries

-- Count records
SELECT COUNT(*) FROM libraries;
```

### Common Database Tasks

```sql
-- View all databases
SELECT datname FROM pg_database ORDER BY datname;

-- Backup database
pg_dump postgresql://postgres:pgpass@127.0.0.1:5433/wordloom > backup.sql

-- Restore database
psql postgresql://postgres:pgpass@127.0.0.1:5433/wordloom < backup.sql

-- Drop all tables
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
```

## Configuration Files

### Frontend
- `frontend/.env.local` - Frontend environment variables
- `frontend/next.config.ts` - Next.js configuration
- `frontend/tsconfig.json` - TypeScript configuration

### Backend
- `backend/api/.env` - Backend environment variables
- `backend/api/app/config/setting.py` - Application settings
- `backend/pyproject.toml` - Python dependencies

## Project Structure

```
d:\Project\Wordloom\
├── frontend/               # Next.js 14 frontend
│   ├── src/
│   │   ├── lib/           # Utilities
│   │   ├── components/    # React components
│   │   ├── styles/        # CSS files
│   │   └── app/           # Pages/routes
│   └── package.json
├── backend/               # FastAPI backend
│   ├── api/
│   │   ├── app/           # Application code
│   │   │   ├── config/    # Configuration
│   │   │   ├── domains/   # Business logic
│   │   │   ├── infra/     # Infrastructure
│   │   │   ├── migrations/# Database migrations
│   │   │   └── main.py    # FastAPI app
│   │   └── .env
│   └── pyproject.toml
├── assets/docs/
│   ├── DDD_RULES.yaml
│   ├── HEXAGONAL_RULES.yaml
│   ├── VISUAL_RULES.yaml
│   └── ADR/
│       ├── ADR-053-wordloom-core-database-schema.md
│       └── ...
└── README.md
```

## Key Files Reference

### Database Schema
- File: `backend/api/app/migrations/001_create_core_schema.sql`
- Tables: 11 (7 core + 3 association + 1 search index)
- Status: ✅ Initialized

### Frontend Theme
- File: `frontend/src/lib/themes.ts`
- Themes: 3 (Light, Dark, Loom)
- Modes: 2 (light, dark) per theme

### API Client
- File: `frontend/src/lib/api/client.ts`
- Auth: JWT Bearer token with auto-refresh
- Timeout: 30 seconds
- Retry: 3 attempts

## Environment Variables

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_BASE=http://localhost:8000
NEXT_PUBLIC_API_TIMEOUT=30000
```

### Backend (.env)
```env
DATABASE_URL=postgresql://postgres:pgpass@127.0.0.1:5433/wordloom
DEBUG=False
ENVIRONMENT=development
LOG_LEVEL=INFO
SECRET_KEY=dev-secret-key-change-in-production
```

## Useful Commands

```bash
# Development servers (run in separate terminals)
cd frontend && npm run dev          # Terminal 1
cd backend/api && python -m uvicorn app.main:app --reload --port 8000  # Terminal 2

# Database
python setup_db.py                  # Check/create database
python init_schema.py               # Initialize schema

# Testing
pytest                              # Run all tests
pytest tests/ -v                    # Verbose output
pytest tests/test_auth.py -k login  # Run specific tests

# Code quality
black .                             # Format Python code
isort .                             # Sort imports
pylint app/                         # Lint Python code
```

## Troubleshooting

### Database Connection Failed
```
Error: connection to server at "127.0.0.1", port 5433 failed
Solution: Check if PostgreSQL is running: systemctl status postgresql
```

### Frontend Port Already in Use
```
Error: Address already in use (port 30001)
Solution: Change port in frontend/.env.local or kill process: lsof -ti:30001 | xargs kill -9
```

### Backend Import Errors
```
Error: ModuleNotFoundError: No module named 'app'
Solution: Install dependencies: pip install -r requirements.txt
```

### Schema Already Exists
```
Error: relation "libraries" already exists
Solution: Drop all tables: python -c "from app import db; db.Base.metadata.drop_all()"
```

## Documentation

- **Architecture**: See `assets/docs/DDD_RULES.yaml` and `HEXAGONAL_RULES.yaml`
- **Frontend Rules**: See `assets/docs/VISUAL_RULES.yaml`
- **Database Design**: See `assets/docs/ADR/ADR-053-wordloom-core-database-schema.md`
- **Frontend Strategy**: See `frontend/docs/ADR-FR-001-theme-strategy.md`

## Contact & Support

For questions or issues:
1. Check documentation in `assets/docs/`
2. Review ADRs in `assets/docs/ADR/`
3. Check git history for similar issues
4. Consult RULES files for architectural decisions
