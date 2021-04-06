import binascii
import datetime
import hashlib
import secrets
import typing

import jwt

import settings
from apps.common.enums import CodeAudiences
from bases.exceptions import HandlerException
from bases.helpers import utc_now
from bases.schemas import BaseSchema

__all__ = ["PasswordsHandler", "TokensHandler"]


class PasswordsHandler:
    iterations: int = 524288  # just a geometric sequence 😉
    algorithm: str = "sha512"
    algorithm_length: int = 128  # length of 'sha512'

    @classmethod
    def __hash(cls, *, salt: str, password: str, encoding: str = "UTF-8") -> str:
        """Make hash for password 128 length string (default length from sha512 algorithm)"""
        password_hash = hashlib.pbkdf2_hmac(
            hash_name="sha512",
            password=password.encode(encoding=encoding),
            salt=salt.encode(encoding=encoding),
            iterations=cls.iterations,
        )
        password_hash = binascii.hexlify(password_hash).decode("UTF-8")
        return password_hash

    @staticmethod
    def __generate_salt() -> str:
        """Returns 128 length string (default length from sha512 algorithm)"""
        return hashlib.sha512(string=secrets.token_bytes(nbytes=64)).hexdigest()  # noqa

    @classmethod
    def check_password(cls, *, password: str, password_hash: str) -> bool:
        """Check password and hash"""
        salt = password_hash[: cls.algorithm_length]
        stored_password_hash = password_hash[cls.algorithm_length :]
        check_password_hash = cls.__hash(salt=salt, password=password)
        return check_password_hash == stored_password_hash

    @classmethod
    def make_password(cls, *, password: str) -> str:
        """Make hash from password (default length is 128)"""
        salt: str = cls.__generate_salt()
        new_password_hash: str = cls.__hash(salt=salt, password=password)
        return salt + new_password_hash


class TokensHandler:
    @classmethod
    def create_code(
        cls,
        *,
        data: dict[str, typing.Union[str, int, float, dict, list, bool]] = None,
        aud: CodeAudiences = CodeAudiences.ACCESS_TOKEN,  # Audience
        iat: datetime.datetime = None,  # Issued at datetime
        exp: datetime.datetime = None,  # Expired at datetime
        nbf: datetime.datetime = None,  # Not before datetime
        iss: str = "",  # Issuer
    ) -> str:
        if data is None:
            data = {}
        now = utc_now()
        if iat is None:
            iat = now
        if exp is None:
            exp = now + datetime.timedelta(minutes=30)
        if nbf is None:
            nbf = now
        payload = data.copy()
        payload |= {"iat": iat, "aud": aud, "exp": exp, "nbf": nbf, "iss": iss}
        return jwt.encode(payload=payload, key=settings.Settings.SECRET_KEY, algorithm="HS512")

    @classmethod
    def read_code(
        cls,
        *,
        code: str,
        aud: CodeAudiences = CodeAudiences.ACCESS_TOKEN,  # Audience
        iss: str = "",  # Issuer
        leeway: int = 0,  # provide extra time in seconds to validate (iat, exp, nbf)
        convert_to: typing.Type[BaseSchema] = None,
    ):
        try:
            payload = jwt.decode(
                jwt=code,
                key=settings.Settings.SECRET_KEY,
                algorithms=["HS512"],
                leeway=leeway,
                audience=aud,
                issuer=iss,
            )
            if convert_to is not None:
                payload = convert_to(**payload)  # noqa
        except jwt.exceptions.InvalidIssuerError as error:
            raise HandlerException("Invalid JWT issuer.") from error
        except jwt.exceptions.InvalidAudienceError as error:
            raise HandlerException("Invalid JWT audience.") from error
        except jwt.exceptions.ExpiredSignatureError as error:
            raise HandlerException("Expired JWT token.") from error
        except jwt.exceptions.ImmatureSignatureError as error:
            raise HandlerException("The token is not valid yet.") from error
        # base error exception from pyjwt
        except jwt.exceptions.PyJWTError as error:
            raise HandlerException("Invalid JWT.") from error
        else:
            return payload
