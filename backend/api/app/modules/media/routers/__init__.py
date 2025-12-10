"""
Media Routers - HTTP Adapter

FastAPI routers for media operations.

Structure:
  routers/
  └── media_router.py

Endpoints map to use cases:
  POST /media/upload → UploadImageUseCase / UploadVideoUseCase
  DELETE /media/{id} → DeleteMediaUseCase
  POST /media/{id}/restore → RestoreMediaUseCase
  GET /media/trash → ListTrashUseCase
  POST /media/purge-expired → PurgeExpiredUseCase
  etc.

All HTTP concerns (parsing, validation, response format) handled here.
Use case logic stays pure and testable.
"""
