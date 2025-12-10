#!/usr/bin/env python3
"""Test upload image use case directly"""
import sys
import asyncio
from pathlib import Path
from uuid import UUID

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test_upload_use_case():
    """Test UploadImageUseCase.execute()"""
    from api.app.modules.media.domain import MediaMimeType
    from api.app.modules.media.application.use_cases.upload_image import UploadImageUseCase
    from infra.storage.media_repository_impl import SQLAlchemyMediaRepository
    from infra.database import get_engine, get_session_factory
    from sqlalchemy.ext.asyncio import AsyncSession

    print("[UC] Testing UploadImageUseCase...")
    try:
        # Get async session
        engine = get_engine()
        session_factory = get_session_factory()

        async with session_factory() as session:
            repo = SQLAlchemyMediaRepository(session)
            uc = UploadImageUseCase(repo)

            print("[UC] Calling execute()...")
            media = await uc.execute(
                filename="test.png",
                mime_type=MediaMimeType.PNG,
                file_size=1024,
                storage_key="test/image.png",
                user_id=None,  # Anonymous
            )

            print(f"[UC] ✅ Media uploaded: {media.id}")
            print(f"[UC] user_id: {media.user_id}")
            return True
    except Exception as e:
        print(f"[UC] ❌ Failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_upload_use_case())
    sys.exit(0 if success else 1)
