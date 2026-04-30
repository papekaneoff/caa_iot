"""
speech_handler.py
Handles Speech-to-Text (STT) using Google Cloud Speech API.
Records audio from the microphone and returns transcribed text.
"""

import os
import wave
import tempfile
import pyaudio
from google.cloud import speech

# ─── Configuration ────────────────────────────────────────────────────────────
# Make sure GOOGLE_APPLICATION_CREDENTIALS is set in your .env
SAMPLE_RATE    = 16000
CHANNELS       = 1
CHUNK          = 1024
FORMAT         = pyaudio.paInt16
RECORD_SECONDS = 5

speech_client = speech.SpeechClient()


# ─── Audio Recording ──────────────────────────────────────────────────────────

def record_audio(duration: int = RECORD_SECONDS) -> bytes:
    """
    Records audio from the microphone for `duration` seconds.
    Returns raw audio bytes (LINEAR16).
    """
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK,
    )

    print(f"[STT] 🎙️ Recording for {duration} seconds...")
    frames = []
    for _ in range(0, int(SAMPLE_RATE / CHUNK * duration)):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()
    print("[STT] ✅ Recording complete.")

    return b"".join(frames)


# ─── Transcription ────────────────────────────────────────────────────────────

def transcribe_audio(audio_bytes: bytes, language: str = "fr-FR") -> str:
    """
    Sends audio bytes to Google Cloud Speech-to-Text.
    Returns transcribed text, or empty string on failure.

    Args:
        audio_bytes: Raw LINEAR16 audio bytes
        language:    BCP-47 language code. 'fr-FR' or 'en-US'
    """
    try:
        audio    = speech.RecognitionAudio(content=audio_bytes)
        config   = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code=language,
            # Also understand a mix of French/English
            alternative_language_codes=["en-US"] if language == "fr-FR" else ["fr-FR"],
        )

        response = speech_client.recognize(config=config, audio=audio)

        if not response.results:
            print("[STT] No speech detected.")
            return ""

        transcript = response.results[0].alternatives[0].transcript.strip()
        confidence = response.results[0].alternatives[0].confidence
        print(f"[STT] Transcribed (conf={confidence:.0%}): '{transcript}'")
        return transcript

    except Exception as e:
        print(f"[STT] Error: {e}")
        return ""


# ─── Main convenience function ────────────────────────────────────────────────

def listen(duration: int = RECORD_SECONDS, language: str = "fr-FR") -> str:
    """
    Records audio and returns transcribed text in one call.
    Usage: text = listen()
    """
    audio_bytes = record_audio(duration)
    return transcribe_audio(audio_bytes, language)


# ─── Test ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = listen(duration=5)
    print(f"You said: {result}")
