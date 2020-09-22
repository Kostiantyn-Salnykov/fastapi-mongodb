from apps.common.bases import BaseRepository
from apps.users.config import users_settings

__all__ = ["UserRepository"]


class UserRepository(BaseRepository):
    def __init__(self, col_name: str = users_settings.USERS_COL, obj_name: str = "User", **kwargs):
        super().__init__(col_name=col_name, obj_name=obj_name, **kwargs)
