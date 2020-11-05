import typing

import fastapi
from pymongo.client_session import ClientSession
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.results import InsertOneResult, InsertManyResult, UpdateResult, DeleteResult

import bases.db
import bases.exceptions
import bases.models
import bases.utils


class BaseRepositoryConfig:
    def __init__(
        self,
        convert: bool = True,
        convert_to: typing.Type[bases.models.BaseMongoDBModel] = None,
        raise_not_found: bool = True,
    ):
        self.convert = convert
        self.convert_to = convert_to
        if self.convert and convert_to is None:
            raise NotImplementedError("Set 'convert_to' attribute or set'convert' to False")
        self.raise_not_found = raise_not_found


class BaseRepository:
    """Class for CRUD for MongoDB"""

    def __init__(self, col_name: str, obj_name: str, repository_config: BaseRepositoryConfig):
        self.obj_name: str = obj_name
        self._db: Database = bases.db.MongoDBConnection.get_default_db()
        self.col: Collection = self._db[col_name]
        self.repository_config: BaseRepositoryConfig = repository_config
        if not issubclass(self.repository_config.convert_to, bases.models.BaseMongoDBModel):
            raise NotImplementedError(
                f"'convert_to' kwarg must be a subclass from '{bases.models.BaseMongoDBModel.__name__}'"
            )

    def convert_one_result(self, result: dict, repository_config: BaseRepositoryConfig = None):
        """Convert result from MongoDB to BaseMongoDBModel subclass"""
        repository_config = self.repository_config if repository_config is None else repository_config
        if repository_config.convert:
            convert_to = repository_config.convert_to
            if convert_to is None:
                raise NotImplementedError(
                    "Please setup repository_config class (and append 'convert_to' argument) or change "
                    "('convert' argument to 'False'). Also, you can override 'repository_config' class in this method."
                )
            result = convert_to.from_db(data=result)
        return result

    async def convert_many_results(self, results_cursor, repository_config: BaseRepositoryConfig = None):
        repository_config = self.repository_config if repository_config is None else repository_config
        convert_to = repository_config.convert_to or self.repository_config.convert_to
        if repository_config.convert:
            return [convert_to.from_db(data=result) async for result in results_cursor]
        return [item async for item in results_cursor]

    def _raise_not_found(self, result, repository_config: BaseRepositoryConfig = None):
        """raise an error if result is None"""
        repository_config = self.repository_config if repository_config is None else repository_config
        raise_not_found = repository_config.raise_not_found
        if result is None and raise_not_found:
            raise bases.exceptions.RepositoryException(
                detail=f"{self.obj_name} not found", status_code=fastapi.status.HTTP_404_NOT_FOUND
            )

    def _not_found_convert_flow(self, result, repository_config: BaseRepositoryConfig = None):
        """convert result to BaseMongoDBModel subclass"""
        self._raise_not_found(result=result, repository_config=repository_config)
        return self.convert_one_result(result=result, repository_config=repository_config)

    async def insert_one(self, document: dict, session: ClientSession = None, **kwargs) -> InsertOneResult:
        """insert one document to MongoDB"""
        result: InsertOneResult = await self.col.insert_one(document=document, session=session, **kwargs)
        return result

    async def insert_many(
        self, documents: list[dict], ordered: bool = False, session: ClientSession = None, **kwargs
    ) -> InsertManyResult:
        """insert many documents to MongoDB"""
        return await self.col.insert_many(documents=documents, ordered=ordered, session=session, **kwargs)

    async def replace_one(
        self, query: dict, replacement: dict, upsert: bool = False, session: ClientSession = None, **kwargs
    ) -> UpdateResult:
        """replace one document in MongoDB"""
        return await self.col.replace_one(
            filter=query, replacement=replacement, upsert=upsert, session=session, **kwargs
        )

    async def update_one(
        self, query: dict, update: dict, upsert: bool = False, session: ClientSession = None, **kwargs
    ) -> UpdateResult:
        """update one document to MongoDB"""
        return await self.col.update_one(filter=query, update=update, upsert=upsert, session=session, **kwargs)

    async def update_many(
        self, query: dict, update: dict, upsert: bool = False, session: ClientSession = None, **kwargs
    ) -> UpdateResult:
        """update many documents to MongoDB"""
        return await self.col.update_many(filter=query, update=update, upsert=upsert, session=session, **kwargs)

    async def delete_one(self, query: dict, session: ClientSession = None, **kwargs) -> DeleteResult:
        """delete one document from MongoDB"""
        return await self.col.delete_one(filter=query, session=session, **kwargs)

    async def delete_many(self, query: dict, session: ClientSession = None, **kwargs) -> DeleteResult:
        """delete many documents from MongoDB"""
        return await self.col.delete_many(filter=query, session=session, **kwargs)

    async def find(
        self,
        query: dict,
        sort: list[tuple[str, int]] = None,
        skip: int = 0,
        limit: int = 0,
        projection: typing.Union[list[str], dict[str, bool]] = None,
        session: ClientSession = None,
        repository_config: BaseRepositoryConfig = None,
        **kwargs,
    ):
        """find documents from MongoDB"""
        results_cursor = self.col.find(
            filter=query, sort=sort, skip=skip, limit=limit, projection=projection, session=session, **kwargs
        )

        return await self.convert_many_results(results_cursor=results_cursor, repository_config=repository_config)

    async def find_one(
        self,
        query: dict,
        sort: list[tuple[str, int]] = None,
        projection: typing.Union[list[str], dict[str, bool]] = None,
        session: ClientSession = None,
        repository_config: BaseRepositoryConfig = None,
        **kwargs,
    ):
        """find one document from MongoDB"""
        result = await self.col.find_one(filter=query, sort=sort, projection=projection, session=session, **kwargs)
        return self._not_found_convert_flow(result=result, repository_config=repository_config)

    async def find_one_and_delete(
        self,
        query: dict,
        sort: list[tuple[str, int]] = None,
        projection: typing.Union[list[str], dict[str, bool]] = None,
        session: ClientSession = None,
        repository_config: BaseRepositoryConfig = None,
        **kwargs,
    ):
        """find one and delete a document from MongoDB"""
        result = await self.col.find_one_and_delete(
            filter=query, projection=projection, sort=sort, session=session, **kwargs
        )
        return self._not_found_convert_flow(result=result, repository_config=repository_config)

    async def find_one_and_replace(
        self,
        query: dict,
        replacement: dict,
        upsert: bool = False,
        sort: list[tuple[str, int]] = None,
        projection: typing.Union[list[str], dict[str, bool]] = None,
        session: ClientSession = None,
        repository_config: BaseRepositoryConfig = None,
        **kwargs,
    ):
        """find one and replace a document from MongoDB"""
        result = await self.col.find_one_and_replace(
            filter=query,
            replacement=replacement,
            upsert=upsert,
            sort=sort,
            projection=projection,
            session=session,
            **kwargs,
        )
        return self._not_found_convert_flow(result=result, repository_config=repository_config)

    async def find_one_and_update(
        self,
        query: dict,
        update: dict,
        sort: list[tuple[str, int]] = None,
        projection: typing.Union[list[str], dict[str, bool]] = None,
        session: ClientSession = None,
        repository_config: BaseRepositoryConfig = None,
        **kwargs,
    ):
        """find one and update document from MongoDB"""
        result = await self.col.find_one_and_update(
            filter=query, update=update, sort=sort, projection=projection, session=session, **kwargs
        )
        return self._not_found_convert_flow(result=result, repository_config=repository_config)

    async def count_documents(self, query: dict, session: ClientSession = None, **kwargs) -> int:
        """count documents in MongoDB collection"""
        return await self.col.count_documents(filter=query, session=session, **kwargs)

    async def estimated_document_count(self, **kwargs):
        """count documents in MongoDB from collection metadata"""
        return await self.col.estimated_document_count(**kwargs)

    async def aggregate(
        self, pipeline: list, session: ClientSession = None, repository_config: BaseRepositoryConfig = None, **kwargs
    ):
        results_cursor = self.col.aggregate(pipeline=pipeline, session=session, **kwargs)
        return await self.convert_many_results(results_cursor=results_cursor, repository_config=repository_config)
