FROM python:3.14.7-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.12.21 /uv /bin/uv
ENV UV_PROJECT_ENVIRONMENT=/opt/docs/.venv PATH="/opt/docs/.venv/bin:$PATH"
WORKDIR /project/docs
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --group docs --no-default-groups
CMD ["mkdocs", "serve", "--dev-addr", "0.0.0.0:8001"]
