# muenster-jetzt database management, data import, and API

Based on [Django](https://www.djangoproject.com/), [Django REST
framework](https://www.django-rest-framework.org/), and
[Scrapy](https://scrapy.org/).

## Development setup for backend

All following commands are to be executed from the `backend` folder of this repository.

### 1. Setup Python with virtual environment

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Install Python and all dependencies into a virtual environment in `backend/.venv`: `uv sync`

   uv picks a Python version matching `requires-python` in `pyproject.toml` (3.14) and downloads it if necessary.
   Dependency versions are pinned in `uv.lock`.

### 2. Initialize Database

1. Configure environmental variables, based on example:

    ```bash
    cp .env.example .env
    ```

   Optionally, these variables and credentials can be changed. But development will work without any change, too.
2. Start database: `docker compose up -d db`
3. Migrate your database: `uv run ./manage.py migrate`
4. Crawl events and store them in the database: `uv run ./manage.py crawl [crawler_name]`
5. Start the API: `uv run ./manage.py runserver 0.0.0.0:8000`

Instead of prefixing every command with `uv run`, you can also activate the virtual environment with `source .venv/bin/activate`.

### 3. Check code style and types

[Ruff](https://docs.astral.sh/ruff/) lints and formats the code, [ty](https://docs.astral.sh/ty/) checks types:

```bash
uv run ruff check
uv run ruff format
uv run ty check
```

These checks, and `uv lock`, also run as Git pre-commit hooks (see `.pre-commit-config.yaml` in the repository root).
Install [prek](https://prek.j178.dev/) (e.g. `uv tool install prek`) and activate the hooks once from the repository root:

```bash
prek install
```

### DEPRECATED ALTERNATIVE: Develop in a container

Change into the `backend` directory.

To open a shell inside a container with all dependencies installed, run:

```bash
# do this only once or if your dependencies (uv.lock) change
docker build -t muenster-jetzt-backend -f deployment/Dockerfile.prod .
# start a container
docker run --rm -it -v $(pwd):/app:Z --entrypoint /bin/bash --network muenster-jetzt_default -p 8000:8000 --env-file .env muenster-jetzt-backend
```

## General information

### Database schema

The database schema is managed via Django. If you need to alter it, just add a
new model in `events/models.py` (or edit an existing one) and run `uv run
./manage.py makemigrations` to create a new migration.

### Naming Convention

Whenever you need to name a property, try to use the name that is used in <https://schema.org/> e.g. for events take a look at: <https://schema.org/Event>

### Dependency management

This project uses [uv](https://docs.astral.sh/uv/) to make sure all deployments are using exactly the same dependency versions.
Only direct dependencies are declared in `pyproject.toml`, the exact versions of all (including transitive) dependencies are pinned in `uv.lock`.
Commit both files.

```bash
# add a new dependency for production use (updates pyproject.toml and uv.lock)
uv add <name>
# add a new dependency for development only
uv add --dev <name>
# remove a dependency
uv remove <name>
# upgrade all dependencies within the constraints of pyproject.toml
uv lock --upgrade
# upgrade only the requested package
uv lock --upgrade-package <name>
# update installed dependencies after the lock file changed
uv sync
```

## Troubleshooting

### Backend has trouble connecting to the database

```bash
# Do this to debug the database container
docker ps                                 # find out name of db container
docker exec -it $containername bash       # log into db container
env                                       # check if env variables are ok

# If you changed the credentials in .env file, recreate db container:
docker compose down db -v
docker compose up db
```

### Database container does not start after the upgrade to PostgreSQL 18

The data of the previous PostgreSQL 12 container cannot be used by PostgreSQL 18.
Recreate the database container (this deletes the local data), then migrate and crawl again:

```bash
docker compose down db -v
docker compose up -d db
```
