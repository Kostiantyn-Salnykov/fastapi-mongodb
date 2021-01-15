import binascii
import datetime
import hashlib
import secrets
import typing

import authlib.jose

import bases
import settings

__all__ = ["PasswordsHandler", "TokensHandler"]

from apps.common.enums import CodeAudiences


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
        sub: str = "",  # Subject
        iss: str = "",  # Issuer
        jti: str = "",  # JWT ID
        header: dict[str, typing.Union[str, int, bool]] = None,  # JWT header, eg: {"alg": "HS256"}
        check: bool = True,  # checks for sensitive data
    ) -> str:
        if data is None:
            data = {}
        now = bases.helpers.utc_now()
        if iat is None:
            iat = now
        if exp is None:
            exp = now + datetime.timedelta(minutes=30)
        if nbf is None:
            nbf = now
        if header is None:
            header = {"alg": "HS512"}
        payload = data.copy()
        payload |= {"iat": iat, "aud": aud, "exp": exp, "nbf": nbf, "iss": iss, "sub": sub, "jti": jti}
        return authlib.jose.jwt.encode(
            header=header, payload=payload, key=settings.Settings.SECRET_KEY, check=check
        ).decode("utf-8")

    @classmethod
    def read_code(
        cls,
        *,
        code: str,
        aud: CodeAudiences = CodeAudiences.ACCESS_TOKEN,  # Audience
        sub: str = "",  # Subject
        iss: str = "",  # Issuer
        jti: str = "",  # JWT ID,
        now: datetime.datetime = None,
        leeway: int = 0,  # provide extra time in seconds to validate (iat, exp, nbf)
        convert_to: typing.Type[bases.schemas.BaseSchema] = None,
    ):
        now = int(bases.helpers.as_utc(date_time=now).timestamp() if now else bases.helpers.utc_now().timestamp())
        try:
            payload = authlib.jose.jwt.decode(
                s=code.encode("utf-8"),
                key=settings.Settings.SECRET_KEY,
                claims_options={
                    "sub": {"value": sub},
                    "aud": {"value": aud},
                    "iss": {"value": iss},
                    "jti": {"value": jti},
                },
            )
            payload.validate(now=now, leeway=leeway)
            if convert_to is not None:
                payload = convert_to(**payload)  # noqa
        except authlib.jose.errors.JoseError as error:
            raise bases.exceptions.HandlerException(error.description)
        else:
            return payload
