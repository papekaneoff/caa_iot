"""
main_interaction.py
Orchestrates all voice interaction for the M5Stack device.
Runs in a background thread alongside the display loop.

Integration example (in your main device script):
─────────────────────────────────────────────────
    from interaction.main_interaction import InteractionController

    controller = InteractionController(
        get_sensor_data_fn=lambda: sensor_module.get_latest(),
        get_weather_fn=lambda: weather_module.get_current(),
    )
    controller.start()

    # In motion sensor callback:
    controller.trigger_motion()

    # When user presses button A:
    controller.trigger_qa()
─────────────────────────────────────────────────
"""

import threading
import time
from datetime import datetime

from speech_handler import listen
from tts_handler import speak
from interaction_manager import handle_question
from announcements import (
    on_presence_detected,
    check_and_alert_indoor,
    announce_evening_summary,
)

LISTEN_TIMEOUT    = 6    # seconds to record user question
ALERT_CHECK_EVERY = 300  # seconds between periodic indoor checks (5 min)


class InteractionController:
    """
    Background controller for all voice interactions and announcements.
    Thread-safe — trigger_motion() and trigger_qa() can be called from any thread.
    """

    def __init__(self, get_sensor_data_fn, get_weather_fn):
        """
        Args:
            get_sensor_data_fn: () → dict with keys:
                temperature_indoor (float), humidity (float), air_quality (float)
            get_weather_fn:     () → dict with keys:
                temperature (float), condition (str), will_rain (bool)
        """
        self._get_sensor  = get_sensor_data_fn
        self._get_weather = get_weather_fn
        self._running     = False
        self._qa_busy     = False
        self._thread      = None
        self._evening_done_date = None

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background loop."""
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True, name="InteractionLoop")
        self._thread.start()
        print("[Interaction] ✅ Controller started.")

    def stop(self) -> None:
        """Stop the background loop."""
        self._running = False
        print("[Interaction] Controller stopped.")

    def trigger_motion(self) -> None:
        """
        Call this from the PIR motion sensor interrupt.
        Fires presence announcement in a separate thread (non-blocking).
        """
        threading.Thread(target=self._handle_presence, daemon=True).start()

    def trigger_qa(self) -> None:
        """
        Call this when the user presses a button to ask a voice question.
        Ignored if a Q&A session is already in progress.
        """
        if not self._qa_busy:
            threading.Thread(target=self._handle_qa, daemon=True).start()

    # ── Background Loop ───────────────────────────────────────────────────────

    def _loop(self) -> None:
        """Periodic tasks: indoor alert checks + evening summary."""
        while self._running:
            try:
                sensor  = self._get_sensor()
                weather = self._get_weather()

                # Periodic indoor air quality / humidity check
                check_and_alert_indoor(
                    humidity=sensor.get("humidity", 50),
                    air_quality=sensor.get("air_quality", 400),
                )

                # Evening summary (once per evening)
                announce_evening_summary(
                    avg_indoor_temp=sensor.get("temperature_indoor", 20),
                    avg_humidity=sensor.get("humidity", 50),
                    outdoor_condition=weather.get("condition", "inconnu"),
                )

            except Exception as e:
                print(f"[Interaction] Loop error: {e}")

            time.sleep(ALERT_CHECK_EVERY)

    # ── Handlers ──────────────────────────────────────────────────────────────

    def _handle_presence(self) -> None:
        """Triggered by motion sensor: announces weather + critical alerts."""
        try:
            sensor  = self._get_sensor()
            weather = self._get_weather()
            on_presence_detected(
                outdoor_temp=weather.get("temperature", 0),
                outdoor_condition=weather.get("condition", "inconnu"),
                will_rain=weather.get("will_rain", False),
                indoor_humidity=sensor.get("humidity", 50),
                indoor_air_quality=sensor.get("air_quality", 400),
            )
        except Exception as e:
            print(f"[Interaction] Presence error: {e}")

    def _handle_qa(self) -> None:
        """Handles a full voice Q&A session: prompt → listen → answer → speak."""
        self._qa_busy = True
        try:
            speak("Oui ? Quelle est votre question ?")
            user_text = listen(duration=LISTEN_TIMEOUT, language="fr-FR")

            if not user_text.strip():
                speak("Je n'ai pas entendu de question. Appuyez à nouveau sur le bouton pour réessayer.")
                return

            answer = handle_question(user_text)
            speak(answer)

        except Exception as e:
            print(f"[Interaction] Q&A error: {e}")
            speak("Désolé, une erreur s'est produite.")
        finally:
            self._qa_busy = False
