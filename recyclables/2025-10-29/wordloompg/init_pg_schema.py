# init_pg_schema.py - create tables in Postgres by importing your models and running create_all
import os, sys
from sqlalchemy import create_engine

api_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from app.models import Base  # uses your current models.py
import app.models_orbit      # ensure Orbit models are imported so tables are registered

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise SystemExit("Please set DATABASE_URL to your Postgres URL before running this script.")

engine = create_engine(DATABASE_URL, future=True)
Base.metadata.create_all(engine)
print("✅ Schema created in Postgres.")
