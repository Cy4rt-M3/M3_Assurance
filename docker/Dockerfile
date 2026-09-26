FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

COPY apps ./apps
COPY alembic ./alembic
COPY alembic.ini ./

ENV PYTHONPATH=/app

CMD ["uv", "run", "uvicorn", "apps.framework_registry.main:app", "--host", "0.0.0.0", "--port", "10006"]