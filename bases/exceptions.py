"""Common apps exceptions"""
from fastapi import status


class PermissionException(Exception):
    """Exception that raises in Permission based classes"""

    def __init__(
        self,
        detail: str = "You aren't authorized to make this action.",
        status_code: int = status.HTTP_403_FORBIDDEN,
    ):
        super().__init__()
        self.detail = detail
        self.status_code = status_code


class HandlerException(Exception):
    """Exception that raises in handlers"""


class NotFoundHandlerException(HandlerException):
    """Exception that raises in handlers if required object wasn't found."""


class RepositoryException(Exception):
    """Exception that raises in repositories"""

    def __init__(self, detail: str = "", status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__()
        self.detail = detail or "Repository exception"
        self.status_code = status_code
