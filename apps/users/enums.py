import enum


class UserRoles(str, enum.Enum):
    CLIENT = "client"
    STAFF = "staff"
    ADMIN = "admin"
