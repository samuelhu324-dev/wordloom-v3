"""
Tag Ports - 所有 Input 和 Output Port 接口

Output Ports (repository.py):
  - TagRepository

Input Ports (input.py):
  - CreateTagUseCase
  - CreateSubtagUseCase
  - UpdateTagUseCase
  - DeleteTagUseCase
  - RestoreTagUseCase
  - AssociateTagUseCase
  - DisassociateTagUseCase
  - SearchTagsUseCase
  - GetMostUsedTagsUseCase

Request/Response DTOs:
  - CreateTagRequest, TagResponse
  - SearchTagsRequest
  - AssociateTagRequest
  - ...
"""

# Output ports (repository)
from .output import TagRepository

# Input ports (use cases) + DTOs
from .input import (
    CreateTagUseCase,
    CreateSubtagUseCase,
    UpdateTagUseCase,
    DeleteTagUseCase,
    RestoreTagUseCase,
    AssociateTagUseCase,
    DisassociateTagUseCase,
    SearchTagsUseCase,
    GetMostUsedTagsUseCase,
    # Request DTOs
    CreateTagRequest,
    CreateSubtagRequest,
    UpdateTagRequest,
    DeleteTagRequest,
    RestoreTagRequest,
    AssociateTagRequest,
    DisassociateTagRequest,
    SearchTagsRequest,
    GetMostUsedTagsRequest,
    # Response DTOs
    TagResponse,
)

__all__ = [
    # Output ports
    "TagRepository",
    # Input ports
    "CreateTagUseCase",
    "CreateSubtagUseCase",
    "UpdateTagUseCase",
    "DeleteTagUseCase",
    "RestoreTagUseCase",
    "AssociateTagUseCase",
    "DisassociateTagUseCase",
    "SearchTagsUseCase",
    "GetMostUsedTagsUseCase",
    # Request DTOs
    "CreateTagRequest",
    "CreateSubtagRequest",
    "UpdateTagRequest",
    "DeleteTagRequest",
    "RestoreTagRequest",
    "AssociateTagRequest",
    "DisassociateTagRequest",
    "SearchTagsRequest",
    "GetMostUsedTagsRequest",
    # Response DTOs
    "TagResponse",
]
