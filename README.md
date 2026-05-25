# caa_iot — Indoor/Outdoor Weather Monitor

A smart IoT weather monitoring system built with M5Stack devices, Google Cloud, and BigQuery.

## 🌐 Live URLs
- **Frontend Dashboard**: https://nextjs-frontend-947281260717.europe-west1.run.app
- **Backend API**: https://django-backend-947281260717.europe-west1.run.app
- **Voice Assistant API**: https://vs-947281260717.europe-west1.run.app

## 👥 Team
| Name | Contribution |
|------|-------------|
| Karim | Backend (Django REST API), Frontend (Next.js dashboard), Cloud infrastructure, BigQuery, OpenWeatherMap integration |
| Kane | Device interaction — Voice assistant (STT/TTS), presence detection, M5Stack UI, Cloud Run voice service |

---

## 📁 Repository Structure

```
caa_iot/
├── backend/          # Django REST API — serves sensor data and weather info
├── frontend/         # Next.js web dashboard — historical data visualization
├── device/           # M5Stack on-device code and cloud voice service
│   ├── vs.py         # Voice assistant Flask server (Cloud Run) — TTS, STT, Q&A, presence
│   └── getweather.py # Cloud Function — ingests sensor data into BigQuery
├── cloudbuild.yaml   # Google Cloud Build CI/CD pipeline
├── docker-compose.yml
└── README.md
```

---

## 🏗️ Architecture

```
M5Stack (sensors: ENV III, PIR, Air Quality)
    │
    ├── POST /ingest ──► getweather (Cloud Function) ──► BigQuery
    │
    ├── POST /presence ──► vs (Cloud Run) ──► Google TTS ──► M5Stack speaker
    ├── POST /ask ──────► vs (Cloud Run) ──► BigQuery ──► Google TTS
    └── POST /tts/stt ──► vs (Cloud Run) ──► Google Speech APIs
                │
                └──► django-backend (Cloud Run) ──► nextjs-frontend (Cloud Run)
```

---

## 🚀 How to Deploy

### Prerequisites
- Google Cloud project with billing enabled
- BigQuery dataset: `weather.weather-data`
- APIs enabled: Cloud Speech-to-Text, Cloud Text-to-Speech, BigQuery

### 1. Clone the repo
```bash
git clone https://github.com/papekaneoff/caa_iot.git
cd caa_iot
```

### 2. Set up environment variables
Create a `.env` file (never commit this!):
```
GCP_PROJECT_ID=your-project-id
OPENWEATHER_API_KEY=your-openweathermap-key
DJANGO_SECRET_KEY=your-secret-key
```

### 3. Deploy via Cloud Build
Connect your GitHub repo to Cloud Build and push to `main` — everything deploys automatically.

Or trigger manually from the Cloud Build console.

### 4. M5Stack Setup
- Flash MicroPython firmware on M5Stack Core2
- Open UIFlow 1.0 at flow.m5stack.com
- Connect to WiFi and paste the device code
- Update `CLOUD_RUN_URL` with your `vs` service URL

---

## 🎙️ Voice Assistant Features

The M5Stack supports **natural language Q&A** via voice:

| Question | Answer |
|----------|--------|
| "What is the temperature now?" | Current indoor temperature from BigQuery |
| "What was the temperature yesterday?" | Daily average from BigQuery |
| "Did humidity exceed 50% two days ago?" | Yes/No from BigQuery |
| "What is the air quality?" | CO2 level and quality rating |
| "What is the weather?" | OpenWeatherMap current conditions |

**Automatic announcements** (PIR motion sensor):
- 🌤️ Weather + indoor conditions on motion — max **once per hour**
- 🌂 Rain reminder if rain is forecast
- 🥶 Cold weather warning (below 5°C)
- 💧 Low humidity alert (below 40%)
- 🏭 Bad air quality alert (CO2 above 1000 ppm)

---

## ⚙️ Environment Variables

| Variable | Description | Used by |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | Google Cloud project ID | vs, getweather |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key | vs, backend |
| `DJANGO_SECRET_KEY` | Django secret key | backend |

> ⚠️ **Never commit `.env` or `service-account.json` to the repo!**

---

## 📹 Demo Video
[Link to YouTube video — add here]
