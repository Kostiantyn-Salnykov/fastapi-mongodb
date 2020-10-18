import fastapi


class BasePermission:
    """Class for permission implementation"""

    def __call__(self, request: fastapi.Request) -> None:
        """method for available Depends in FastAPI"""
        self.check(request=request)

    def check(self, request: fastapi.Request):
        """default method for check permission"""
        raise NotImplementedError
