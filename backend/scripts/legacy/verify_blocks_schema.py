import asyncio
import sys
from sqlalchemy import text
from infra.database.session import get_engine

async def main():
    eng = await get_engine()
    async with eng.begin() as conn:
        cols = await conn.execute(text("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name='blocks' ORDER BY ordinal_position"))
        print('blocks 列:')
        for c in cols.fetchall():
            print(c)
        cons = await conn.execute(text("SELECT constraint_name FROM information_schema.table_constraints WHERE table_name='blocks'"))
        print('blocks 约束:', [r[0] for r in cons.fetchall()])
    await eng.dispose()

if __name__ == '__main__':
    if sys.platform.startswith('win'):
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass
    asyncio.run(main())