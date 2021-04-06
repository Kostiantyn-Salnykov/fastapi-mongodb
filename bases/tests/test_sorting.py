import typing

import pymongo

from bases.helpers import AsyncTestCase
from bases.models import BaseDBModel
from bases.sorting import BaseSort, SortBuilder


class TestSortBuilder(AsyncTestCase):
    class TestModel(BaseDBModel):
        a: typing.Optional[str]
        b: typing.Optional[str]
        c: typing.Optional[str]

        class Config(BaseDBModel.Config):
            sorting_fields = ["a", "b"]
            sorting_default = [("a", pymongo.DESCENDING)]

    class TestModelNoSortingFields(BaseDBModel):
        a: typing.Optional[str]

        class Config:
            pass

    class TestModelNoSortingDefault(BaseDBModel):
        a: typing.Optional[str]
        b: typing.Optional[str]
        c: typing.Optional[str]

        class Config:
            sorting_fields = ["a", "b"]

    def test__init__(self):
        sorting_fields = [
            ("a", pymongo.ASCENDING),
            ("b", pymongo.DESCENDING),
            ("c", pymongo.ASCENDING),
        ]

        builder = SortBuilder(sorting_fields=sorting_fields)

        self.assertEqual([("_id", pymongo.DESCENDING)], builder.sorting_default)
        self.assertEqual(sorting_fields, builder.sorting_fields)

    def test_to_db(self):
        sorting_fields = [
            ("a", pymongo.ASCENDING),
            ("b", pymongo.DESCENDING),
            ("c", pymongo.ASCENDING),
        ]
        expected_result = [
            ("a", pymongo.ASCENDING),
            ("b", pymongo.DESCENDING),
            ("_id", pymongo.DESCENDING),
        ]

        result = SortBuilder(sorting_fields=sorting_fields).to_db(model=self.TestModel)

        self.assertEqual(expected_result, result)

    def test_to_db_model_default(self):
        sorting_fields = []
        expected_result = self.TestModel.Config.sorting_default

        result = SortBuilder(sorting_fields=sorting_fields).to_db(
            model=self.TestModel, append_sorting_default=False
        )

        self.assertEqual(expected_result, result)

    def test_to_db_pipeline(self):
        sorting_fields = [
            ("a", pymongo.ASCENDING),
            ("b", pymongo.DESCENDING),
            ("c", pymongo.ASCENDING),
        ]
        expected_result = {
            "a": pymongo.ASCENDING,
            "b": pymongo.DESCENDING,
            "_id": pymongo.DESCENDING,
        }

        result = SortBuilder(sorting_fields=sorting_fields).to_db(
            model=self.TestModel, to_pipeline_stage=True
        )

        self.assertEqual(expected_result, result)

    def test_to_db_pipeline_model_default(self):
        sorting_fields = []
        expected_result = {"a": pymongo.DESCENDING}

        result = SortBuilder(sorting_fields=sorting_fields).to_db(
            model=self.TestModel, to_pipeline_stage=True, append_sorting_default=False
        )

        self.assertEqual(expected_result, result)

    def test_to_db_model_no_sorting_fields(self):
        sorting_fields = []

        with self.assertRaises(NotImplementedError):
            SortBuilder(sorting_fields=sorting_fields).to_db(model=self.TestModelNoSortingFields)

    def test_to_db_model_no_sorting_default(self):
        sorting_fields = []
        expected_result = [("_id", pymongo.DESCENDING)]

        result = SortBuilder(sorting_fields=sorting_fields).to_db(model=self.TestModelNoSortingDefault)

        self.assertEqual(expected_result, result)


class TestBaseSort(AsyncTestCase):
    def test__call__(self):
        expected_sorting_fields = [
            ("_id", pymongo.DESCENDING),
            ("a", pymongo.ASCENDING),
            ("b", pymongo.DESCENDING),
            ("c", pymongo.DESCENDING),
        ]

        sort_builder = BaseSort()(order_by=" -_id  , a  , -b , -c   ")

        self.assertIsInstance(sort_builder, SortBuilder)
        self.assertEqual(expected_sorting_fields, sort_builder.sorting_fields)

    def test__call__empty(self):
        sort_builder = BaseSort()(order_by="")

        self.assertEqual([], sort_builder.sorting_fields)
