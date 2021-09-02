import binascii
import datetime
import enum
import hashlib
import secrets
import typing

import jwt

import fastapi_mongodb.exceptions
import fastapi_mongodb.helpers
import fastapi_mongodb.schemas

__all__ = ["PASSWORD_ALGORITHMS", "PasswordsManager", "TokensManager"]


class PASSWORD_ALGORITHMS(str, enum.Enum):
    SHA256 = "sha256"
    SHA384 = "sha384"
    SHA512 = "sha512"


ALGORITHMS_LENGTH_MAP = {
    PASSWORD_ALGORITHMS.SHA256: 64,
    PASSWORD_ALGORITHMS.SHA384: 96,
    PASSWORD_ALGORITHMS.SHA512: 128,
}
ALGORITHMS_METHODS_MAP = {
    PASSWORD_ALGORITHMS.SHA256: hashlib.sha256,
    PASSWORD_ALGORITHMS.SHA384: hashlib.sha384,
    PASSWORD_ALGORITHMS.SHA512: hashlib.sha512,
}


class TOKEN_ALGORITHMS(str, enum.Enum):
    HS256 = "HS256"
    HS384 = "HS384"
    HS512 = "HS512"


class PasswordsManager:
    def __init__(self, algorithm: PASSWORD_ALGORITHMS = PASSWORD_ALGORITHMS.SHA512, iterations: int = 524288):
        self._algorithm = algorithm
        self._algorithm_length = ALGORITHMS_LENGTH_MAP[self._algorithm]
        self.iterations = iterations

    def __repr__(self):
        return f"{self.__class__.__name__}(algorithm={self._algorithm}, iterations={self.iterations})"

    def __hash(self, *, salt: str, password: str, encoding: str = "UTF-8") -> str:
        """Make hash for password N length string (default length from algorithm)"""
        password_hash = hashlib.pbkdf2_hmac(
            hash_name=self._algorithm,
            password=password.encode(encoding=encoding),
            salt=salt.encode(encoding=encoding),
            iterations=self.iterations,
        )
        password_hash = binascii.hexlify(password_hash).decode(encoding)
        return password_hash

    def __generate_salt(self) -> str:
        """Returns N length string (default length from algorithm)"""
        method = ALGORITHMS_METHODS_MAP[self._algorithm]
        return method(string=secrets.token_bytes(nbytes=64)).hexdigest()  # noqa

    def check_password(self, *, password: str, password_hash: str) -> bool:
        """Check password and hash"""
        salt = password_hash[: self._algorithm_length]
        stored_password_hash = password_hash[self._algorithm_length :]
        check_password_hash = self.__hash(salt=salt, password=password)
        return check_password_hash == stored_password_hash

    def make_password(self, *, password: str) -> str:
        """Make hash from password"""
        salt: str = self.__generate_salt()
        new_password_hash: str = self.__hash(salt=salt, password=password)
        return salt + new_password_hash


class TokensManager:
    def __init__(
        self,
        secret_key: str,
        algorithm: TOKEN_ALGORITHMS = TOKEN_ALGORITHMS.HS256,
        default_token_lifetime: datetime.timedelta = datetime.timedelta(minutes=30),
    ):
        self._secret_key = secret_key
        self._algorithm = algorithm
        self.default_token_lifetime = default_token_lifetime

    def create_code(
        self,
        *,
        data: dict[str, typing.Union[str, int, float, dict, list, bool]] = None,
        aud: str = "access",  # Audience
        iat: datetime.datetime = None,  # Issued at datetime
        exp: datetime.datetime = None,  # Expired at datetime
        nbf: datetime.datetime = None,  # Not before datetime
        iss: str = "",  # Issuer
    ) -> str:
        if data is None:
            data = {}
        now = fastapi_mongodb.helpers.utc_now()
        if iat is None:
            iat = now
        if exp is None:
            exp = now + self.default_token_lifetime
        if nbf is None:
            nbf = now
        payload = data.copy()
        payload |= {"iat": iat, "aud": aud, "exp": exp, "nbf": nbf, "iss": iss}
        return jwt.encode(payload=payload, key=self._secret_key, algorithm=self._algorithm)

    def read_code(
        self,
        *,
        code: str,
        aud: str = "access",  # Audience
        iss: str = "",  # Issuer
        leeway: int = 0,  # provide extra time in seconds to validate (iat, exp, nbf)
        convert_to: typing.Type[fastapi_mongodb.schemas.BaseSchema] = None,
    ):
        try:
            payload = jwt.decode(
                jwt=code,
                key=self._secret_key,
                algorithms=[self._algorithm],
                leeway=leeway,
                audience=aud,
                issuer=iss,
            )
            if convert_to is not None:
                payload = convert_to(**payload)  # noqa
        except jwt.exceptions.InvalidIssuerError as error:
            raise fastapi_mongodb.exceptions.ManagerException("Invalid JWT issuer.") from error
        except jwt.exceptions.InvalidAudienceError as error:
            raise fastapi_mongodb.exceptions.ManagerException("Invalid JWT audience.") from error
        except jwt.exceptions.ExpiredSignatureError as error:
            raise fastapi_mongodb.exceptions.ManagerException("Expired JWT token.") from error
        except jwt.exceptions.ImmatureSignatureError as error:
            raise fastapi_mongodb.exceptions.ManagerException("The token is not valid yet.") from error
        # base error exception from pyjwt
        except jwt.exceptions.PyJWTError as error:
            raise fastapi_mongodb.exceptions.ManagerException("Invalid JWT.") from error
        else:
            return payload
