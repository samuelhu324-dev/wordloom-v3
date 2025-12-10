#!/usr/bin/env python3
"""Direct backend test without HTTP - call functions directly"""
import sys
from pathlib import Path
from uuid import UUID

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

async def test_media_creation():
    """Test Media domain object creation"""
    from api.app.modules.media.domain import Media, MediaMimeType

    print("[DIRECT] Testing Media.create_image...")
    try:
        media = Media.create_image(
            filename="test.png",
            mime_type=MediaMimeType.PNG,
            file_size=1024,
            storage_key="test/key",
            user_id=None,  # Anonymous
        )
        print(f"[DIRECT] ✅ Media created: {media.id}")
        print(f"[DIRECT] user_id: {media.user_id}")
        print(f"[DIRECT] filename: {media.filename}")
        return True
    except Exception as e:
        print(f"[DIRECT] ❌ Failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_media_creation())
    sys.exit(0 if success else 1)
