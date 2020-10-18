import apps.users.models
import bases.repositories
from apps.users.config import users_settings

__all__ = ["UserRepository"]


class UserRepository(bases.repositories.BaseRepository):
    def __init__(
        self,
        col_name: str = users_settings.USERS_COL,
        obj_name: str = "User",
        repository_config: bases.repositories.BaseRepositoryConfig = bases.repositories.BaseRepositoryConfig(
            convert_to=apps.users.models.UserModel
        ),
    ):
        super().__init__(col_name=col_name, obj_name=obj_name, repository_config=repository_config)
