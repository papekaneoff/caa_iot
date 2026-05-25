# caa_iot — Indoor/Outdoor Weather Monitor

A smart IoT weather monitoring system built with M5Stack devices, Google Cloud, and BigQuery.

- **Architecture Diagram**: https://papekaneoff.github.io/caa_iot/architecture.html


## 🌐 Live URLs
- **Frontend Dashboard**: https://nextjs-frontend-947281260717.europe-west1.run.app
- **Backend API**: https://django-backend-947281260717.europe-west1.run.app/api/health/
- **Voice Assistant**: https://vs-947281260717.europe-west1.run.app
- **Data Ingestion**: https://getweather-947281260717.europe-west1.run.app

## 👥 Team
| Name | Contribution |
|------|-------------|
| Karim Al Khadzh | Backend (Django REST API), Frontend (Next.js dashboard), Cloud infrastructure, BigQuery, OpenWeatherMap integration, M5Stack device UI, data ingestion service (`getweather`) |
| Pape Kane | Voice assistant Cloud Run service (`vs`), data ingestion service (`getweather`), M5Stack device UI, Speech-to-Text/Text-to-Speech, presence detection |

---

## 📁 Repository Structure

```
├── backend/          # Django REST API
│   ├── core/         # Views, URLs, models
│   ├── config/       # Django settings
│   └── Dockerfile
├── frontend/         # Next.js web dashboard
│   └── Dockerfile
├── vs/               # Voice Assistant (Cloud Run)
│   ├── vs.py         # TTS, STT, Q&A, presence, weather
│   └── Dockerfile
├── getweather/       # Data Ingestion (Cloud Run)
│   ├── getweather.py # Receives M5Stack data → inserts into BigQuery
│   └── Dockerfile
├── device/           # M5Stack on-device code
│   ├── assistant.py        # Voice assistant device code
│   └── neon_weather_grid.py # Weather display UI
├── architecture.html # System architecture diagram
├── cloudbuild.yaml   # CI/CD pipeline — auto-deploys all 4 services
├── docker-compose.yml
└── README.md
```

---

## 🏗️ Architecture

```
M5Stack Core2 (ENV III, PIR, Air Quality sensors)
    │
    ├── POST / ───────────► getweather (Cloud Run) ──► BigQuery
    │
    ├── POST /presence ───► vs (Cloud Run) ──► Google TTS ──► M5Stack speaker
    ├── POST /ask ────────► vs (Cloud Run) ──► BigQuery ──► Google TTS
    └── POST /tts + /stt ─► vs (Cloud Run) ──► Google Speech APIs
                │
                └──► django-backend ──► nextjs-frontend
```

---

## 🚀 How to Deploy

### 1. Clone the repo
```bash
git clone https://github.com/papekaneoff/caa_iot.git
cd caa_iot
```

### 2. Set up Secret Manager on Google Cloud
Add these secrets in Google Secret Manager:
```
OPENWEATHER_API_KEY = your OpenWeatherMap API key
DJANGO_SECRET_KEY   = your Django secret key
```

### 3. Connect GitHub to Cloud Build
- Go to https://console.cloud.google.com/cloud-build/triggers
- Connect the `papekaneoff/caa_iot` repository
- Every push to `main` auto-deploys all 4 services

### 4. Push to deploy
```bash
git push origin main
```

### 5. M5Stack Setup
- Open UIFlow 1.0 at flow.m5stack.com
- Connect M5Stack Core2 to WiFi
- Set `VS_URL = "https://vs-947281260717.europe-west1.run.app"`
- Set `GETWEATHER_URL = "https://getweather-947281260717.europe-west1.run.app"`

---

## 🎙️ Voice Assistant API (`vs`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Status check → `{"status": "running"}` |
| `/weather` | GET | Current outdoor weather (OpenWeatherMap) |
| `/ask` | POST | Natural language Q&A from BigQuery |
| `/tts` | POST | Text → WAV audio |
| `/stt` | POST | Audio → transcribed text |
| `/presence` | POST | Motion detected → weather announcement (1h cooldown) |
| `/morning` | GET | Morning weather reminder |

**Example questions:**
- "What is the temperature now?"
- "What was the temperature yesterday?"
- "Did humidity exceed 50% two days ago?"
- "What is the air quality?"

---

## 📡 Data Ingestion API (`getweather`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | POST | Receive sensor data from M5Stack → insert into BigQuery |

---

## 🔌 Backend API (`django-backend`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/sensor/` | GET | Latest sensor data |
| `/api/openweather/` | GET | Outdoor weather data |
| `/api/health/` | GET | Health check → `{"status": "ok"}` |

---

## ⚙️ Environment Variables

| Variable | Description | Used by |
|----------|-------------|---------|
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key | vs, backend |
| `DJANGO_SECRET_KEY` | Django secret key | backend |

> ⚠️ **Never commit `.env` or `service-account.json` to the repo!**
> All secrets are managed via Google Secret Manager.

---

## 📹 Demo Video
[Link to YouTube video — add here]
