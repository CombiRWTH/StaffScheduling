IMAGE_NAME := "staff-scheduling-api"
PORT := "8000"

# Shared Docker args for dev commands
DOCKER_DEV_ARGS := "--env-file api/.env -v $PWD/api/app:/app/app -v $PWD/api/tests:/app/tests -v $PWD/api/found_solutions:/app/found_solutions -v $PWD/api/processed_solutions:/app/processed_solutions" + " -p " + PORT + ":8000"

_default:
    just --list

sync:
    cd api && uv sync --frozen --all-extras
    cd webapp && npm ci

lint *args:
    cd api && uv run ruff check . {{args}}

format *args:
    cd api && uv run ruff format . {{args}}

typecheck *args:
    cd api && uv run pyright . {{args}}

test *args:
    cd api && uv run python -m pytest {{args}}

check: lint typecheck test

build:
    docker build -t {{IMAGE_NAME}} api

run:
    docker run --rm -it \
        {{DOCKER_DEV_ARGS}} \
        {{IMAGE_NAME}} \
        uv run \
            fastapi dev \
            app/main.py \
            --host 0.0.0.0 --port 8000

debug:
    docker run --rm -it \
        {{DOCKER_DEV_ARGS}} \
        -p 5678:5678 \
        {{IMAGE_NAME}} \
        uv run \
            python -m debugpy \
            --listen 0.0.0.0:5678 \
            --wait-for-client \
            -m fastapi dev \
            app/main.py \
            --host 0.0.0.0 --port 8000

docker-shell:
    docker run --rm -it \
        {{DOCKER_DEV_ARGS}} \
        {{IMAGE_NAME}} \
        bash

health:
    curl http://localhost:{{PORT}}/status

# Starts the container in the background and keeps it alive
up:
    docker run -d --name {{IMAGE_NAME}}-dev \
        {{DOCKER_DEV_ARGS}} \
        {{IMAGE_NAME}} \
        tail -f /dev/null

# Runs a command inside the running container
exec *args:
    docker exec -it {{IMAGE_NAME}}-dev uv run {{args}}

# Stops the background container
down:
    docker stop {{IMAGE_NAME}}-dev && docker rm {{IMAGE_NAME}}-dev

# Native host startup; connected Compose startup is introduced in the foundation pass.
api-dev:
    cd api && uv run fastapi dev app/main.py --host 127.0.0.1 --port 8000

webapp-dev:
    cd webapp && npm run dev

webapp-build:
    cd webapp && npm run build

docs:
    cd api && uv run --extra docs mkdocs serve -f ../mkdocs.yml

docs-check:
    cd api && uv run --extra docs mkdocs build --strict -f ../mkdocs.yml
