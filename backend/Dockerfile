FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -Ls https://astral.sh/uv/install.sh | sh

# IMPORTANT: make uv available
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY . .

# Install dependencies (NO uv venv needed)
RUN uv sync

EXPOSE 8000

CMD ["sh", "-c", "uv run gunicorn config.wsgi:application --bind 0.0.0.0:$PORT"]