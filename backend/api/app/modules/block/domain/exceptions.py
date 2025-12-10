"""
Block domain-specific exceptions - Business error hierarchy

All exceptions inherit from BusinessError base class.
Mapped to HTTP status codes in router layer.
"""

from typing import Optional
from uuid import UUID

from api.app.shared.errors import BusinessError


# Domain exception alias for router exception handling
DomainException = BusinessError


# Block-specific exceptions

class BlockNotFoundError(BusinessError):
    """Block with given ID does not exist"""
    status_code = 404
    error_code = "BLOCK_NOT_FOUND"
    message = "Block not found"

    def __init__(self, block_id: UUID, detail: Optional[str] = None):
        self.block_id = block_id
        self.detail = detail or f"Block {block_id} does not exist"
        super().__init__(self.message, self.detail)


class InvalidBlockDataError(BusinessError):
    """Block data is invalid"""
    status_code = 422
    error_code = "INVALID_BLOCK_DATA"
    message = "Invalid block data"

    def __init__(self, detail: str):
        super().__init__(self.message, detail)


class BlockInvalidTypeError(BusinessError):
    """Block type is invalid"""
    status_code = 422
    error_code = "INVALID_BLOCK_TYPE"
    message = "Invalid block type"

    def __init__(self, block_type: str, detail: Optional[str] = None):
        self.block_type = block_type
        msg = detail or f"Block type '{block_type}' is not valid"
        super().__init__(self.message, msg)


class BlockOperationError(BusinessError):
    """Generic block operation error"""
    status_code = 500
    error_code = "BLOCK_OPERATION_ERROR"
    message = "Block operation failed"

    def __init__(self, operation: str, reason: str):
        self.operation = operation
        detail = f"Operation '{operation}' failed: {reason}"
        super().__init__(self.message, detail)
