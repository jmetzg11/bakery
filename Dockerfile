FROM python:3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/ src/

RUN uv run src/manage.py collectstatic --noinput

EXPOSE 8000

CMD uv run src/manage.py migrate --noinput && uv run gunicorn bakery.wsgi:application --bind 0.0.0.0:8000 --chdir src
