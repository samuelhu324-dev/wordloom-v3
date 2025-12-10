import asyncio
from sqlalchemy import select
from infra.database.session import get_session_factory
from infra.database.models.library_models import LibraryModel

async def main():
    factory = await get_session_factory()
    async with factory() as session:
        result = await session.execute(select(LibraryModel))
        rows = result.scalars().all()
        print(f"Total libraries: {len(rows)}")
        for r in rows:
            print(r.id, r.user_id, r.name)

asyncio.run(main())
