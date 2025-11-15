"""
Media Application Ports

Input ports (use case interfaces):
- IUploadMediaUseCase
- IUpdateMediaMetadataUseCase
- IGetMediaUseCase
- IListMediaUseCase
- IAssociateMediaUseCase
- IDisassociateMediaUseCase
- IMoveMediaToTrashUseCase
- IRestoreMediaUseCase
- IPurgeExpiredMediaUseCase

Output ports (repository interface):
- MediaRepository (abstract interface for persistence)
"""

from .input import (
    IUploadMediaUseCase,
    IUpdateMediaMetadataUseCase,
    IGetMediaUseCase,
    IListMediaUseCase,
    IAssociateMediaUseCase,
    IDisassociateMediaUseCase,
    IMoveMediaToTrashUseCase,
    IRestoreMediaUseCase,
    IPurgeExpiredMediaUseCase,
    UploadMediaRequest,
    UploadMediaResponse,
    UpdateMediaMetadataRequest,
    MediaResponse,
    MediaListResponse,
    AssociateMediaRequest,
    DisassociateMediaRequest,
    RestoreMediaRequest,
)

from .output import MediaRepository

__all__ = [
    # Input port use cases
    "IUploadMediaUseCase",
    "IUpdateMediaMetadataUseCase",
    "IGetMediaUseCase",
    "IListMediaUseCase",
    "IAssociateMediaUseCase",
    "IDisassociateMediaUseCase",
    "IMoveMediaToTrashUseCase",
    "IRestoreMediaUseCase",
    "IPurgeExpiredMediaUseCase",
    # Input port DTOs
    "UploadMediaRequest",
    "UploadMediaResponse",
    "UpdateMediaMetadataRequest",
    "MediaResponse",
    "MediaListResponse",
    "AssociateMediaRequest",
    "DisassociateMediaRequest",
    "RestoreMediaRequest",
    # Output port
    "MediaRepository",
]
