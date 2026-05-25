FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY vs.py .
RUN pip install --no-cache-dir flask google-cloud-texttospeech google-cloud-speech google-cloud-bigquery requests python-dotenv functions-framework
EXPOSE 8080
CMD ["python", "vs.py"]