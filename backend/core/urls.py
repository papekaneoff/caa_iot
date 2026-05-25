from django.urls import path
from .views import sensor_data, openweather, health

urlpatterns = [
    path("sensor/", sensor_data),
    path("openweather/", openweather),
    path("health/", health),
]