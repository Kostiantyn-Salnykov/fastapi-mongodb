import abc

import fastapi
import pymongo.errors

from bases.exceptions import HandlerException

__all__ = ["mongo_duplicate_key_error_handler", "BaseHandler"]


# TODO (Refactor this func to use in handlers or repositories) kost:
def mongo_duplicate_key_error_handler(
    model_name: str, fields: list[str], error: pymongo.errors.DuplicateKeyError
):  # pragma: no cover
    error_details = error.details.get("keyValue", {})
    for field in fields:
        if field in error_details:
            raise HandlerException(
                f"{model_name} with this '{error_details[field]}' {field} already exists"
            )
    raise HandlerException("Unexpected duplication error")


class BaseHandler(abc.ABC):
    @abc.abstractmethod
    def __init__(self, request: fastapi.Request):
        self.request = request

    def get_handler(self, name: str) -> "BaseHandler":
        try:
            handler_class = getattr(self.request.app.state, name)
            handler_instance = handler_class(request=self.request)
        except AttributeError as error:
            raise NotImplementedError(error) from error
        else:
            return handler_instance
