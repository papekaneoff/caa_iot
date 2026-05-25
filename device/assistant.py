from m5stack import *
from m5ui import *
from uiflow import *
import MicrophonePDM as MIC
import urequests
import time
import network

setScreenColor(0x111111)

BASE_URL = "https://vs-947281260717.europe-west1.run.app"
WIFI_SSID = "yallo_7016692"
WIFI_PASS = "wvvjcgxSvcGzcgm8"

def show_message(title, msg, color=0xffffff):
    lcd.clear()
    lcd.font(lcd.FONT_DejaVu24)
    lcd.print(title, 10, 20, color)
    lcd.font(lcd.FONT_DejaVu18)
    lcd.print(str(msg)[:180], 10, 70, 0xffffff)

def connect_wifi():
    show_message("Wifi", "Connecting...", 0xffaa00)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASS)
        timeout = 0
        while not wlan.isconnected():
            time.sleep(0.5)
            timeout += 1
            if timeout > 20:
                show_message("Wifi", "FAILED", 0xff0000)
                return False
    show_message("Wifi", "Connected!", 0x00ff00)
    time.sleep(1)
    return True

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

def buttonB_wasPressed():
    show_message("Recording", "Ask your question...", 0xffaa00)
    try:
        MIC.begin(
            pin_ws=0,
            pin_data=34,
            sample_rate_hz=16000,
            buffer_length_ms=1000,
            block_length_ms=100
        )
        f = open("/flash/question.wav", "wb")
        MIC.recordStart(f, 3000)
        time.sleep(4)
        MIC.recordStop()
        time.sleep(0.5)
        f.close()
        MIC.deinit(0)
        time.sleep(1)
    except Exception as e:
        show_message("Record Error", str(e), 0xff0000)
        try:
            f.close()
        except:
            pass
        return

    show_message("Sending", "Processing...", 0x00aaff)

    try:
        f = open("/flash/question.wav", "rb")
        audio_data = f.read()
        f.close()

        r = urequests.post(
            BASE_URL + "/stt",
            data=audio_data,
            headers={"Content-Type": "audio/wav"}
        )

        data = r.json()
        r.close()

        transcript = data.get("transcript", "")
        answer = data.get("answer", "")

        if transcript:
            show_message("You said", transcript, 0x00ff00)
        else:
            show_message("Not understood", answer, 0xff0000)

        time.sleep(2)

        if answer:
            speak(answer)

        show_message("Done", "Press B again!", 0x00ff00)

    except Exception as e:
        show_message("HTTP Error", str(e), 0xff0000)

connect_wifi()

btnB.wasPressed(buttonB_wasPressed)
show_message("M5 Assistant", "Press B to ask", 0xffffff)

while True:
    time.sleep(0.1)