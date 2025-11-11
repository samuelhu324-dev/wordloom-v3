"""
Library Domain Exceptions

所有 Library 相关的业务异常都在这里定义
"""

class LibraryException(Exception):
    """Library Domain 的基类异常"""
    pass


class LibraryNotFoundError(LibraryException):
    """Library 不存在"""
    def __init__(self, library_id: str):
        self.library_id = library_id
        super().__init__(f"Library {library_id} not found")


class DuplicateLibraryError(LibraryException):
    """用户已有 Library（违反 RULE-001）"""
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User {user_id} already has a Library")


class InvalidLibraryError(LibraryException):
    """Library 数据无效"""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Invalid Library: {reason}")# Domain exceptions for library module
