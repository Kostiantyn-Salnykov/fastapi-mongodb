![GitHub](https://img.shields.io/github/license/KosT-NavySky/fastapi-mongodb)
![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/Kost-NavySky/fastapi-mongodb/Python%20package/master)
![GitHub last commit (branch)](https://img.shields.io/github/last-commit/kost-navysky/fastapi-mongodb/master)
![Codecov](https://img.shields.io/codecov/c/github/kost-navysky/fastapi-mongodb)
[![](https://img.shields.io/badge/code%20style-black-000000?style=flat)](https://github.com/psf/black)
![PyPI - Downloads](https://img.shields.io/pypi/dm/fastapi-mongodb)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/fastapi-mongodb)
![PyPI](https://img.shields.io/pypi/v/fastapi-mongodb)

# fastapi-mongodb

## Requirements

- Python 3.9 +
- poetry

## Tests

```
poetry run pytest
```

## Coverage

```
poetry run coverage run -m pytest
poetry coverage report
```

## Roadmap

- ➕ BaseModel (data container and to_db / from_db)
- ➕ BaseSchema (request / response validation and serialization)
- ➕ BaseRepository (CRUD operations for the DB)
- ➕ BaseRepositoryConfig (customization for Repository logic)
- ➕ TokensHandler (encode / decode and validate JWT tokens)
- ➕ PasswordsHandler (password hashing and password checking)
- ➕ settings.py (get base config from .env)
- ➕ BaseLogger (debug logger and simple logger)
- ➕ DB profiling and monitoring
- ➕ Application setup (config.py, indexes, collection setup)
- ➕ Tests and test environment (test DB configuration)
- ➕ Model Factories (factory_boy)
- ➕➖ Pagination (?limit, ?offset, ?latest_id)
- ➕➖ Sorting (?orderBy)
- ➕➖ Projectors (?showFields, ?hideFields)
- ➕➖ Trace memory allocations (tracemalloc)
- ➕➖ BaseProfiler (decorator and context manager and metaclass / cProfile)
- ➕➖ manage.py commands (setup apps / create apps etc)
- ➕➖ .Dockerfile and docker-compose.yaml
- ➕➖ DB setup (db management, db level commands)
- ➖ DB User management commands (append to manage.py)
- ➖ DB ReplicaSet setup + docker-compose.yaml
- ➖ DB migrations handler (migrations running and tracking)
- ➖ DB dump/restore
- ➖ Filters ("Depends" classes maybe DB applicable)
- ➖ Change email flow
- ➖ Change password flow
- ➖ Reset password flow
- ➖ Load testing with Locust
- ➖ Login with Google, Facebook, Twitter
- ➖ .csv / .xlsx Handlers
- ➖ Background tasks (Redis + celery/celery-beat)

