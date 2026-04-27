from django.urls import path
from .views import weather_data

urlpatterns = [
    path("weather/", weather_data),
]