import fastapi
import pydantic

import bases


class Paginator(pydantic.BaseModel):
    """Class returns from pagination"""

    skip: int = pydantic.Field(
        default=bases.config.common_settings.PAGINATION_DEFAULT_OFFSET,
        ge=bases.config.common_settings.PAGINATION_MIN_OFFSET,
    )
    limit: int = pydantic.Field(
        default=bases.config.common_settings.PAGINATION_DEFAULT_LIMIT,
        ge=bases.config.common_settings.PAGINATION_MIN_LIMIT,
        le=bases.config.common_settings.PAGINATION_MAX_LIMIT,
    )


class LimitOffsetPagination:
    """Pagination based on 'limit' and 'offset' parameters"""

    def __call__(
        self,
        limit: int = fastapi.Query(
            default=bases.config.common_settings.PAGINATION_DEFAULT_LIMIT,
            ge=bases.config.common_settings.PAGINATION_MIN_LIMIT,
            le=bases.config.common_settings.PAGINATION_MAX_LIMIT,
        ),
        offset: int = fastapi.Query(
            default=bases.config.common_settings.PAGINATION_DEFAULT_OFFSET,
            ge=bases.config.common_settings.PAGINATION_MIN_OFFSET,
        ),
    ) -> Paginator:
        """Enable to use inside FastAPI Depends"""
        return Paginator(skip=offset, limit=limit)
