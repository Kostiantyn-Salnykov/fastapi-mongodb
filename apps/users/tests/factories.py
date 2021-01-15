import factory.fuzzy

from apps.common.enums import CodeAudiences
from apps.users.models import UserCode, UserModel


class UserCodeFactory(factory.Factory):
    code = factory.Faker("pystr")
    type = factory.fuzzy.FuzzyChoice(choices=CodeAudiences)

    class Meta:
        model = UserCode


class UserFactory(factory.Factory):
    email = factory.Faker("email")

    class Meta:
        model = UserModel
