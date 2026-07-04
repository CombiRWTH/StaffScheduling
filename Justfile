IMAGE_NAME := "staff-scheduling-api"
PORT := "8000"

# Shared Docker args for dev commands
DOCKER_DEV_ARGS := "--env-file .env -v $PWD/src:/app/src -v $PWD/tests:/app/tests -v $PWD/found_solutions:/app/found_solutions -v $PWD/processed_solutions:/app/processed_solutions" + " -p " + PORT + ":8000"

_default:
    just --list

sync:
    uv sync --all-extras

lint *args:
    uv run ruff check . {{args}}

format *args:
    uv run ruff format . {{args}}

typecheck *args:
    uv run pyright . {{args}}

test *args:
    uv run pytest {{args}}

check: lint typecheck test

build:
    docker build -t {{IMAGE_NAME}} .

run:
    docker run --rm -it \
        {{DOCKER_DEV_ARGS}} \
        {{IMAGE_NAME}} \
        uv run \
            fastapi dev \
            src/scheduling/api/app.py \
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
            src/scheduling/api/app.py \
            --host 0.0.0.0 --port 8000

docker-shell:
    docker run --rm -it \
        {{DOCKER_DEV_ARGS}} \
        {{IMAGE_NAME}} \
        bash

health:
    curl http://localhost:{{PORT}}/health

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
