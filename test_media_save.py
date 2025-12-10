#!/usr/bin/env python3
"""
Direct test of media save operation
Tests SQLAlchemy ORM mapping without HTTP layer
"""
import asyncio
import sys
import os
from pathlib import Path
from uuid import uuid4

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

async def test_media_save():
    """Test direct media save to database"""
    try:
        print("[TEST] Setting up database connection...")

        # Set environment
        os.environ["DATABASE_URL"] = "postgresql://postgres:pgpass@172.31.150.143:5432/wordloom"

        # Import after setting env
        from infra.database.session import get_engine
        from infra.database.models.media_models import MediaModel, MediaType, MediaState
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession

        print("[TEST] Getting engine...")
        engine = await get_engine()

        print("[TEST] Creating async session factory...")
        from infra.database.session import get_session_factory
        SessionLocal = await get_session_factory()

        print("[TEST] Starting transaction...")
        async with SessionLocal() as session:
            # First, try a SELECT to test ORM mapping
            print("[TEST] Testing SELECT with ORM mapping...")
            stmt = select(MediaModel)
            result = await session.execute(stmt)
            existing_media = result.scalars().all()
            print(f"[TEST] ✓ Found {len(existing_media)} existing media items")

            # Now try INSERT
            print("[TEST] Creating new MediaModel instance...")
            new_media = MediaModel(
                id=uuid4(),
                filename="test.jpg",
                storage_key=f"test_{uuid4()}",
                mime_type="image/jpeg",
                file_size=1024,
                width=100,
                height=100,
                media_type="image",  # This should be a string now
                state="ACTIVE",
            )

            print("[TEST] Adding to session...")
            session.add(new_media)

            print("[TEST] Committing transaction...")
            await session.commit()

            print(f"[TEST] ✓ Successfully saved media: {new_media.id}")

        print("[TEST] ✓✓✓ All tests passed!")
        return True

    except Exception as e:
        print(f"[TEST] ✗ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        print("[TEST] Cleaning up...")

if __name__ == "__main__":
    success = asyncio.run(test_media_save())
    sys.exit(0 if success else 1)
