FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY getweather.py .
RUN pip install --no-cache-dir google-cloud-bigquery functions-framework flask 
EXPOSE 8080
CMD ["python", "getweather.py"]