APP_NAME := "staff-scheduling-api"
IMAGE_NAME := "staff-scheduling-api"
PORT := "8000"

# Shared Docker args for dev commands
DOCKER_DEV_ARGS := "-p " + PORT + ":8000 --env-file .env -v $PWD:/app -v staff-scheduling-venv:/app/.venv -v staff-scheduling-uv-cache:/root/.cache/uv"

_default:
    just --list

sync:
    uv sync

test:
    uv run pytest

lint:
    uv run ruff check .

format:
    uv run ruff format .

typecheck:
    uv run pyright .

check: lint typecheck test

build:
    docker build -t {{IMAGE_NAME}} .

# App CLI wrapper:
cli *args:
    docker run --rm -it \
        {{DOCKER_DEV_ARGS}} \
        {{IMAGE_NAME}} \
        uv run staff-scheduling {{args}}

dev:
    docker run --rm -it \
        {{DOCKER_DEV_ARGS}} \
        {{IMAGE_NAME}} \
        uv run uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

docker-shell:
    docker run --rm -it \
        {{DOCKER_DEV_ARGS}} \
        {{IMAGE_NAME}} \
        bash

status:
    curl http://localhost:{{PORT}}/status
