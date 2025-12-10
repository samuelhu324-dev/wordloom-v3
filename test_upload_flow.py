#!/usr/bin/env python3
"""
Test the complete media upload flow using domain/application layer
"""
import asyncio
import sys
import os
from pathlib import Path
from uuid import uuid4
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent / "backend"))

async def test_complete_upload_flow():
    """Test complete upload flow"""
    try:
        print("[FLOW] Setting up...")
        os.environ["DATABASE_URL"] = "postgresql://postgres:pgpass@172.31.150.143:5432/wordloom"

        from infra.database.session import get_engine, get_session_factory
        from infra.storage.media_repository_impl import SQLAlchemyMediaRepository
        from api.app.modules.media.application.use_cases.upload_image import UploadImageUseCase
        from api.app.modules.media.domain import MediaMimeType

        print("[FLOW] Getting engine...")
        engine = await get_engine()
        SessionLocal = await get_session_factory()

        print("[FLOW] Creating use case...")
        async with SessionLocal() as session:
            repository = SQLAlchemyMediaRepository(session)
            use_case = UploadImageUseCase(repository)

            print("[FLOW] Executing upload with minimal params...")
            try:
                media = await use_case.execute(
                    filename="test_flow.jpg",
                    mime_type=MediaMimeType.JPEG,
                    file_size=1024,
                    storage_key=f"test_flow_{uuid4()}",
                    user_id=None,  # Anonymous upload
                    width=100,
                    height=100,
                )
                print(f"[FLOW] ✓ Successfully created media: {media.id}")
                print(f"[FLOW] ✓✓✓ Complete flow test passed!")
                return True
            except Exception as e:
                print(f"[FLOW] ✗ Use case failed: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return False

    except Exception as e:
        print(f"[FLOW] ✗ Setup failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_complete_upload_flow())
    sys.exit(0 if success else 1)
