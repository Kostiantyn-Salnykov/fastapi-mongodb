from enum import Enum


class UserRoles(str, Enum):
    CLIENT = "client"
    STAFF = "staff"
    ADMIN = "admin"
