# TODO: optimize sorting for a query and aggregate
import typing

import fastapi
import pymongo


class BaseSort:
    """Class as dependency for sorting query system"""

    def __init__(self, model):
        self.model = model
        self._id_field = "_id"
        self.default_sort_query = f"-{self._id_field}"
        self.sorting_model_fields: list[str] = self._get_sorting_fields()
        self.sorting_model_default: str = self._get_sorting_default()
        self.order_by = None

    def __call__(
        self,
        order_by: typing.Optional[str] = fastapi.Query(
            default=None,
            max_length=256,
            alias="orderBy",
            description="Comma separated values with 'field_name' for ascending order and '-field_name' for descending "
            "order. Examples: 'orderBy=-email,-id' or 'orderBy=email,id'",
            example="email,-id",
        ),
    ):
        if order_by is None:
            self.order_by = self.sorting_model_default
        else:
            self.order_by = order_by
        return self

    def _get_sorting_fields(self):
        try:
            return self.model.Config.sorting_fields
        except Exception as error:
            raise NotImplementedError from error

    def _get_sorting_default(self):
        try:
            return self.model.Config.sorting_default
        except (KeyError, AttributeError):
            return self.default_sort_query

    def _append_id_field_sorting(self, key_or_list: list[tuple[str, int]]):
        append_id_sorting = True

        for sorting in key_or_list:
            sort_key = sorting[0]
            if sort_key == self._id_field:
                append_id_sorting = False

        if append_id_sorting:
            key_or_list.append((self._id_field, pymongo.DESCENDING))

    def _convert_to_pipeline_stage(self, key_or_list: list[tuple[str, int]]) -> dict[str, int]:
        sort_stage = {}

        for field_name, ordering in key_or_list:
            sort_stage.update({field_name: ordering})

        return sort_stage

    def to_db(self, to_pipeline_stage: bool = False) -> typing.Union[list[tuple[str, int]], dict[str, int]]:
        """Collect sorting keys for MongoDB"""
        sort_list = self.order_by.split(",")
        key_or_list = []
        for field in sort_list:
            ordering = pymongo.ASCENDING
            field_name = field
            if field.startswith("-"):
                ordering = pymongo.DESCENDING  # change ordering for descending
                field_name = field.removeprefix("-")  # get field_name without '-' character

            if field_name in self.sorting_model_fields:
                key_or_list.append((field_name, ordering))

        self._append_id_field_sorting(key_or_list=key_or_list)

        if to_pipeline_stage:
            return self._convert_to_pipeline_stage(key_or_list=key_or_list)

        return key_or_list
