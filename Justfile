_default:
    just --list

# Optional native development tools; normal startup needs Docker and just only.
install:
    cd api && uv sync --frozen
    cd webapp && pnpm install --frozen-lockfile
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

check: format-check lint quality typecheck test docs-check

run:
    docker compose up --build --wait

stop:
    docker compose down

logs:
    docker compose logs --follow

# Native development is optional and uses the same service locks.
api-dev:
    cd api && uv run --frozen fastapi dev app/main.py --host 127.0.0.1 --port 8000

webapp-dev:
    cd webapp && pnpm run dev

docs:
    uv run --directory docs --frozen --python "$(cat api/.python-version)" mkdocs serve --dev-addr 127.0.0.1:8001

docs-check:
    uv run --directory docs --frozen --python "$(cat api/.python-version)" mkdocs build --strict
