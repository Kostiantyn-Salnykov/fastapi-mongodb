import apps.users.models
from apps.users.config import users_settings
from bases.repositories import BaseRepository, BaseRepositoryConfig

__all__ = ["UserRepository"]


class UserRepository(BaseRepository):
    def __init__(
        self,
        col_name: str = users_settings.USERS_COL,
        obj_name: str = "User",
        repository_config: BaseRepositoryConfig = BaseRepositoryConfig(
            convert_to=apps.users.models.UserModel
        ),
    ):
        super().__init__(col_name=col_name, obj_name=obj_name, repository_config=repository_config)
