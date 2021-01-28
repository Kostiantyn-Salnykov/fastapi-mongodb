# fastapi_mongodb

## Requirements

- Python 3.9 +
- pipenv
- Docker, docker-compose

## Setup

```sh
docker-compose up
pipenv install
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
- ➖ Login with Google, Facebook, Twitter
- ➕➖ manage.py commands (setup apps / create apps etc)
- ➕ settings.py (get base config from .env)
- ➕ BaseLogger (debug logger and simple logger)
- ➕➖ DB setup (db management, db level commands)
- ➕ DB profiling and monitoring
- ➕ Application setup (config.py, indexes, collection setup)
- ➕ Tests and test environment (test DB configuration)
- ➖ Load testing with Locust
- ➕➖ .Dockerfile and docker-compose.yaml
- ➕➖ Sorting (?orderBy)
- ➕ Pagination (?limit, ?offset)
- ➕➖ Projectors (?showFields, ?hideFields)
- ➖ Filters ("Depends" classes maybe DB applicable)
- ➖ Change email flow
- ➖ Change password flow
- ➖ Reset password flow
- ➖ DB ReplicaSet setup + docker-compose.yaml
- ➖ DB User management commands (Makefile)
- ➕➖ Trace memory allocations (tracemalloc)
- ➕➖ BaseProfiler (decorator and context manager / cProfile)
- ➕ Model Factories (factory_boy)
- ➖ .csv / .xlsx Handlers 
