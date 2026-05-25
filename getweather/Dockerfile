FROM python:3.12-slim

# Prevent Python from writing pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY getweather.py .

# Cloud Run listens on 8080
EXPOSE 8080

# Start Functions Framework
CMD ["functions-framework", "--target=ingest", "--host=0.0.0.0", "--port=8080"]