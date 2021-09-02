"""Common apps exceptions"""

__all__ = ["ManagerException", "NotFoundManagerException"]


class ManagerException(Exception):
    """Exception that raises in managers"""


class NotFoundManagerException(ManagerException):
    """Exception that raises in managers if required object wasn't found."""
