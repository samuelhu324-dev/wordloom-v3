"""
Media Ports - 所有 Input 和 Output Port 接口

Output Ports (repository.py):
  - MediaRepository

Input Ports (input.py):
  - UploadImageUseCase
  - UploadVideoUseCase
  - DeleteMediaUseCase
  - RestoreMediaUseCase
  - PurgeMediaUseCase
  - AssociateMediaUseCase
  - DisassociateMediaUseCase
  - GetMediaUseCase
  - UpdateMediaMetadataUseCase

Request/Response DTOs:
  - UploadImageRequest, MediaResponse
  - DeleteMediaRequest
  - AssociateMediaRequest
  - ...
"""

# Output ports (repository)
from .output import MediaRepository

# Input ports (use cases) + DTOs
from .input import (
    UploadImageUseCase,
    UploadVideoUseCase,
    DeleteMediaUseCase,
    RestoreMediaUseCase,
    PurgeMediaUseCase,
    AssociateMediaUseCase,
    DisassociateMediaUseCase,
    GetMediaUseCase,
    UpdateMediaMetadataUseCase,
    # Request DTOs
    UploadImageRequest,
    UploadVideoRequest,
    DeleteMediaRequest,
    RestoreMediaRequest,
    PurgeMediaRequest,
    AssociateMediaRequest,
    DisassociateMediaRequest,
    GetMediaRequest,
    UpdateImageMetadataRequest,
    UpdateVideoMetadataRequest,
    # Response DTOs
    MediaResponse,
)

__all__ = [
    # Output ports
    "MediaRepository",
    # Input ports
    "UploadImageUseCase",
    "UploadVideoUseCase",
    "DeleteMediaUseCase",
    "RestoreMediaUseCase",
    "PurgeMediaUseCase",
    "AssociateMediaUseCase",
    "DisassociateMediaUseCase",
    "GetMediaUseCase",
    "UpdateMediaMetadataUseCase",
    # Request DTOs
    "UploadImageRequest",
    "UploadVideoRequest",
    "DeleteMediaRequest",
    "RestoreMediaRequest",
    "PurgeMediaRequest",
    "AssociateMediaRequest",
    "DisassociateMediaRequest",
    "GetMediaRequest",
    "UpdateImageMetadataRequest",
    "UpdateVideoMetadataRequest",
    # Response DTOs
    "MediaResponse",
]
