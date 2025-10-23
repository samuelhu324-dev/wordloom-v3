# ---- app/database.py (v4: explicit .env path + override=True)
import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Always load the api/.env of THIS app, even if parent/.env or system env exists.
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

DEFAULT_URL = "postgresql+psycopg://postgres:pgpass@localhost:5444/wordloompg"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_URL)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    future=True,
)

@event.listens_for(engine, "connect")
def _set_search_path(dbapi_conn, conn_record):
    try:
        cur = dbapi_conn.cursor()
        cur.execute("SET search_path TO public")
        cur.close()
    except Exception:
        pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
