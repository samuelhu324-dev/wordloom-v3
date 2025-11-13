"""
Media Exceptions - Domain-specific exceptions with HTTP mapping

Implements comprehensive exception hierarchy aligned with DDD_RULES:
  - POLICY-009: Media storage quota and usage limits
  - POLICY-010: Media trash retention and purge lifecycle
  - Media file validation (MIME types, dimensions, duration)

Exception Hierarchy:
  DomainException (base)
    ├─ MediaException
    │   ├─ NotFoundError (404)
    │   ├─ InvalidMimeTypeError (422)
    │   ├─ FileSizeTooLargeError (422)
    │   ├─ InvalidDimensionsError (422)
    │   ├─ InvalidDurationError (422)
    │   ├─ StorageQuotaExceededError (429)
    │   ├─ MediaInTrashError (409)
    │   ├─ CannotPurgeError (409)
    │   ├─ CannotRestoreError (409)
    │   ├─ AssociationError (409)
    │   └─ OperationError (500)
    └─ RepositoryException (500)
"""

from typing import Optional, Dict, Any
from uuid import UUID


class DomainException(Exception):
    """Base for all Domain exceptions"""
    code: str = "DOMAIN_ERROR"
    http_status: int = 500
    details: Dict[str, Any] = {}

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        http_status: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if http_status:
            self.http_status = http_status
        if details:
            self.details = details

    @property
    def http_status_code(self) -> int:
        """Alias for http_status"""
        return self.http_status

    def to_dict(self) -> Dict[str, Any]:
        """序列化为 API 响应"""
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details,
        }


# ============================================
# Media Domain Exceptions
# ============================================

class MediaException(DomainException):
    """Base for all Media Domain exceptions"""
    pass


class MediaNotFoundError(MediaException):
    """
    当请求的 Media 文件不存在时触发

    对应场景：
    - GET /media/{id}/download 文件不存在
    - DELETE /media/{id} 文件不存在
    - 获取已删除的 Media
    """
    def __init__(self, media_id: UUID):
        super().__init__(
            message=f"Media {media_id} not found",
            code="MEDIA_NOT_FOUND",
            http_status=404,
            details={"media_id": str(media_id)}
        )


class InvalidMimeTypeError(MediaException):
    """
    POLICY-009: 不支持的 MIME 类型

    支持的类型：
    - 图片: image/jpeg, image/png, image/webp, image/gif
    - 视频: video/mp4, video/webm, video/ogg

    对应场景：
    - POST /media/upload 文件类型不支持
    - 上传 .exe 或其他二进制文件
    """
    def __init__(self, mime_type: str, media_type: Optional[str] = None):
        super().__init__(
            message=f"Invalid MIME type: {mime_type}",
            code="INVALID_MIME_TYPE",
            http_status=422,
            details={"mime_type": mime_type, "expected_type": media_type}
        )


class FileSizeTooLargeError(MediaException):
    """
    POLICY-009: 文件大小超过限制

    大小限制：
    - 图片: 10MB
    - 视频: 100MB

    对应场景：
    - POST /media/upload 文件过大
    - 客户端应该在上传前检查大小
    """
    def __init__(self, media_type: str, file_size: int, max_size: int):
        size_mb = file_size / (1024 * 1024)
        max_mb = max_size / (1024 * 1024)
        super().__init__(
            message=f"{media_type.capitalize()} file size ({size_mb:.1f}MB) exceeds limit ({max_mb:.0f}MB)",
            code="FILE_SIZE_TOO_LARGE",
            http_status=422,
            details={
                "media_type": media_type,
                "file_size": file_size,
                "max_size": max_size,
                "size_mb": round(size_mb, 1),
                "max_mb": round(max_mb, 1)
            }
        )


class InvalidDimensionsError(MediaException):
    """
    图片尺寸验证失败

    约束条件：
    - width > 0
    - height > 0
    - width <= 8000, height <= 8000 (防止极端尺寸)

    对应场景：
    - 图片元数据提取失败
    - 尺寸为 0 或负数
    """
    def __init__(self, width: Optional[int], height: Optional[int], reason: str):
        super().__init__(
            message=f"Invalid image dimensions: {reason}",
            code="INVALID_DIMENSIONS",
            http_status=422,
            details={"width": width, "height": height, "reason": reason}
        )


class InvalidDurationError(MediaException):
    """
    视频时长验证失败

    约束条件：
    - duration_ms > 0
    - duration_ms <= 7200000 (2 小时)

    对应场景：
    - 视频元数据提取失败
    - 时长为 0 或超过限制
    """
    def __init__(self, duration_ms: Optional[int], reason: str):
        super().__init__(
            message=f"Invalid video duration: {reason}",
            code="INVALID_DURATION",
            http_status=422,
            details={"duration_ms": duration_ms, "reason": reason}
        )


class StorageQuotaExceededError(MediaException):
    """
    POLICY-009: 存储配额已满

    对应场景：
    - POST /media/upload 用户/工作区存储已满
    - 需要删除文件或购买更多配额
    """
    def __init__(self, used_bytes: int, quota_bytes: int, needed_bytes: int):
        used_mb = used_bytes / (1024 * 1024)
        quota_mb = quota_bytes / (1024 * 1024)
        needed_mb = needed_bytes / (1024 * 1024)
        super().__init__(
            message=f"Storage quota exceeded: {used_mb:.1f}MB/{quota_mb:.0f}MB used, need {needed_mb:.1f}MB more",
            code="STORAGE_QUOTA_EXCEEDED",
            http_status=429,
            details={
                "used_bytes": used_bytes,
                "quota_bytes": quota_bytes,
                "needed_bytes": needed_bytes,
                "used_mb": round(used_mb, 1),
                "quota_mb": round(quota_mb, 1),
                "needed_mb": round(needed_mb, 1)
            }
        )


class MediaInTrashError(MediaException):
    """
    POLICY-010: 媒体已在垃圾箱中

    对应场景：
    - 尝试对垃圾中的文件进行操作
    - 关联垃圾中的媒体到实体
    - 二次删除操作
    """
    def __init__(self, media_id: UUID, operation: str):
        super().__init__(
            message=f"Cannot {operation}: media {media_id} is in trash",
            code="MEDIA_IN_TRASH",
            http_status=409,
            details={"media_id": str(media_id), "operation": operation}
        )


class CannotPurgeError(MediaException):
    """
    POLICY-010: 无法永久删除媒体

    约束条件：
    - 只能删除垃圾中的文件
    - 必须在垃圾中停留 30 天后才能删除

    对应场景：
    - 尝试删除活跃的文件
    - 尝试提前删除垃圾文件
    """
    def __init__(self, media_id: UUID, reason: str, days_remaining: Optional[int] = None):
        details = {"media_id": str(media_id), "reason": reason}
        if days_remaining is not None:
            details["days_remaining"] = days_remaining
            message = f"Cannot purge media {media_id}: {days_remaining} days remaining in trash"
        else:
            message = f"Cannot purge media {media_id}: {reason}"

        super().__init__(
            message=message,
            code="CANNOT_PURGE",
            http_status=409,
            details=details
        )


class CannotRestoreError(MediaException):
    """
    POLICY-010: 无法从垃圾还原媒体

    对应场景：
    - 尝试还原不在垃圾中的文件
    - 已被永久删除的文件
    """
    def __init__(self, media_id: UUID, reason: str):
        super().__init__(
            message=f"Cannot restore media {media_id}: {reason}",
            code="CANNOT_RESTORE",
            http_status=409,
            details={"media_id": str(media_id), "reason": reason}
        )


class AssociationError(MediaException):
    """
    媒体与实体的关联错误

    对应场景：
    - 尝试关联不存在的实体
    - 重复关联
    - 关联不存在的媒体
    """
    def __init__(self, media_id: UUID, entity_type: str, entity_id: UUID, reason: str):
        super().__init__(
            message=f"Association error: {reason}",
            code="ASSOCIATION_ERROR",
            http_status=409,
            details={
                "media_id": str(media_id),
                "entity_type": entity_type,
                "entity_id": str(entity_id),
                "reason": reason
            }
        )


class MediaOperationError(MediaException):
    """
    通用操作错误（500 级别）

    对应场景：
    - 文件系统操作失败
    - 数据库操作失败
    - 元数据提取失败
    - 事务提交失败
    """
    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if operation:
            error_details["operation"] = operation

        super().__init__(
            message=message,
            code="MEDIA_OPERATION_ERROR",
            http_status=500,
            details=error_details
        )


# ============================================
# Repository Level Exceptions
# ============================================

class MediaRepositoryException(DomainException):
    """Base for repository-level exceptions"""
    code: str = "MEDIA_REPOSITORY_ERROR"
    http_status: int = 500

    def __init__(self, message: str, operation: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        error_details = details or {}
        if operation:
            error_details["operation"] = operation

        super().__init__(
            message=message,
            code=self.code,
            http_status=self.http_status,
            details=error_details
        )


class MediaRepositoryQueryError(MediaRepositoryException):
    """查询操作失败"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Failed to query media: {reason}",
            operation="query",
            details={"reason": reason}
        )


class MediaRepositorySaveError(MediaRepositoryException):
    """持久化操作失败"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Failed to save media: {reason}",
            operation="save",
            details={"reason": reason}
        )


class MediaRepositoryDeleteError(MediaRepositoryException):
    """删除操作失败"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Failed to delete media: {reason}",
            operation="delete",
            details={"reason": reason}
        )
