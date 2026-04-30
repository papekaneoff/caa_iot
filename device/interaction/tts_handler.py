"""
tts_handler.py
Handles Text-to-Speech (TTS) using Google Cloud Text-to-Speech API.
Converts text to audio and plays it through the speaker.
"""

import os
import tempfile
import pygame
from google.cloud import texttospeech

# ─── Configuration ────────────────────────────────────────────────────────────
# Voice options: https://cloud.google.com/text-to-speech/docs/voices
TTS_LANGUAGE  = "fr-FR"
TTS_VOICE     = "fr-FR-Neural2-C"   # Natural French female voice
TTS_SPEED     = 1.05                # Slightly faster than default
TTS_PITCH     = 0.0                 # Default pitch

tts_client = texttospeech.TextToSpeechClient()

# Initialize pygame mixer once
pygame.mixer.init()


# ─── Core TTS Function ────────────────────────────────────────────────────────

def speak(text: str, language: str = TTS_LANGUAGE, voice_name: str = TTS_VOICE) -> None:
    """
    Converts `text` to speech using Google TTS and plays it.
    Blocks until audio playback is complete.

    Args:
        text:       The text to speak
        language:   BCP-47 language code (fr-FR or en-US)
        voice_name: Google voice name
    """
    if not text or not text.strip():
        print("[TTS] Empty text, skipping.")
        return

    preview = text[:60] + "..." if len(text) > 60 else text
    print(f"[TTS] 🔊 Speaking: '{preview}'")

    try:
        synthesis_input = texttospeech.SynthesisInput(text=text)

        voice = texttospeech.VoiceSelectionParams(
            language_code=language,
            name=voice_name,
        )

        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=TTS_SPEED,
            pitch=TTS_PITCH,
        )

        response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

        # Write to temp file and play
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp.write(response.audio_content)
            tmp_path = tmp.name

        _play_audio(tmp_path)

    except Exception as e:
        print(f"[TTS] Error: {e}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def _play_audio(path: str) -> None:
    """Loads and plays an MP3 file, blocking until done."""
    pygame.mixer.music.load(path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)


# ─── Convenience wrappers ─────────────────────────────────────────────────────

def speak_weather_announcement(outdoor_temp: float, condition: str, will_rain: bool) -> None:
    """Announces current outdoor weather conditions."""
    rain_warning = " N'oubliez pas votre parapluie !" if will_rain else ""
    message = (
        f"Bonjour ! La température extérieure est de {outdoor_temp:.0f} degrés. "
        f"Le temps est {condition}.{rain_warning}"
    )
    speak(message)


def speak_alert(alert_type: str, value: float) -> None:
    """Announces a sensor alert (low humidity, bad air quality, storm)."""
    messages = {
        "low_humidity": (
            f"Attention ! L'humidité intérieure est basse : {value:.0f} pourcent. "
            f"Pensez à aérer ou à utiliser un humidificateur."
        ),
        "bad_air": (
            f"Attention ! La qualité de l'air est mauvaise : {value:.0f} ppm de CO2. "
            f"Veuillez ouvrir une fenêtre."
        ),
        "storm": "Attention ! Une tempête est prévue. Restez à l'intérieur si possible.",
    }
    msg = messages.get(alert_type, f"Alerte capteur : {alert_type}, valeur {value}.")
    speak(msg)


# ─── Test ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    speak("Bonjour ! La température extérieure est de 12 degrés. Il fait nuageux aujourd'hui.")
