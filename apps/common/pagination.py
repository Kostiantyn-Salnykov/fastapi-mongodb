import fastapi

from apps.common.bases import Paginator
from apps.common.config import common_settings


class LimitOffsetPagination:
    """Pagination based on 'Limit' and  'Offset' parameters"""

    def __call__(
        self,
        limit: int = fastapi.Query(
            default=common_settings.PAGINATION_DEFAULT_LIMIT,
            ge=common_settings.PAGINATION_MIN_LIMIT,
            le=common_settings.PAGINATION_MAX_LIMIT,
        ),
        offset: int = fastapi.Query(
            default=common_settings.PAGINATION_DEFAULT_OFFSET, ge=common_settings.PAGINATION_MIN_OFFSET
        ),
    ) -> Paginator:
        """Enable to use inside FastAPI Depends"""
        return Paginator(skip=offset, limit=limit)
