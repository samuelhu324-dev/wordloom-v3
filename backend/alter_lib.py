import asyncio
from sqlalchemy import text
from infra.database.session import get_engine

STATEMENTS = [
    "ALTER TABLE libraries DROP CONSTRAINT IF EXISTS libraries_user_id_key",
    "ALTER TABLE libraries ALTER COLUMN user_id TYPE uuid USING gen_random_uuid()",
    "DROP INDEX IF EXISTS idx_libraries_user_id",
    "CREATE INDEX idx_libraries_user_id ON libraries(user_id)",
]

async def run():
    engine = await get_engine()
    async with engine.begin() as conn:
        for stmt in STATEMENTS:
            try:
                await conn.execute(text(stmt))
                print("OK:", stmt)
            except Exception as e:
                print("ERR:", stmt, e)
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run())
