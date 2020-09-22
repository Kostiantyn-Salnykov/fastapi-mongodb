from fastapi import Query

from apps.common.bases import BasePagination, Paginator
from apps.common.config import common_settings


class LimitOffsetPagination(BasePagination):
    """Pagination based on 'Limit' and  'Offset' parameters"""

    def __call__(
        self,
        limit: int = Query(
            default=common_settings.PAGINATION_DEFAULT_LIMIT,
            ge=common_settings.PAGINATION_MIN_LIMIT,
            le=common_settings.PAGINATION_MAX_LIMIT,
        ),
        offset: int = Query(
            default=common_settings.PAGINATION_DEFAULT_OFFSET, ge=common_settings.PAGINATION_MIN_OFFSET
        ),
    ) -> Paginator:
        """Enable to use inside FastAPI Depends"""
        return self.make_paginator(skip=offset, limit=limit)
