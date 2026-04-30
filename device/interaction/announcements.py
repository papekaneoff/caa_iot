"""
announcements.py
Automatic announcements triggered by motion sensor or periodic checks.

Rules:
  - Weather announcement: max once per hour (ANNOUNCEMENT_COOLDOWN)
  - Critical alerts (humidity, air quality): always immediate, no cooldown
  - Morning reminders (7h-10h): rain, cold, heat warnings
  - Evening summary: once around 19h-21h
"""

import time
from datetime import datetime
from tts_handler import speak, speak_alert, speak_weather_announcement

# ─── State ────────────────────────────────────────────────────────────────────
_last_announcement_ts: float = 0.0
ANNOUNCEMENT_COOLDOWN: int   = 3600   # 1 hour in seconds

MORNING_START = 7
MORNING_END   = 10

# Alert thresholds (can be overridden via env vars)
HUMIDITY_ALERT_THRESHOLD    = 40.0   # % — alert if below this
AIR_QUALITY_ALERT_THRESHOLD = 1000.0 # ppm CO2 — alert if above this


# ─── Core ─────────────────────────────────────────────────────────────────────

def _can_announce() -> bool:
    return (time.time() - _last_announcement_ts) >= ANNOUNCEMENT_COOLDOWN


def _mark_announced() -> None:
    global _last_announcement_ts
    _last_announcement_ts = time.time()


# ─── Presence Trigger ─────────────────────────────────────────────────────────

def on_presence_detected(
    outdoor_temp: float,
    outdoor_condition: str,
    will_rain: bool,
    indoor_humidity: float,
    indoor_air_quality: float,
) -> None:
    """
    Called when motion sensor detects a person.
    Always checks for critical alerts.
    Weather announcement respects the 1-hour cooldown.
    """
    # ── Critical alerts: always fire immediately ──
    if indoor_humidity < HUMIDITY_ALERT_THRESHOLD:
        speak_alert("low_humidity", indoor_humidity)

    if indoor_air_quality > AIR_QUALITY_ALERT_THRESHOLD:
        speak_alert("bad_air", indoor_air_quality)

    # ── Weather announcement: respect cooldown ──
    if not _can_announce():
        print(f"[Announce] Cooldown active, skipping weather.")
        return

    speak_weather_announcement(outdoor_temp, outdoor_condition, will_rain)
    _morning_reminders(will_rain, outdoor_temp)
    _mark_announced()


# ─── Morning Reminders ────────────────────────────────────────────────────────

def _morning_reminders(will_rain: bool, outdoor_temp: float) -> None:
    """Contextual reminders spoken only during morning hours."""
    now = datetime.now()
    if not (MORNING_START <= now.hour < MORNING_END):
        return

    if will_rain:
        speak("Il va pleuvoir aujourd'hui. N'oubliez pas votre parapluie !")
        time.sleep(0.5)

    if outdoor_temp < 5:
        speak(f"Il fait très froid dehors : {outdoor_temp:.0f} degrés. Couvrez-vous bien !")
        time.sleep(0.5)
    elif outdoor_temp > 30:
        speak(f"Il fait très chaud : {outdoor_temp:.0f} degrés. Pensez à vous hydrater !")
        time.sleep(0.5)


# ─── Periodic Alert Check ─────────────────────────────────────────────────────

def check_and_alert_indoor(humidity: float, air_quality: float) -> None:
    """
    Call this from the main loop every few minutes.
    Fires spoken alerts if thresholds are exceeded.
    """
    if humidity < HUMIDITY_ALERT_THRESHOLD:
        speak_alert("low_humidity", humidity)

    if air_quality > AIR_QUALITY_ALERT_THRESHOLD:
        speak_alert("bad_air", air_quality)


# ─── Storm Warning ────────────────────────────────────────────────────────────

def announce_storm_warning() -> None:
    """Call when OpenWeatherMap detects severe/storm conditions."""
    speak_alert("storm", 0)


# ─── Evening Summary ──────────────────────────────────────────────────────────

_evening_summary_done_date = None


def announce_evening_summary(
    avg_indoor_temp: float,
    avg_humidity: float,
    outdoor_condition: str,
) -> None:
    """
    Announces a daily summary once in the evening (19h-21h).
    Tracks whether it's been done today to avoid repetition.
    """
    global _evening_summary_done_date
    now   = datetime.now()
    today = now.date()

    if not (19 <= now.hour < 21):
        return
    if _evening_summary_done_date == today:
        return

    _evening_summary_done_date = today
    speak(
        f"Résumé de la journée : température intérieure moyenne de {avg_indoor_temp:.1f} degrés, "
        f"humidité moyenne de {avg_humidity:.0f} pourcent. "
        f"Météo extérieure : {outdoor_condition}. Bonne soirée !"
    )


# ─── Test ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    on_presence_detected(
        outdoor_temp=6.0,
        outdoor_condition="nuageux avec pluie",
        will_rain=True,
        indoor_humidity=33.0,     # ← below threshold, triggers alert
        indoor_air_quality=850.0, # ← OK
    )
