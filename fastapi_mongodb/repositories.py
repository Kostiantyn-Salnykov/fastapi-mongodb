import typing
from functools import cached_property

import motor.motor_asyncio
import pymongo.client_session
import pymongo.results

from fastapi_mongodb.db import BaseDBManager


class BaseRepository:
    def __init__(self, db_manager: BaseDBManager, db_name: str, col_name: str):
        self._db_manager = db_manager
        self._db_name = db_name
        self._col_name = col_name

    @cached_property
    def db(self) -> motor.motor_asyncio.AsyncIOMotorDatabase:
        return self._db_manager.retrieve_database(name=self._db_name)

    @cached_property
    def col(self) -> motor.motor_asyncio.AsyncIOMotorCollection:
        return self.db[self._col_name]

    async def insert_one(
        self,
        *,
        document: dict,
        session: pymongo.client_session.ClientSession = None,
        **kwargs,
    ) -> pymongo.results.InsertOneResult:
        """insert one document to MongoDB"""
        return await self.col.insert_one(document=document, session=session, **kwargs)

    async def insert_many(
        self,
        *,
        documents: list[dict],
        ordered: bool = False,
        session: pymongo.client_session.ClientSession = None,
        **kwargs,
    ) -> pymongo.results.InsertManyResult:
        """insert many documents to MongoDB"""
        return await self.col.insert_many(documents=documents, ordered=ordered, session=session, **kwargs)

    async def replace_one(
        self,
        *,
        query: dict,
        replacement: dict,
        upsert: bool = False,
        session: pymongo.client_session.ClientSession = None,
        **kwargs,
    ) -> pymongo.results.UpdateResult:
        """replace one document in MongoDB"""
        return await self.col.replace_one(
            filter=query,
            replacement=replacement,
            upsert=upsert,
            session=session,
            **kwargs,
        )

    async def update_one(
        self,
        *,
        query: dict,
        update: dict,
        upsert: bool = False,
        session: pymongo.client_session.ClientSession = None,
        **kwargs,
    ) -> pymongo.results.UpdateResult:
        """update one document to MongoDB"""
        return await self.col.update_one(filter=query, update=update, upsert=upsert, session=session, **kwargs)

    async def update_many(
        self,
        *,
        query: dict,
        update: dict,
        upsert: bool = False,
        session: pymongo.client_session.ClientSession = None,
        **kwargs,
    ) -> pymongo.results.UpdateResult:
        """update many documents to MongoDB"""
        return await self.col.update_many(filter=query, update=update, upsert=upsert, session=session, **kwargs)

    async def delete_one(
        self,
        *,
        query: dict,
        session: pymongo.client_session.ClientSession = None,
        **kwargs,
    ) -> pymongo.results.DeleteResult:
        """delete one document from MongoDB"""
        return await self.col.delete_one(filter=query, session=session, **kwargs)

    async def delete_many(
        self,
        *,
        query: dict,
        session: pymongo.client_session.ClientSession = None,
        **kwargs,
    ) -> pymongo.results.DeleteResult:
        """delete many documents from MongoDB"""
        return await self.col.delete_many(filter=query, session=session, **kwargs)

    async def find(
        self,
        *,
        query: dict,
        sort: list[tuple[str, int]] = None,
        skip: int = 0,
        limit: int = 0,
        projection: typing.Union[list[str], dict[str, bool]] = None,
        session: pymongo.client_session.ClientSession = None,
        **kwargs,
    ) -> motor.motor_asyncio.AsyncIOMotorCursor:
        """find documents from MongoDB"""
        return self.col.find(
            filter=query,
            sort=sort,
            skip=skip,
            limit=limit,
            projection=projection,
            session=session,
            **kwargs,
        )

    async def find_one(
        self,
        *,
        query: dict,
        sort: list[tuple[str, int]] = None,
        projection: typing.Union[list[str], dict[str, bool]] = None,
        session: pymongo.client_session.ClientSession = None,
        **kwargs,
    ):
        """find one document from MongoDB"""
        return await self.col.find_one(filter=query, sort=sort, projection=projection, session=session, **kwargs)

    async def find_one_and_delete(
        self,
        *,
        query: dict,
        sort: list[tuple[str, int]] = None,
        projection: typing.Union[list[str], dict[str, bool]] = None,
        session: pymongo.client_session.ClientSession = None,
        **kwargs,
    ):
        """find one and delete a document from MongoDB"""
        return await self.col.find_one_and_delete(
            filter=query, projection=projection, sort=sort, session=session, **kwargs
        )

    async def find_one_and_replace(
        self,
        *,
        query: dict,
        replacement: dict,
        upsert: bool = False,
        sort: list[tuple[str, int]] = None,
        projection: typing.Union[list[str], dict[str, bool]] = None,
        return_document: pymongo.ReturnDocument = pymongo.ReturnDocument.AFTER,  # default BEFORE
        session: pymongo.client_session.ClientSession = None,
        **kwargs,
    ):
        """find one and replace a document from MongoDB"""
        return await self.col.find_one_and_replace(
            filter=query,
            replacement=replacement,
            upsert=upsert,
            sort=sort,
            projection=projection,
            session=session,
            return_document=return_document,
            **kwargs,
        )

    async def find_one_and_update(
        self,
        *,
        query: dict,
        update: dict,
        sort: list[tuple[str, int]] = None,
        projection: typing.Union[list[str], dict[str, bool]] = None,
        return_document: pymongo.ReturnDocument = pymongo.ReturnDocument.AFTER,  # default BEFORE
        session: pymongo.client_session.ClientSession = None,
        **kwargs,
    ):
        """find one and update document from MongoDB"""
        return await self.col.find_one_and_update(
            filter=query,
            update=update,
            sort=sort,
            projection=projection,
            session=session,
            return_document=return_document,
            **kwargs,
        )

    async def count_documents(
        self,
        *,
        query: dict,
        session: pymongo.client_session.ClientSession = None,
        **kwargs,
    ) -> int:
        """count documents in MongoDB collection"""
        return await self.col.count_documents(filter=query, session=session, **kwargs)

    async def estimated_document_count(self, **kwargs):
        """count documents in MongoDB from collection metadata"""
        return await self.col.estimated_document_count(**kwargs)

    async def aggregate(
        self,
        *,
        pipeline: list,
        session: pymongo.client_session.ClientSession = None,
        **kwargs,
    ) -> motor.motor_asyncio.AsyncIOMotorCommandCursor:
        return self.col.aggregate(pipeline=pipeline, session=session, **kwargs)

    async def bulk_write(
        self,
        *,
        operations: list[
            typing.Union[
                pymongo.operations.InsertOne,
                pymongo.operations.UpdateOne,
                pymongo.operations.UpdateMany,
                pymongo.operations.ReplaceOne,
                pymongo.operations.DeleteOne,
                pymongo.operations.DeleteMany,
            ]
        ],
        ordered: bool = False,  # default True
        session: pymongo.client_session.ClientSession = None,
    ) -> pymongo.results.BulkWriteResult:
        return await self.col.bulk_write(requests=operations, ordered=ordered, session=session)

    async def watch(
        self, *, pipeline: list[dict], session: pymongo.client_session.ClientSession = None, **kwargs
    ) -> motor.motor_asyncio.AsyncIOMotorChangeStream:
        return self.col.watch(pipeline=pipeline, session=session, **kwargs)
