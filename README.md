![GitHub Workflow Status (branch)](https://img.shields.io/github/workflow/status/Kost-NavySky/fastapi_mongodb/Python%20package/master)
![GitHub](https://img.shields.io/github/license/KosT-NavySky/fastapi_mongodb)
[![codecov](https://codecov.io/gh/KosT-NavySky/fastapi_mongodb/branch/master/graph/badge.svg)](https://codecov.io/gh/KosT-NavySky/fastapi_mongodb)
[![](https://img.shields.io/badge/code%20style-black-000000?style=flat)](https://github.com/psf/black)

# fastapi_mongodb

## Requirements

- Python 3.9 +
- poetry
- Docker, docker-compose

## Setup

```sh
docker-compose up
poetry install
python run.py
```

## Tests

```
python -m unittest discover
```

## Coverage

```
coverage run -m unittest discover
coverate report
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
- ➕ Pagination (?limit, ?offset)
- ➕➖ Sorting (?orderBy)
- ➕➖ Projectors (?showFields, ?hideFields)
- ➕➖ Trace memory allocations (tracemalloc)
- ➕➖ BaseProfiler (decorator and context manager / cProfile)
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

