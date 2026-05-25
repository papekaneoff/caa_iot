from flask import Flask, request, jsonify, send_file
from google.cloud import bigquery
from google.cloud import speech
from google.cloud import texttospeech
from dotenv import load_dotenv

import os
import requests
import tempfile
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)

PROJECT_ID = "esoteric-storm-496611-p0"
OPENWEATHER_API_KEY = os.environ["OPENWEATHER_API_KEY"]

client = bigquery.Client(project=PROJECT_ID)
speech_client = speech.SpeechClient()
tts_client = texttospeech.TextToSpeechClient()

TABLE = "`esoteric-storm-496611-p0.weather.weather-data`"

last_announcement = None


# ---------------------------------------------------
# WEATHER
# ---------------------------------------------------

def weather_sentence(city="Lausanne"):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    data = requests.get(url, params=params).json()
    temp = data["main"]["temp"]
    desc = data["weather"][0]["description"]
    main = data["weather"][0]["main"].lower()

    sentence = f"The weather in {city} is {desc} with {temp:.1f} degrees."

    if "rain" in main:
        sentence += " Take an umbrella today."
    else:
        sentence += " No umbrella needed today, have a nice day!"

    if temp < 5:
        sentence += " It is cold outside. Wear a jacket."

    return sentence

# ---------------------------------------------------
# SMART QUESTIONS
# ---------------------------------------------------

def smart_answer(question):

    q = question.lower()

    # CURRENT TEMP
    if "temperature" in q and ("now" in q or "current" in q):

        query = f"""
        SELECT temperature
        FROM {TABLE}
        ORDER BY timestamp DESC
        LIMIT 1
        """

        rows = list(client.query(query).result())

        if rows:
            return f"The current indoor temperature is {rows[0].temperature:.1f} degrees."

        return "No temperature data found."

    # YESTERDAY TEMP
    if "yesterday" in q and "temperature" in q:

        query = f"""
        SELECT AVG(temperature) AS avg_temp
        FROM {TABLE}
        WHERE DATE(timestamp) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
        """

        rows = list(client.query(query).result())

        if rows and rows[0].avg_temp:
            return f"Yesterday the average indoor temperature was {rows[0].avg_temp:.1f} degrees."

        return "No data found for yesterday."

    # HUMIDITY
    if "humidity" in q and "50" in q:

        query = f"""
        SELECT MAX(humidity) AS max_humidity
        FROM {TABLE}
        WHERE DATE(timestamp) = DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
        """

        rows = list(client.query(query).result())

        if rows and rows[0].max_humidity:

            if rows[0].max_humidity > 50:
                return "Yes, humidity exceeded 50 percent two days ago."

            return "No, humidity did not exceed 50 percent two days ago."

    # AIR QUALITY
    if "air quality" in q:

        query = f"""
        SELECT tvoc, eco2
        FROM {TABLE}
        ORDER BY timestamp DESC
        LIMIT 1
        """

        rows = list(client.query(query).result())

        if rows:

            eco2 = rows[0].eco2

            if eco2 > 1000:
                return f"Indoor air quality is bad. ECO2 is {eco2}."

            return f"Indoor air quality is acceptable. ECO2 is {eco2}."

    # WEATHER
    if "weather" in q or "rain" in q:
        return weather_sentence()

    return "I can answer questions about temperature, humidity, air quality and weather."


# ---------------------------------------------------
# HOME
# ---------------------------------------------------

@app.route("/")
def home():

    return jsonify({
        "status": "running"
    })


# ---------------------------------------------------
# WEATHER
# ---------------------------------------------------

@app.route("/weather")
def weather():
    sentence = weather_sentence()
    return jsonify({
        "message": sentence
    })


# ---------------------------------------------------
# ASK
# ---------------------------------------------------

@app.route("/ask", methods=["POST"])
def ask():

    data = request.get_json()

    question = data.get("question", "")

    answer = smart_answer(question)

    return jsonify({
        "question": question,
        "answer": answer
    })


# ---------------------------------------------------
# TEXT TO SPEECH
# ---------------------------------------------------

@app.route("/tts", methods=["POST"])
def tts():

    import wave
    import io
    import struct

    data = request.get_json()

    text = data.get("text", "Hello")

    synthesis_input = texttospeech.SynthesisInput(
        text=text
    )

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Neural2-F"
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        speaking_rate=0.9,
        volume_gain_db=16.0
    )

    response = tts_client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    input_wav = io.BytesIO(response.audio_content)

    output_wav = io.BytesIO()

    BOOST = 20.0

    with wave.open(input_wav, "rb") as wav_in:

        params = wav_in.getparams()

        frames = wav_in.readframes(
            wav_in.getnframes()
        )

        samples = struct.unpack(
            "<" + "h" * (len(frames) // 2),
            frames
        )

        boosted = []

        for s in samples:

            v = int(s * BOOST)

            if v > 32767:
                v = 32767

            if v < -32768:
                v = -32768

            boosted.append(v)

        boosted_frames = struct.pack(
            "<" + "h" * len(boosted),
            *boosted
        )

        with wave.open(output_wav, "wb") as wav_out:

            wav_out.setparams(params)

            wav_out.writeframes(
                boosted_frames
            )

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".wav"
    )

    temp_file.write(
        output_wav.getvalue()
    )

    temp_file.close()

    return send_file(
        temp_file.name,
        mimetype="audio/wav"
    )


# ---------------------------------------------------
# SPEECH TO TEXT
# ---------------------------------------------------

@app.route("/stt", methods=["POST"])
def stt():
    if "audio" in request.files:
        content = request.files["audio"].read()
    elif request.data:
        content = request.data
    else:
        return jsonify({"error": "No audio data"}), 400

    try:
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )
        response = speech_client.recognize(config=config, audio=audio)

        if not response.results:
            return jsonify({
                "transcript": "",
                "answer": "I could not understand the audio."
            })

        transcript = response.results[0].alternatives[0].transcript
        answer = smart_answer(transcript)

        return jsonify({
            "transcript": transcript,
            "answer": answer
        })

    except Exception as e:
        return jsonify({
            "transcript": "",
            "answer": "Error processing audio.",
            "error": str(e)
        }), 200

# ---------------------------------------------------
# PRESENCE
# ---------------------------------------------------

@app.route("/presence", methods=["POST"])
def presence():

    global last_announcement

    now = datetime.now()

    if last_announcement:

        if now - last_announcement < timedelta(hours=1):

            return jsonify({
                "announce": False,
                "message": "Already announced recently"
            })

    last_announcement = now

    sentence = weather_sentence()

    return jsonify({
        "announce": True,
        "message": sentence
    })


# ---------------------------------------------------
# MORNING
# ---------------------------------------------------

@app.route("/morning")
def morning():

    sentence = weather_sentence()

    return jsonify({
        "message": sentence
    })


# ---------------------------------------------------

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

import functions_framework

@functions_framework.http
def main(request):
    with app.request_context(request.environ):
        return app.full_dispatch_request()