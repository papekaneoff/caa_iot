from django.shortcuts import render

from google.cloud import bigquery
from django.http import JsonResponse

import os
import requests
import logging

logger = logging.getLogger(__name__)

client = bigquery.Client()

def sensor_data(request):
    query = """
        SELECT
            device_id,
            temperature,
            humidity,
            pressure,
            timestamp,
            tvoc,
            eco2
        FROM `caaproject-490112.weather.weather-data`
        ORDER BY timestamp ASC
    """

    results = client.query(query).result()

    data = []
    for row in results:
        data.append({
            "device_id": row.device_id,
            "temperature": row.temperature,
            "humidity": row.humidity,
            "pressure": row.pressure,
            "timestamp": row.timestamp.isoformat(),
            "tvoc": row.tvoc,
            "eco2": row.eco2,
        })

    return JsonResponse(data, safe=False)


def openweather(request):
    def c_to_f(c):
        return round((c * 9/5) + 32, 1)

    def ms_to_mph(ms):
        return round(ms * 2.23694, 1)

    def meters_to_miles(m):
        return round(m * 0.000621371, 1)

    # ✅ Get city from query params, fallback to Lausanne
    city = (request.GET.get("city", "").strip() or "Lausanne")

    logger.info(f"OpenWeather request for city: {city}")

    base_url = "https://api.openweathermap.org/data/2.5"

    params = {
        "q": city,
        "appid": os.environ["OPENWEATHER_API_KEY"],
        "units": "metric"
    }

    current_res = requests.get(f"{base_url}/weather", params=params).json()
    forecast_res = requests.get(f"{base_url}/forecast", params=params).json()

    # ✅ handle API errors
    if "main" not in current_res:
        return JsonResponse({
            "error": "OpenWeather current failed",
            "details": current_res
        }, status=500)

    if "list" not in forecast_res:
        return JsonResponse({
            "error": "OpenWeather forecast failed",
            "details": forecast_res
        }, status=500)

    current = {
        "city": current_res.get("name"),
        "temp_c": current_res["main"]["temp"],
        "temp_f": c_to_f(current_res["main"]["temp"]),
        "feels_like_c": current_res["main"]["feels_like"],
        "feels_like_f": c_to_f(current_res["main"]["feels_like"]),
        "temp_min_c": current_res["main"]["temp_min"],
        "temp_min_f": c_to_f(current_res["main"]["temp_min"]),
        "temp_max_c": current_res["main"]["temp_max"],
        "temp_max_f": c_to_f(current_res["main"]["temp_max"]),
        "humidity": current_res["main"]["humidity"],
        "pressure": current_res["main"]["pressure"],
        "description": current_res["weather"][0]["description"],
        "icon": current_res["weather"][0]["icon"],
        "wind_speed_ms": current_res["wind"]["speed"],
        "wind_speed_mph": ms_to_mph(current_res["wind"]["speed"]),
        "clouds": current_res["clouds"]["all"],
        "sunrise": current_res["sys"]["sunrise"],
        "sunset": current_res["sys"]["sunset"],
        "visibility_m": current_res.get("visibility"),
        "visibility_miles": meters_to_miles(current_res.get("visibility", 0)),
    }

    forecast = [
        {
            "time": item["dt_txt"],
            "temp_c": item["main"]["temp"],
            "temp_f": c_to_f(item["main"]["temp"]),
            "humidity": item["main"]["humidity"],
            "pop": item.get("pop", 0),
        }
        for item in forecast_res["list"]
    ]

    return JsonResponse({
        "current": current,
        "forecast": forecast
    })