from m5stack import *
from m5stack_ui import *
from uiflow import *
import urequests
from libs.json_py import *
import unit
import gc
import time
import ntptime
import wifiCfg
from m5ui import *
from machine import Pin

BASE_URL = "https://vs-947281260717.europe-west1.run.app"

PIR_PIN = 32
pir = Pin(PIR_PIN, Pin.IN)

last_motion_announcement = -99999
COOLDOWN_SECONDS = 3600

WIFI_PROFILES = [
    ("iot-unil", "4u6uch4hpY9pJ2f9"),
    ("LAPTOP-DFQ5ND9M 3421", "T73949l%"),
    ("yallo_7016692", "wvvjcgxSvcGzcgm8")
]

current_wifi = 1
current_ssid = "NONE"
should_connect = False

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

            speak(msg)

        except Exception as e:
            pass
    else:
        pass

def connect_wifi(index):

    global current_wifi, current_ssid

    try:

        ssid, pwd = WIFI_PROFILES[index]

        status_label.set_text("CON " + ssid)
        status_label.set_text_color(0xffcc00)

        # disconnect first
        try:
            wifiCfg.wlan_sta.disconnect()
        except:
            pass

        wait(0.2)

        # start connection
        wifiCfg.doConnect(ssid, pwd)

        # shorter timeout
        timeout = 1.5
        t0 = time.time()

        while True:

            if wifiCfg.wlan_sta.isconnected():

                current_wifi = index
                current_ssid = ssid

                status_label.set_text("::" + ssid)
                status_label.set_text_color(0x00ff99)

                return True

            # fail fast
            if time.time() - t0 > timeout:

                try:
                    wifiCfg.wlan_sta.disconnect()
                except:
                    pass

                status_label.set_text("<!>" + ssid)
                status_label.set_text_color(0xff3355)

                return False

            wait(0.05)

    except:

        status_label.set_text("FAIL")
        status_label.set_text_color(0xff3355)

        return False

def buttonA_wasPressed():
    global current_wifi
    current_wifi = (current_wifi - 1) % len(WIFI_PROFILES)
    status_label.set_text(">" + WIFI_PROFILES[current_wifi][0])
    status_label.set_text_color(0x00ff99)
    global should_connect
    should_connect = True
      
btnA.wasPressed(buttonA_wasPressed)


def buttonB_wasPressed():
    status_label.set_text(">" + WIFI_PROFILES[current_wifi][0])
    status_label.set_text_color(0x00ff99)
    global should_connect
    should_connect = True

btnB.wasPressed(buttonB_wasPressed)


def buttonC_wasPressed():
    global current_wifi
    current_wifi = (current_wifi + 1) % len(WIFI_PROFILES)
    status_label.set_text(">" + WIFI_PROFILES[current_wifi][0])
    status_label.set_text_color(0x00ff99)
    global should_connect
    should_connect = True

btnC.wasPressed(buttonC_wasPressed)

# =========================================================
# CYBERPUNK WEATHER + AIR QUALITY TERMINAL
# =========================================================

# =========================================================
# CONFIG
# =========================================================

DISPLAY_REFRESH = 0.2
WEATHER_REFRESH = 600   # 10 min

SEND_INTERVAL = 300     # upload every 5 min

last_weather_update = 0
last_send = 0

# =========================================================
# SENSOR DATA UPLOAD
# =========================================================

def upload_sensor_data():

    try:

        req = urequests.request(
            method='POST',
            url='https://getweather-947281260717.europe-west1.run.app',
            json=py_2_json({
                'device_id': '0',

                'temperature': env3_0.temperature,
                'humidity': env3_0.humidity,
                'pressure': env3_0.pressure,

                'timestamp': rtc.datetime(),

                'iaq_baseline': tvoc_0.get_iaq_baseline(),

                'tvoc': tvoc_0.TVOC,
                'eco2': tvoc_0.eCO2,

                'h2': tvoc_0.H2,
                'ethanol': tvoc_0.Ethanol,
            }),
            headers={
                'Content-Type': 'application/json'
            }
        )

        req.close()

        gc.collect()

        status_label.set_text('SYNC')
        status_label.set_text_color(0x00ff99)

        return True

    except:

        status_label.set_text('ERR ' + current_ssid)
        status_label.set_text_color(0xff3355)

        return False

# -----------------------
# Screen setup
# -----------------------
screen = M5Screen()
screen.clean_screen()
screen.set_screen_bg_color(0x050816)

# =========================================================
# CYBERPUNK FRAME
# =========================================================

# Outer frame
M5Line(x1=4, y1=4, x2=316, y2=4, color=0xff00ff, width=2)
M5Line(x1=4, y1=236, x2=316, y2=236, color=0xff00ff, width=2)

M5Line(x1=4, y1=4, x2=4, y2=236, color=0x00e5ff, width=2)
M5Line(x1=316, y1=4, x2=316, y2=236, color=0x00e5ff, width=2)

# Header glow
M5Line(x1=12, y1=36, x2=308, y2=36, color=0x00e5ff, width=2)
M5Line(x1=12, y1=37, x2=308, y2=37, color=0xff00ff, width=1)

# =========================================================
# HEADER
# =========================================================

time_label = M5Label(
    '--:--:--',
    x=16,
    y=10,
    color=0x00ffff,
    font=FONT_MONT_14
)

title = M5Label(
    'NEON WEATHER GRID',
    x=162,
    y=25,
    color=0xff00ff,
    font=FONT_MONT_10
)

status_label = M5Label(
    'WIFI',
    x=200,
    y=10,
    color=0x00e5ff,
    font=FONT_MONT_14
)

# =========================================================
# CURRENT WEATHER PANEL FRAME
# =========================================================

# outer frame
M5Line(x1=12, y1=48, x2=308, y2=48, color=0x00e5ff, width=1)
M5Line(x1=12, y1=122, x2=308, y2=122, color=0xff00ff, width=1)

M5Line(x1=12, y1=48, x2=12, y2=122, color=0x00e5ff, width=1)
M5Line(x1=308, y1=48, x2=308, y2=122, color=0xff00ff, width=1)

# glow accents
M5Line(x1=18, y1=48, x2=140, y2=48, color=0xff00ff, width=1)
M5Line(x1=180, y1=122, x2=300, y2=122, color=0x00e5ff, width=1)

weather_city = M5Label(
    'LAUSANNE',
    x=20,
    y=56,
    color=0x00e5ff,
    font=FONT_MONT_14
)

weather_desc = M5Label(
    'OVERCAST',
    x=20,
    y=80,
    color=0xb0b7c3,
    font=FONT_MONT_14
)

weather_temp = M5Label(
    '--.-°C',
    x=180,
    y=58,
    color=0xffcc00,
    font=FONT_MONT_26
)

weather_rain = M5Label(
    'RAIN --%',
    x=182,
    y=96,
    color=0x00d9ff,
    font=FONT_MONT_14
)

# =========================================================
# FORECAST PANEL
# =========================================================

forecast_title = M5Label(
    'FORECAST',
    x=18,
    y=132,
    color=0xff00ff,
    font=FONT_MONT_14
)

M5Line(x1=16, y1=154, x2=304, y2=154, color=0x182033, width=1)

forecast_1 = M5Label(
    '--:-- --.-°C',
    x=18,
    y=164,
    color=0xffcc00,
    font=FONT_MONT_14
)

forecast_2 = M5Label(
    '--:-- --.-°C',
    x=18,
    y=182,
    color=0x00ffff,
    font=FONT_MONT_14
)

forecast_3 = M5Label(
    '--:-- --.-°C',
    x=18,
    y=200,
    color=0x00ff99,
    font=FONT_MONT_14
)

forecast_4 = M5Label(
    '--:-- --.-°C',
    x=18,
    y=218,
    color=0xff00ff,
    font=FONT_MONT_14
)

# =========================================================
# INDOOR SENSOR PANEL
# =========================================================

indoor_title = M5Label(
    'INDOOR',
    x=170,
    y=132,
    color=0x00e5ff,
    font=FONT_MONT_14
)

# Indoor Temp
indoor_temp = M5Label(
    'T --.-°C',
    x=170,
    y=156,
    color=0xffcc00,
    font=FONT_MONT_14
)

# Indoor Humidity
indoor_hum = M5Label(
    'H --%',
    x=170,
    y=172,
    color=0x00d9ff,
    font=FONT_MONT_14
)

# Pressure
indoor_press = M5Label(
    'P ----hPa',
    x=170,
    y=188,
    color=0x00ff99,
    font=FONT_MONT_14
)

# TVOC
tvoc_label = M5Label(
    'TVOC ---ppb',
    x=170,
    y=204,
    color=0xff00ff,
    font=FONT_MONT_14
)

# eCO2
eco2_label = M5Label(
    'CO2 ----ppm',
    x=170,
    y=218,
    color=0xff3366,
    font=FONT_MONT_14
)

# =========================================================
# SENSORS
# =========================================================

env3_0 = unit.get(unit.ENV3, unit.PORTA)
tvoc_0 = unit.get(unit.TVOC, unit.PORTC)

# =========================================================
# WEATHER STORAGE
# =========================================================

weather_data = None

# =========================================================
# WEATHER FETCH
# =========================================================

def fetch_weather():

    global weather_data

    try:

        req = urequests.request(
            method='GET',
            url='https://django-backend-947281260717.europe-west1.run.app/api/openweather/'
        )

        weather_data = req.json()

        req.close()

        status_label.set_text('SYNC')
        status_label.set_text_color(0x00ff99)

        gc.collect()

    except:

        status_label.set_text('ERR ' + current_ssid)
        status_label.set_text_color(0xff3355)

# =========================================================
# UPDATE WEATHER UI
# =========================================================

def update_weather_ui():

    global weather_data

    if weather_data is None:
        return

    current = weather_data['current']
    forecast = weather_data['forecast']

    # -----------------------
    # Current weather
    # -----------------------

    weather_city.set_text(current['city'].upper())

    weather_desc.set_text(
        current['description'].upper()
    )

    weather_temp.set_text(
        '{:.1f}°C'.format(current['temp_c'])
    )

    # Chance of rain
    rain_chance = int(forecast[0]['pop'] * 100)

    weather_rain.set_text(
        'RAIN {}%'.format(rain_chance)
    )

    # -----------------------
    # Forecast
    # -----------------------

    try:

        f1 = forecast[0]
        f2 = forecast[1]
        f3 = forecast[2]
        f4 = forecast[3]

        forecast_1.set_text(
            '{}  {:.1f}°C'.format(
                f1['time'][11:16],
                f1['temp_c']
            )
        )

        forecast_2.set_text(
            '{}  {:.1f}°C'.format(
                f2['time'][11:16],
                f2['temp_c']
            )
        )

        forecast_3.set_text(
            '{}  {:.1f}°C'.format(
                f3['time'][11:16],
                f3['temp_c']
            )
        )
        
        forecast_4.set_text(
            '{}  {:.1f}°C'.format(
                f4['time'][11:16],
                f4['temp_c']
            )
        )

    except:
        pass

# =========================================================
# WIFI CONNECT
# =========================================================

connect_wifi(current_wifi)

# =========================================================
# RTC SYNC
# =========================================================
try:
    ntp = ntptime.client(host='cn.pool.ntp.org', timezone=2)
except:
    pass

rtc.settime('ntp', host='cn.pool.ntp.org', tzone=0)

# =========================================================
# INITIAL WEATHER LOAD
# =========================================================

fetch_weather()
update_weather_ui()

# =========================================================
# MAIN LOOP
# =========================================================

while True:
  
    if should_connect:
        should_connect = False
        connect_wifi(current_wifi)

    # -----------------------
    # Clock
    # -----------------------
    try:
        time_label.set_text(
            ntp.formatDatetime('-', ':')
        )
    except:
        time_label.set_text('--:--:--')

    # -----------------------
    # Sensor readings
    # -----------------------

    temp = env3_0.temperature
    hum = env3_0.humidity
    press = env3_0.pressure

    tvoc = tvoc_0.TVOC
    eco2 = tvoc_0.eCO2

    # -----------------------
    # INDOOR UI
    # -----------------------
      
    indoor_temp.set_text(
        'T {:.1f}°C'.format(temp)
    )
    
    indoor_hum.set_text(
        'H {:.0f}%'.format(hum)
    )
    
    indoor_press.set_text(
        'P {:.0f} hPa'.format(press)
    )
    
    tvoc_label.set_text(
        'TVOC {} ppb'.format(tvoc)
    )
    
    eco2_label.set_text(
        'CO2 {} ppm'.format(eco2)
    )
    
    # motion
    if pir.value() == 1:
        motion_detected()

    # -----------------------
    # Weather refresh
    # -----------------------

    now = time.time()

    if now - last_weather_update >= WEATHER_REFRESH:

        fetch_weather()
        update_weather_ui()

        last_weather_update = now

    # -----------------------
    # Sensor upload
    # -----------------------

    if now - last_send >= SEND_INTERVAL:

        if upload_sensor_data():

            last_send = now

    wait(DISPLAY_REFRESH)