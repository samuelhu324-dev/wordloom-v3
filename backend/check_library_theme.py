import asyncio
import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select
from infra.database.session import get_engine
from infra.database.models.library_models import LibraryModel
from sqlalchemy.ext.asyncio import AsyncSession

async def check():
    engine = await get_engine()
    async with AsyncSession(engine) as session:
        result = await session.execute(
            select(LibraryModel.id, LibraryModel.name, LibraryModel.theme_color).limit(10)
        )
        rows = result.all()
        print('=== Library theme_color 数据检查 ===')
        for row in rows:
            print(f'Library: {row[1]:<30} | theme_color: {row[2] or "(NULL)"}')
        print(f'\n总共 {len(rows)} 条记录')
    await engine.dispose()

asyncio.run(check())
