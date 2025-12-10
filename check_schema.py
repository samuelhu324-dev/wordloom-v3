import asyncio
import sys
from pathlib import Path

backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from infra.database import get_session_factory
from sqlalchemy import text

async def check_schema():
    factory = await get_session_factory()
    async with factory() as session:
        # Check media table schema
        result = await session.execute(text('SELECT column_name, is_nullable, data_type FROM information_schema.columns WHERE table_name = \'media\' ORDER BY ordinal_position'))
        rows = result.fetchall()
        print("Media table columns:")
        for row in rows:
            print(f"  {row}")

asyncio.run(check_schema())
