import abc

import fastapi


class BasePermission(abc.ABC):
    @abc.abstractmethod
    def __call__(self, request: fastapi.Request):
        """Check permissions logic and if no valid raise bases.exceptions.PermissionException."""
