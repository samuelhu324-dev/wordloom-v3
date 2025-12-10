"""
Tag Exceptions - Domain-specific exceptions with HTTP mapping

Implements comprehensive exception hierarchy aligned with DDD_RULES:
  - RULE-018: Tag creation with name/color/icon validation
  - RULE-019: Tag-Entity association management
  - RULE-020: Tag hierarchical structures (parent-child relationships)

Exception Hierarchy:
  DomainException (base)
    ├─ TagException
    │   ├─ NotFoundError (404)
    │   ├─ AlreadyExistsError (409)
    │   ├─ InvalidNameError (422)
    │   ├─ InvalidColorError (422)
    │   ├─ InvalidHierarchyError (422)
    │   ├─ AlreadyAssociatedError (409)
    │   ├─ AssociationNotFoundError (404)
    │   ├─ AlreadyDeletedError (409)
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
# Tag Domain Exceptions
# ============================================

class TagException(DomainException):
    """Base for all Tag Domain exceptions"""
    pass


class TagNotFoundError(TagException):
    """
    RULE-018: 当请求的 Tag 不存在时触发

    对应场景：
    - GET /tags/{id} 不存在
    - 删除已删除的 Tag
    - 更新不存在的 Tag
    """
    def __init__(self, tag_id: UUID):
        super().__init__(
            message=f"Tag {tag_id} not found",
            code="TAG_NOT_FOUND",
            http_status=404,
            details={"tag_id": str(tag_id)}
        )


class TagAlreadyExistsError(TagException):
    """
    RULE-018: 尝试创建具有相同名称的 Tag

    对应场景：
    - POST /tags 使用重复的名称
    - Unique constraint violation on name
    """
    def __init__(self, name: str):
        super().__init__(
            message=f"Tag '{name}' already exists",
            code="TAG_ALREADY_EXISTS",
            http_status=409,
            details={"name": name}
        )


class TagInvalidNameError(TagException):
    """
    RULE-018: Tag 名称验证失败

    约束条件：
    - 非空字符串
    - 长度 1-50 个字符
    - 不能只含空格

    对应场景：
    - 名称为空或超过长度
    - POST/PATCH /tags 名称验证失败
    """
    def __init__(self, reason: str, name: Optional[str] = None):
        super().__init__(
            message=f"Invalid tag name: {reason}",
            code="TAG_INVALID_NAME",
            http_status=422,
            details={"reason": reason, "name": name}
        )


class TagInvalidColorError(TagException):
    """
    RULE-018: Tag 颜色验证失败

    约束条件：
    - 必须是有效的十六进制颜色代码
    - 格式：#RRGGBB 或 #RRGGBBAA
    - 示例：#FF5733, #00FF00CC

    对应场景：
    - 颜色格式错误
    - POST/PATCH /tags 颜色验证失败
    """
    def __init__(self, color: str, reason: Optional[str] = None):
        super().__init__(
            message=f"Invalid tag color: {reason or 'Invalid hex format'}",
            code="TAG_INVALID_COLOR",
            http_status=422,
            details={"color": color, "reason": reason}
        )


class TagInvalidHierarchyError(TagException):
    """
    RULE-020: 标签层级结构验证失败

    约束条件：
    - parent_tag_id 必须指向存在的 Tag
    - 不允许循环引用（A 的子标签不能包含 A）
    - 最大层级深度：3 级（0=顶级，1=一级子标签，2=二级子标签）

    对应场景：
    - 创建子标签时 parent_tag_id 不存在
    - 尝试设置自己为父标签
    - 超过最大层级深度
    """
    def __init__(self, reason: str, parent_tag_id: Optional[UUID] = None):
        super().__init__(
            message=f"Invalid tag hierarchy: {reason}",
            code="TAG_INVALID_HIERARCHY",
            http_status=422,
            details={"reason": reason, "parent_tag_id": str(parent_tag_id) if parent_tag_id else None}
        )


class TagAlreadyAssociatedError(TagException):
    """
    RULE-019: Tag 与实体的关联已存在

    对应场景：
    - POST /tags/{id}/associate 重复关联
    - 已将标签与 Book/Bookshelf/Block 关联
    """
    def __init__(self, tag_id: UUID, entity_type: str, entity_id: UUID):
        super().__init__(
            message=f"Tag {tag_id} is already associated with {entity_type} {entity_id}",
            code="TAG_ALREADY_ASSOCIATED",
            http_status=409,
            details={
                "tag_id": str(tag_id),
                "entity_type": entity_type,
                "entity_id": str(entity_id)
            }
        )


class TagAssociationNotFoundError(TagException):
    """
    RULE-019: Tag 与实体的关联不存在

    对应场景：
    - DELETE /tags/{id}/associate 尝试移除不存在的关联
    - 标签与实体的关联被删除
    """
    def __init__(self, tag_id: UUID, entity_type: str, entity_id: UUID):
        super().__init__(
            message=f"Association between Tag {tag_id} and {entity_type} {entity_id} not found",
            code="TAG_ASSOCIATION_NOT_FOUND",
            http_status=404,
            details={
                "tag_id": str(tag_id),
                "entity_type": entity_type,
                "entity_id": str(entity_id)
            }
        )


class TagAlreadyDeletedError(TagException):
    """
    RULE-018: 尝试删除已删除的 Tag

    对应场景：
    - DELETE /tags/{id} 标签已软删除
    - 尝试重复删除
    """
    def __init__(self, tag_id: UUID):
        super().__init__(
            message=f"Tag {tag_id} is already deleted",
            code="TAG_ALREADY_DELETED",
            http_status=409,
            details={"tag_id": str(tag_id)}
        )


class TagOperationError(TagException):
    """
    通用操作错误（500 级别）

    对应场景：
    - 数据库操作失败
    - 事务提交失败
    - 未预期的业务逻辑错误
    """
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="TAG_OPERATION_ERROR",
            http_status=500,
            details=details or {}
        )


# ============================================
# Repository Level Exceptions
# ============================================

class TagRepositoryException(DomainException):
    """Base for repository-level exceptions"""
    code: str = "TAG_REPOSITORY_ERROR"
    http_status: int = 500

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code=self.code,
            http_status=self.http_status,
            details=details or {}
        )


class TagRepositoryQueryError(TagRepositoryException):
    """查询操作失败"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Failed to query tags: {reason}",
            details={"reason": reason}
        )


class TagRepositorySaveError(TagRepositoryException):
    """持久化操作失败"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Failed to save tag: {reason}",
            details={"reason": reason}
        )


class TagRepositoryDeleteError(TagRepositoryException):
    """删除操作失败"""
    def __init__(self, reason: str):
        super().__init__(
            message=f"Failed to delete tag: {reason}",
            details={"reason": reason}
        )
