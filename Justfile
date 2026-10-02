_default:
    just --list

# Install host dependencies for IDE support and dependency maintenance.
install:
    cd api && uv sync --frozen
    cd webapp && pnpm install --frozen-lockfile
    cd webapp && pnpm exec playwright install chromium
    cd api && uv run --frozen pre-commit install

# Warn about tools that are missing or differ from the project pins; fail if the password file is missing.
precheck:
    #!/usr/bin/env bash
    check_version() {
        local found
        [[ -n $2 ]] || { echo "Warning: could not read the pinned $1 version." >&2; return; }
        found=$("$1" --version 2>/dev/null) || { echo "Warning: $1 not found; native development needs $1 $2." >&2; return; }
        [[ $found =~ [0-9]+(\.[0-9]+)+ && ${BASH_REMATCH[0]} == "$2" ]] || echo "Warning: $found found; this project uses $2." >&2
    }
    docker compose version >/dev/null 2>&1 || echo "Warning: Docker with Compose not found; just run needs it." >&2
    python=$(<api/.python-version)
    check_version "{{just_executable()}}" "$(sed -n '/just-version:/{s/.*"\(.*\)"/\1/p;q;}' .github/workflows/ci.yml)"
    check_version uv "$(sed -n 's/^required-version = "==\(.*\)"/\1/p' api/pyproject.toml)"
    check_version "python${python%.*}" "$python"
    check_version node "$(sed -n 's/.*"node": "\(.*\)".*/\1/p' webapp/package.json)"
    check_version pnpm "$(sed -n 's/.*"packageManager": "pnpm@\(.*\)".*/\1/p' webapp/package.json)"
    file=${DB_PASSWORD_FILE:-.secrets/db_password}
    [[ -f $file ]] || { echo "Missing $file; create it as described in the quickstart." >&2; exit 1; }

format:
    cd api && uv run --frozen ruff format .
    cd webapp && pnpm exec prettier --write . ../docs/source ../docs/adr ../docs/mkdocs.yml ../README.md ../compose.yaml ../.github ../.pre-commit-config.yaml --config .prettierrc.json

format-check:
    cd api && uv run --frozen ruff format --check .
    cd webapp && pnpm exec prettier --check . ../docs/source ../docs/adr ../docs/mkdocs.yml ../README.md ../compose.yaml ../.github ../.pre-commit-config.yaml --config .prettierrc.json

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
    @result=0; for task in format-check lint quality typecheck test test-browser build docs-check; do "{{just_executable()}}" "$task" || result=1; done; exit "$result"

build:
    cd webapp && pnpm run build

run: precheck
    docker compose up --build --wait

stop:
    docker compose down

logs:
    docker compose logs --follow

docs:
    uv run --directory docs --frozen --python "$(cat api/.python-version)" mkdocs serve --dev-addr 127.0.0.1:8001

docs-check:
    uv run --directory docs --frozen --python "$(cat api/.python-version)" mkdocs build --strict

# Explicit read-only external integration diagnostics; services must already be running.
connectivity:
    docker compose exec -T api python -m app.timeoffice.database

# Only tests explicitly marked for the authorized external test database, in the API image with its ODBC driver.
# plaene/ is writable for the example generation, which runs only with PLAENE_GENERATION=write.
test-timeoffice *args:
    docker compose run --build --rm --no-deps -v ./api/tests:/project/api/tests:ro -v ./plaene:/project/plaene -e TIMEOFFICE_PREPARATION -e PLAENE_GENERATION api python -m pytest -p no:cacheprovider -m timeoffice {{args}}
