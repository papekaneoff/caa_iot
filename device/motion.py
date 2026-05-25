from m5stack import *
from m5ui import *
from machine import Pin
import urequests
import time

setScreenColor(0x111111)

BASE_URL = "https://vs-947281260717.europe-west1.run.app"

PIR_PIN = 32
pir = Pin(PIR_PIN, Pin.IN)

last_motion_announcement = -99999
COOLDOWN_SECONDS = 3600

def show_message(title, msg, color=0xffffff):
    lcd.clear()
    lcd.font(lcd.FONT_DejaVu24)
    lcd.print(title, 10, 20, color)
    lcd.font(lcd.FONT_DejaVu18)
    lcd.print(msg[:180], 10, 70, 0xffffff)

def ask_backend(question):
    r = urequests.post(
        BASE_URL + "/ask",
        json={"question": question}
    )
    data = r.json()
    r.close()
    return data["answer"]

def get_weather():
    r = urequests.get(BASE_URL + "/weather")
    data = r.json()
    r.close()
    return data.get("message", "")

def speak(text):
    show_message("Speaking", text)
    r = urequests.post(
        BASE_URL + "/tts",
        json={"text": text}
    )
    audio_data = r.content
    r.close()
    f = open("/flash/speech.wav", "wb")
    f.write(audio_data)
    f.close()
    speaker.playWAV(
        "/flash/speech.wav",
        rate=16000,
        volume=6
    )

def motion_detected():
    global last_motion_announcement
    now = time.time()
    if now - last_motion_announcement > COOLDOWN_SECONDS:
        last_motion_announcement = now
        try:
            # Heure actuelle UTC+2
            hour = time.localtime()[3] + 2

            # Température intérieure
            temp = ask_backend("What is the current temperature?")

            # Météo extérieure
            weather = get_weather()

            # Message de base
            msg = temp + " " + weather

            # Matin — umbrella
            if 6 <= hour <= 12:
                if "rain" in weather.lower() or "umbrella" in weather.lower():
                    msg = "Good morning! " + temp + " Don't forget your umbrella today!"
                else:
                    msg = "Good morning! " + temp + " No umbrella needed, have a nice day!"

            # Après-midi
            elif 12 < hour <= 18:
                msg = "Good afternoon! " + temp + " " + weather

            # Soir
            elif hour > 18:
                msg = "Good evening! " + temp + " " + weather

            show_message("Motion", msg, 0x00ff00)
            speak(msg)

        except Exception as e:
            show_message("Error", str(e), 0xff0000)
    else:
        show_message("Motion", "Already announced recently", 0xffaa00)

show_message("M5 Assistant", "Motion sensor active", 0xffffff)

while True:
    if pir.value() == 1:
        motion_detected()
        while pir.value() == 1:
            time.sleep(0.1)
        time.sleep(2)
    time.sleep(0.1)