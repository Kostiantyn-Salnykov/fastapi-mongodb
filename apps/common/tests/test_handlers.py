import datetime
import typing

import jwt
from apps.common.enums import CodeAudiences
import bases
from apps.common.handlers import PasswordsHandler, TokensHandler


class TestPasswordsHandler(bases.helpers.AsyncTestCaseWithPathing):
    def setUp(self) -> None:
        self.passwords_handler = PasswordsHandler()

    def test_make_password(self):
        expected_length = 128 + 128  # 128 for salt and 128 for password's hash
        password = self.faker.pystr()

        result = self.passwords_handler.make_password(password=password)

        self.assertNotEqual(password, result)
        self.assertEqual(expected_length, len(result))

    def test_check_password_true(self):
        password = self.faker.pystr()
        password_hash = self.passwords_handler.make_password(password=password)

        result = self.passwords_handler.check_password(password=password, password_hash=password_hash)

        self.assertTrue(result)

    def test_check_password_false(self):
        password = self.faker.pystr()
        other_password = self.faker.pystr()
        password_hash = self.passwords_handler.make_password(password=password)

        result = self.passwords_handler.check_password(password=other_password, password_hash=password_hash)

        self.assertFalse(result)


class TestTokensHandler(bases.helpers.AsyncTestCaseWithPathing):
    class TestModel(bases.schemas.BaseSchema):
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

    def setUp(self) -> None:
        self.tokens_handler = TokensHandler()

    def get_test_data(self):
        return {
            "int_key": self.faker.pyint(),
            "float_key": self.faker.pyfloat(),
            "bool_key": self.faker.pybool(),
            "str_key": self.faker.pystr(),
            "list_key": self.faker.pylist(
                nb_elements=10, variable_nb_elements=True, value_types=[int, float, bool, str]
            ),
            "dict_key": self.faker.pydict(
                nb_elements=10, variable_nb_elements=True, value_types=[int, float, bool, str]
            ),
        }

    def get_custom_claims(self):
        return {"iss": self.faker.pystr()}

    def test_create_read_code_default(self):
        code = self.tokens_handler.create_code()

        parsed: dict = self.tokens_handler.read_code(code=code)

        self.assertIsInstance(code, str)
        self.assertIsInstance(parsed, dict)

    def test_create_read_code_custom(self):
        test_data = self.get_test_data()
        now = bases.helpers.utc_now()
        custom_claims = self.get_custom_claims()
        test_data |= custom_claims

        code = self.tokens_handler.create_code(
            data=test_data,
            iat=now,
            exp=now,
            nbf=now,
            aud=CodeAudiences.EMAIL_RESET,
            **custom_claims
        )

        parsed = self.tokens_handler.read_code(
            code=code,
            aud=CodeAudiences.EMAIL_RESET,
            leeway=self.faker.pyint(),
            convert_to=self.TestModel,
            **custom_claims
        )

        self.assertIsInstance(code, str)
        self.assertIsInstance(parsed, self.TestModel)  # convert_to kwarg
        self.assertDictEqual(test_data, parsed.dict(include={key for key in test_data.keys()}))

    def test_read_code_exception_exp(self):
        now = bases.helpers.utc_now()
        code = self.tokens_handler.create_code(exp=now - datetime.timedelta(seconds=1))

        with self.assertRaises(expected_exception=bases.exceptions.HandlerException) as exception_context:
            self.tokens_handler.read_code(code=code)
        self.assertEqual("Expired JWT token.", str(exception_context.exception))

    def test_read_code_exception_nbf(self):
        now = bases.helpers.utc_now()
        code = self.tokens_handler.create_code(nbf=now + datetime.timedelta(seconds=1))

        with self.assertRaises(expected_exception=bases.exceptions.HandlerException) as exception_context:
            self.tokens_handler.read_code(code=code)
        self.assertEqual("The token is not valid yet.", str(exception_context.exception))

    def test_read_code_leeway(self):
        now = bases.helpers.utc_now()
        code = self.tokens_handler.create_code(exp=now - datetime.timedelta(seconds=1))

        parsed = self.tokens_handler.read_code(code=code, leeway=1)
        with self.assertRaises(expected_exception=bases.exceptions.HandlerException) as exception_context:
            self.tokens_handler.read_code(code=code)

        self.assertEqual("Expired JWT token.", str(exception_context.exception))
        self.assertIsInstance(parsed, dict)

    def test_read_code_exception_aud(self):
        code = self.tokens_handler.create_code()

        with self.assertRaises(expected_exception=bases.exceptions.HandlerException) as exception_context:
            self.tokens_handler.read_code(code=code, aud=CodeAudiences.REFRESH_TOKEN)

        self.assertEqual("Invalid JWT audience.", str(exception_context.exception))

    def test_read_code_exception_iss(self):
        code = self.tokens_handler.create_code(iss=self.faker.pystr())

        with self.assertRaises(expected_exception=bases.exceptions.HandlerException) as exception_context:
            self.tokens_handler.read_code(code=code)

        self.assertEqual("Invalid JWT issuer.", str(exception_context.exception))

    def test_read_code_exception_invalid_jwt(self):
        with self.assertRaises(expected_exception=bases.exceptions.HandlerException) as exception_context:
            self.tokens_handler.read_code(code=self.faker.pystr())

        self.assertEqual("Invalid JWT.", str(exception_context.exception))
