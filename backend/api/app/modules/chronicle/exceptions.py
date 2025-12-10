"""Chronicle Exceptions - 最小异常层

后续可扩展细分错误 (速率限制、非法状态变更等)。
"""

from typing import Optional, Dict, Any


class ChronicleException(Exception):
    code: str = "CHRONICLE_ERROR"
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

    def to_dict(self) -> Dict[str, Any]:
        return {"code": self.code, "message": self.message, "details": self.details}


class ChronicleInvalidEventError(ChronicleException):
    def __init__(self, reason: str):
        super().__init__(
            message=f"Invalid chronicle event: {reason}",
            code="CHRONICLE_INVALID_EVENT",
            http_status=422,
            details={"reason": reason},
        )


class ChronicleRepositoryError(ChronicleException):
    def __init__(self, reason: str):
        super().__init__(
            message=f"Chronicle repository error: {reason}",
            code="CHRONICLE_REPOSITORY_ERROR",
            http_status=500,
            details={"reason": reason},
        )
