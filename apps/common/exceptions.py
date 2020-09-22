"""Common apps exceptions"""
from fastapi import status


class PermissionException(Exception):
    """Exception that raises in Permission based classes"""

    def __init__(self, detail: str = "", status_code: int = status.HTTP_403_FORBIDDEN):
        self.detail = detail or "This user is not authorized to access this endpoint"
        self.status_code = status_code


class HandlerException(Exception):
    """Exception that raises in handlers"""


class NotFoundHandlerException(HandlerException):
    """Exception that raises in handlers if required object wasn't found."""


class RepositoryException(Exception):
    def __init__(self, detail: str = "", status_code: int = status.HTTP_400_BAD_REQUEST):
        self.detail = detail or "Repository exception"
        self.status_code = status_code
