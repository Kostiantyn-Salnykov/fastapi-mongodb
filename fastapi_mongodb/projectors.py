import typing

import fastapi

from fastapi_mongodb.exceptions import HandlerException
from fastapi_mongodb.models import BaseDBModel


class BaseProjector:
    def __init__(self, model_class: typing.Type[BaseDBModel]):
        self.model = model_class
        self._id_field = "_id"
        self.fields_show = None
        self.fields_hide = None

    def __call__(
        self,
        fields_show: str = fastapi.Query(
            default=None,
            alias="fieldsShow",
            description="Comma separated values with field names. (You can't exclude '_id' field)",
        ),
        fields_hide: str = fastapi.Query(
            default=None,
            alias="fieldsHide",
            description="Comma separated values with field names. (You can't exclude '_id' field)",
        ),
    ):
        if fields_show is not None and fields_hide is not None:
            raise HandlerException("You can't add 'fieldsShow' and 'fieldsHide' together to Projector")
        self.fields_show = fields_show
        self.fields_hide = fields_hide
        return self

    def _create_projection(self, show: bool) -> dict[str, bool]:
        fields: str = (self.fields_hide, self.fields_show)[show]
        projection = {}
        for field in fields.split(","):
            striped_field = field.strip()
            if striped_field in self.model.__fields__ and self.model.__fields__[striped_field].has_alias:
                striped_field = self.model.__fields__[striped_field].alias
            if striped_field:
                projection[striped_field] = show

        if self._id_field in projection:
            projection.pop(self._id_field)  # can't exclude '_id' field from response
        return projection

    def to_db(self) -> typing.Union[dict[str, bool], None]:
        if self.fields_hide is None and self.fields_show is None:
            return None

        show = False
        if self.fields_show:
            show = True

        return self._create_projection(show=show)
