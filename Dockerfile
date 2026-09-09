FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY apps ./apps
COPY contracts ./contracts
COPY data ./data
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

CMD ["uv", "run", "python", "-m", "apps.controls_importer.main"]
