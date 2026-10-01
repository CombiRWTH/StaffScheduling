_default:
    just --list

# Install host dependencies for IDE support and dependency maintenance.
install:
    cd api && uv sync --frozen
    cd webapp && pnpm install --frozen-lockfile
    cd webapp && pnpm exec playwright install chromium
    cd api && uv run --frozen pre-commit install

format:
    cd api && uv run --frozen ruff format .
    cd webapp && pnpm exec prettier --write . ../docs/source ../docs/mkdocs.yml ../README.md ../compose.yaml ../.github ../.pre-commit-config.yaml ../.vscode/extensions.json --config .prettierrc.json

format-check:
    cd api && uv run --frozen ruff format --check .
    cd webapp && pnpm exec prettier --check . ../docs/source ../docs/mkdocs.yml ../README.md ../compose.yaml ../.github ../.pre-commit-config.yaml ../.vscode/extensions.json --config .prettierrc.json

lint:
    cd api && uv run --frozen ruff check .
    cd webapp && pnpm run lint

quality:
    cd webapp && pnpm run quality

typecheck:
    cd api && uv run --frozen pyright .
    cd webapp && pnpm run typecheck

test *args:
    cd api && uv run --frozen python -m pytest {{args}}

test-browser:
    cd webapp && pnpm run test:browser

# Run every independent offline gate and retain a failure exit status.
check:
    @result=0; for task in format-check lint quality typecheck test test-browser build docs-check smoke; do "{{just_executable()}}" "$task" || result=1; done; exit "$result"

build:
    cd webapp && pnpm run build

run:
    mkdir -p data/found_solutions data/processed_solutions
    docker compose up --build --wait

stop:
    docker compose down

logs:
    docker compose logs --follow

docs:
    uv run --directory docs --frozen --python "$(cat api/.python-version)" mkdocs serve --dev-addr 127.0.0.1:8001

docs-check:
    uv run --directory docs --frozen --python "$(cat api/.python-version)" mkdocs build --strict

# Credential-free isolated startup, HTTP connectivity and persistent output checks.
smoke:
    sh scripts/smoke.sh

# Explicit read-only external integration diagnostics; services must already be running.
connectivity:
    docker compose exec -T api python -m app.timeoffice.database

# Only tests explicitly marked for the authorized external test database.
test-timeoffice:
    cd api && uv run --frozen python -m pytest -m timeoffice
