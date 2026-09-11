FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv \
    && uv sync --frozen --no-dev

COPY apps ./apps
COPY alembic.ini ./
COPY alembic ./alembic

COPY tests/fixtures ./tests/fixtures
COPY docker/seed ./docker/seed

EXPOSE 10002

CMD ["uv", "run", "uvicorn", "apps.evidence_aggregator.main:app", "--host", "0.0.0.0", "--port", "10002"]