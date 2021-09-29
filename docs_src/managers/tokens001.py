import datetime

import fastapi_mongodb

SECRET_KEY = "SUPER SECURE TOKEN FROM ENVIRONMENT VARIABLES!!!"

tokens_manager = fastapi_mongodb.TokensManager(
    secret_key=SECRET_KEY,
    algorithm=fastapi_mongodb.TOKEN_ALGORITHMS.HS256,
    default_token_lifetime=datetime.timedelta(minutes=30),
)

token_data = {
    "anyKey": "Not Secure",
    "anotherKey": "All data available to Front-end and JWT clients!!!",
}

jwt_token = tokens_manager.create_code(
    data=token_data, aud="test_audience", iss="test_issuer"
)

parsed_token = tokens_manager.read_code(
    code=jwt_token, aud="test_audience", iss="test_issuer"
)
