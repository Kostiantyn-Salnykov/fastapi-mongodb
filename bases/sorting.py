# TODO: optimize sorting for a query and aggregate
import typing

import fastapi
import pymongo


class SortBuilder:
    def __init__(self, *, sorting_fields: list[tuple[str, int]]):
        self._id_field_name = "_id"
        self.sorting_default = [(self._id_field_name, pymongo.DESCENDING)]
        self.sorting_fields = sorting_fields

    @staticmethod
    def _get_model_sorting_fields(*, model) -> list[str]:
        try:
            return model.Config.sorting_fields
        except Exception as error:
            raise NotImplementedError from error

    def _get_model_sorting_default(self, *, model) -> list[tuple[str, int]]:
        try:
            return model.Config.sorting_default
        except (KeyError, AttributeError):
            return self.sorting_default

    @staticmethod
    def _add_one_to_sorting(
        *,
        mongo_sorting: typing.Union[dict[str, int], list[tuple[str, int]]],
        field_name: str,
        ordering: int,
        to_pipeline_stage: bool,
    ):
        mongo_sorting.update({field_name: ordering}) if to_pipeline_stage else mongo_sorting.append(
            (field_name, ordering)
        )

    def _add_many_to_sorting(
        self,
        *,
        mongo_sorting: typing.Union[dict[str, int], list[tuple[str, int]]],
        fields: list[tuple[str, int]],
        to_pipeline_stage: bool,
    ):
        for field_name, ordering in fields:
            self._add_one_to_sorting(
                mongo_sorting=mongo_sorting,
                field_name=field_name,
                ordering=ordering,
                to_pipeline_stage=to_pipeline_stage,
            )

    # TODO (Make model_sorting_fields by aliases) kost:
    def to_db(
        self, *, model, to_pipeline_stage: bool = False, append_sorting_default: bool = True
    ) -> typing.Union[dict[str, int], list[tuple[str, int]]]:
        model_sorting_fields: list[str] = self._get_model_sorting_fields(model=model)
        field_names = []
        mongo_sorting = {} if to_pipeline_stage else []

        for field_name, ordering in self.sorting_fields:
            field_names.append(field_name)
            if field_name in model_sorting_fields:
                self._add_one_to_sorting(
                    mongo_sorting=mongo_sorting,
                    field_name=field_name,
                    ordering=ordering,
                    to_pipeline_stage=to_pipeline_stage,
                )

        if not mongo_sorting:
            append_sorting_default = False
            model_sorting_default: typing.Union[
                list[tuple[str, int]], tuple[str, int]
            ] = self._get_model_sorting_default(model=model)
            self._add_many_to_sorting(
                mongo_sorting=mongo_sorting, fields=model_sorting_default, to_pipeline_stage=to_pipeline_stage
            )

        if append_sorting_default and self._id_field_name not in field_names:
            self._add_many_to_sorting(
                mongo_sorting=mongo_sorting, fields=self.sorting_default, to_pipeline_stage=to_pipeline_stage
            )

        return mongo_sorting


class BaseSort:
    """Class as dependency for sorting query system"""

    def __call__(
        self,
        order_by: typing.Optional[str] = fastapi.Query(
            default="",
            max_length=256,
            alias="orderBy",
            description="Comma separated values with 'field_name' for ascending order and '-field_name' for descending "
            "order. Examples: 'orderBy=-email,-_id' or 'orderBy=email,_id'",
            example="email,-id",
        ),
    ):
        sort_list: list[str] = order_by.split(",") if order_by else []
        sorting_fields = []
        for field in sort_list:
            stripped_field = field.strip()
            field_name = stripped_field.removeprefix("-")
            ordering = (pymongo.ASCENDING, pymongo.DESCENDING)[stripped_field.startswith("-")]
            sorting_fields.append((field_name, ordering))

        return SortBuilder(sorting_fields=sorting_fields)
