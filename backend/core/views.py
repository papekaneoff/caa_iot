from django.shortcuts import render

from google.cloud import bigquery
from django.http import JsonResponse

client = bigquery.Client()

def weather_data(request):
    query = """
        SELECT
            device_id,
            temperature,
            humidity,
            pressure,
            timestamp
        FROM `caaproject-490112.weather.weather-data`
        ORDER BY timestamp DESC
        LIMIT 200
    """

    results = client.query(query).result()

    data = []
    for row in results:
        data.append({
            "device_id": row.device_id,
            "temperature": row.temperature,
            "humidity": row.humidity,
            "pressure": row.pressure,
            "timestamp": row.timestamp.isoformat()
        })

    return JsonResponse(data, safe=False)
