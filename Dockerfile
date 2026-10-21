# syntax=docker/dockerfile:1

# Image d'exécution du pipeline BEGES.
# Les dépendances sont résolues par uv et figées par uv.lock.
FROM python:3.12-slim-bookworm AS builder

COPY --from=ghcr.io/astral-sh/uv:0.10.8 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    HOME=/home/app \
    UV_NO_SYNC=1 \
    BEGES_DB_PATH=/app/data/warehouse/beges.duckdb \
    BEGES_CONFIG_DIR=/app/config \
    BEGES_SITE_DIR=/app/site

RUN apt-get update \
    && apt-get install -y --no-install-recommends make libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 app

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.10.8 /uv /usr/local/bin/uv
COPY --from=builder --chown=app:app /app/.venv /app/.venv

COPY --chown=app:app Makefile pyproject.toml uv.lock README.md ./
COPY --chown=app:app config ./config
COPY --chown=app:app dashboard ./dashboard
COPY --chown=app:app dbt ./dbt
COPY --chown=app:app donnees-sources-fictives ./donnees-sources-fictives
COPY --chown=app:app src ./src
COPY --chown=root:root docker/entrypoint.sh /usr/local/bin/entrypoint.sh

RUN mkdir -p /app/data/warehouse /app/site \
    && chown -R app:app /app/data /app/site \
    && chmod 755 /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["make", "all"]
