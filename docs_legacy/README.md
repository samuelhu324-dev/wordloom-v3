# Wordloom

---

## What it is

- Wordloom is a personal knowledge management (PKM) workspace centered around **Library / Bookshelf / Book / Block**.
- Built-in features include **tags**, **search**, and a recycle bin (**Basement**).
- Tech stack: **Next.js** (Frontend), **FastAPI** (Backend), **PostgreSQL** (Database).

## Quick start (Docker)

```powershell
# Prereq (Windows): install Docker Desktop and make sure it is running

# 0) Choose a working directory
cd <any path>

# 1) Clone
git clone https://github.com/samuelhu324-dev/Wordloom.git Wordloom

# 2) Enter repo
cd Wordloom

# 3) Copy docker env files
copy backend\.env.docker.example backend\.env.docker
copy frontend\.env.docker.example frontend\.env.docker

# 4) Start containers
docker compose up -d --build

# 5) Open (Frontend)
start http://localhost:31002
```

## Default ports

- Frontend: http://localhost:31002
- Backend API: http://localhost:31001
- Postgres: localhost:5434 (container 5432)

## Notes / troubleshooting

- Backend runs Alembic migrations via the container entrypoint.
- If `docker` is not found, Docker Desktop is not installed or not running.
- If `31002` is already in use, Docker Compose will fail with a port conflict; change the host port in `docker-compose.yml`.
