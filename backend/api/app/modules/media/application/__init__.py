"""
Media Application Layer - Use Cases & Ports

Application layer orchestrates media domain logic and infrastructure.

Structure:
  application/
  ├── ports/
  │   ├── input.py       - UseCase interfaces
  │   └── output.py      - Repository & FileSystem interfaces
  ├── use_cases/
  │   ├── upload_image.py
  │   ├── upload_video.py
  │   ├── delete_media.py
  │   ├── restore_media.py
  │   ├── restore_batch.py
  │   ├── list_trash.py
  │   ├── purge_expired.py
  │   ├── associate_media.py
  │   ├── disassociate_media.py
  │   └── list_entity_media.py
  └── __init__.py
"""
