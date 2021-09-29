import fastapi_mongodb

passwords_manager = fastapi_mongodb.PasswordsManager(
    algorithm=fastapi_mongodb.PASSWORD_ALGORITHMS.SHA512, iterations=524288
)

raw_password = "SUPER SECURE PASSWORD!"
password_hash = passwords_manager.make_password(password=raw_password)
if passwords_manager.check_password(
    password=raw_password, password_hash=password_hash
):
    print("""ALLOW ACCESS!""")
else:
    print("""ACCESS DENIED!""")
