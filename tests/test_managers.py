import datetime

import pytest

import fastapi_mongodb.exceptions
import fastapi_mongodb.helpers
import fastapi_mongodb.managers
import fastapi_mongodb.schemas


class TestPasswordsHandler:
    def _manager_factory(self, algorithm: fastapi_mongodb.managers.PASSWORD_ALGORITHMS):
        return fastapi_mongodb.managers.PasswordsManager(algorithm=algorithm, iterations=1)

    @pytest.mark.parametrize(
        argnames=["algorithm", "faker"],
        argvalues=[(algorithm, "faker") for algorithm in fastapi_mongodb.managers.PASSWORD_ALGORITHMS],
        indirect=["faker"],
    )
    def test_make_password(self, algorithm: fastapi_mongodb.managers.PASSWORD_ALGORITHMS, faker):
        fake_password = faker.pystr()
        hash_length = fastapi_mongodb.managers.ALGORITHMS_LENGTH_MAP[algorithm] * 2  # SALT + HASH
        manager = self._manager_factory(algorithm=algorithm)

        password_hash = manager.make_password(password=fake_password)

        assert len(password_hash) == hash_length
        assert isinstance(password_hash, str)

    @pytest.mark.parametrize(
        argnames=["algorithm", "faker"],
        argvalues=[(algorithm, "faker") for algorithm in fastapi_mongodb.managers.PASSWORD_ALGORITHMS],
        indirect=["faker"],
    )
    def test_check_password(self, algorithm: fastapi_mongodb.managers.PASSWORD_ALGORITHMS, faker):
        fake_password = faker.pystr()
        fake_password_2 = faker.pystr()
        manager = self._manager_factory(algorithm=algorithm)
        fake_password_hash = manager.make_password(password=fake_password)
        fake_password_hash_2 = manager.make_password(password=fake_password_2)

        assert manager.check_password(password=fake_password, password_hash=fake_password_hash) is True
        assert manager.check_password(password=fake_password_2, password_hash=fake_password_hash_2) is True
        assert manager.check_password(password=fake_password, password_hash=fake_password_hash_2) is False
        assert manager.check_password(password=fake_password_2, password_hash=fake_password_hash) is False


class TestTokensManager:
    class MockPayload(fastapi_mongodb.schemas.BaseSchema):
        # JWT options
        iss: str
        iat: datetime.datetime
        exp: datetime.datetime
        nbf: datetime.datetime

        int_key: int
        float_key: float
        bool_key: bool
        str_key: str
        list_key: list
        dict_key: dict

    def test_data(self, faker):
        return {
            "int_key": faker.pyint(),
            "float_key": faker.pyfloat(),
            "bool_key": faker.pybool(),
            "str_key": faker.pystr(),
            "list_key": faker.pylist(nb_elements=10, variable_nb_elements=True, value_types=[int, float, bool, str]),
            "dict_key": faker.pydict(nb_elements=10, variable_nb_elements=True, value_types=[int, float, bool, str]),
        }

    @staticmethod
    def generate_issuer(faker):
        return {"iss": faker.pystr()}

    @staticmethod
    def _manager_factory(algorithm):
        return fastapi_mongodb.managers.TokensManager(secret_key="TEST", algorithm=algorithm)

    @staticmethod
    def _get_default_claims():
        return ["aud", "exp", "iat", "iss", "nbf"]

    @pytest.mark.parametrize(
        argnames=["algorithm"], argvalues=[(algorithm,) for algorithm in fastapi_mongodb.managers.TOKEN_ALGORITHMS]
    )
    def test_create_read_code_default(self, algorithm: fastapi_mongodb.managers.TOKEN_ALGORITHMS):
        manager = self._manager_factory(algorithm=algorithm)
        code = manager.create_code()

        parsed = manager.read_code(code=code)

        assert isinstance(code, str)
        assert isinstance(parsed, dict)
        assert all(field in parsed for field in self._get_default_claims())

    @pytest.mark.parametrize(
        argnames=["algorithm", "faker"],
        argvalues=[(algorithm, "faker") for algorithm in fastapi_mongodb.managers.TOKEN_ALGORITHMS],
        indirect=["faker"],
    )
    def test_create_read_code_custom(self, algorithm: fastapi_mongodb.managers.TOKEN_ALGORITHMS, faker):
        now = fastapi_mongodb.helpers.utc_now()
        test_data = self.test_data(faker=faker)
        custom_claims = self.generate_issuer(faker=faker)
        audience = faker.pystr()
        test_data |= custom_claims
        manager = self._manager_factory(algorithm=algorithm)

        code = manager.create_code(data=test_data, iat=now, exp=now, nbf=now, aud=audience, **custom_claims)

        parsed = manager.read_code(
            code=code, aud=audience, leeway=faker.pyint(), convert_to=self.MockPayload, **custom_claims
        )

        assert isinstance(code, str)
        assert isinstance(parsed, self.MockPayload)
        assert test_data == parsed.dict(include={key for key in test_data.keys()})

    @pytest.mark.parametrize(
        argnames=["algorithm"],
        argvalues=[(algorithm,) for algorithm in fastapi_mongodb.managers.TOKEN_ALGORITHMS],
    )
    def test_read_code_exception_exp(self, algorithm: fastapi_mongodb.managers.TOKEN_ALGORITHMS):
        manager = self._manager_factory(algorithm=algorithm)
        code = manager.create_code(exp=fastapi_mongodb.helpers.utc_now() - datetime.timedelta(seconds=5))

        with pytest.raises(expected_exception=fastapi_mongodb.exceptions.ManagerException) as exception_context:
            manager.read_code(code=code)

        assert "Expired JWT token." == str(exception_context.value)

    @pytest.mark.parametrize(
        argnames=["algorithm"],
        argvalues=[(algorithm,) for algorithm in fastapi_mongodb.managers.TOKEN_ALGORITHMS],
    )
    def test_read_code_exception_nbf(self, algorithm: fastapi_mongodb.managers.TOKEN_ALGORITHMS):
        manager = self._manager_factory(algorithm=algorithm)
        code = manager.create_code(nbf=fastapi_mongodb.helpers.utc_now() + datetime.timedelta(seconds=5))

        with pytest.raises(expected_exception=fastapi_mongodb.exceptions.ManagerException) as exception_context:
            manager.read_code(code=code)

        assert "The token is not valid yet." == str(exception_context.value)

    @pytest.mark.parametrize(
        argnames=["algorithm"],
        argvalues=[(algorithm,) for algorithm in fastapi_mongodb.managers.TOKEN_ALGORITHMS],
    )
    def test_read_code_exception_leeway(self, algorithm: fastapi_mongodb.managers.TOKEN_ALGORITHMS):
        manager = self._manager_factory(algorithm=algorithm)
        code = manager.create_code(exp=fastapi_mongodb.helpers.utc_now() - datetime.timedelta(seconds=5))

        parsed = manager.read_code(code=code, leeway=5)
        with pytest.raises(expected_exception=fastapi_mongodb.exceptions.ManagerException) as exception_context:
            manager.read_code(code=code)

        assert "Expired JWT token." == str(exception_context.value)
        assert isinstance(parsed, dict)

    @pytest.mark.parametrize(
        argnames=["algorithm"],
        argvalues=[(algorithm,) for algorithm in fastapi_mongodb.managers.TOKEN_ALGORITHMS],
    )
    def test_read_code_exception_aud(self, algorithm: fastapi_mongodb.managers.TOKEN_ALGORITHMS):
        manager = self._manager_factory(algorithm=algorithm)
        code = manager.create_code(aud="TEST")

        with pytest.raises(expected_exception=fastapi_mongodb.exceptions.ManagerException) as exception_context:
            manager.read_code(code=code)

        assert "Invalid JWT audience." == str(exception_context.value)

    @pytest.mark.parametrize(
        argnames=["algorithm"],
        argvalues=[(algorithm,) for algorithm in fastapi_mongodb.managers.TOKEN_ALGORITHMS],
    )
    def test_read_code_exception_iss(self, algorithm: fastapi_mongodb.managers.TOKEN_ALGORITHMS):
        manager = self._manager_factory(algorithm=algorithm)
        code = manager.create_code(iss="TEST")

        with pytest.raises(expected_exception=fastapi_mongodb.exceptions.ManagerException) as exception_context:
            manager.read_code(code=code)

        assert "Invalid JWT issuer." == str(exception_context.value)

    @pytest.mark.parametrize(
        argnames=["algorithm", "faker"],
        argvalues=[(algorithm, "faker") for algorithm in fastapi_mongodb.managers.TOKEN_ALGORITHMS],
        indirect=["faker"],
    )
    def test_read_code_exception_invalid_jwt(self, algorithm: fastapi_mongodb.managers.TOKEN_ALGORITHMS, faker):
        manager = self._manager_factory(algorithm=algorithm)

        with pytest.raises(expected_exception=fastapi_mongodb.exceptions.ManagerException) as exception_context:
            manager.read_code(code=faker.pystr())

        assert "Invalid JWT." == str(exception_context.value)
