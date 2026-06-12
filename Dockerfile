FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

# System dependencies:
# - curl/gnupg/ca-certificates: install Microsoft repo
# - unixodbc/unixodbc-dev: required by pyodbc
# - msodbcsql18: Microsoft ODBC Driver 18 for SQL Server
# - build-essential: useful if a dependency needs compilation
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    bash \
    curl \
    ca-certificates \
    gnupg \
    unixodbc \
    unixodbc-dev \
    build-essential \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" \
    > /etc/apt/sources.list.d/microsoft-prod.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# Install uv from the official uv image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN mkdir -p cases found_solutions

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

EXPOSE 8000

# Bind to 0.0.0.0 so the API is reachable from outside the container.
CMD ["uv", "run", "--no-sync", "uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
