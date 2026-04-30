"""
interaction_manager.py
Interprets user voice questions and fetches relevant data from BigQuery.
Uses Google Cloud Vertex AI (Gemini) OR OpenAI GPT to generate natural answers.

Pipeline:
  user question (text)
    → parse_intent() — extracts structured intent via LLM
    → BigQuery query — fetches relevant sensor data
    → generate_natural_answer() — produces a spoken response
"""

import os
import json
from datetime import datetime, timedelta
from google.cloud import bigquery

# ── LLM for intent parsing: try Vertex AI Gemini, fallback to OpenAI ──────────
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
    GCP_REGION     = os.environ.get("GCP_REGION", "europe-west1")
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    gemini_model = GenerativeModel("gemini-1.5-flash")
    USE_GEMINI = True
    print("[Interaction] Using Google Gemini for LLM.")
except Exception:
    from openai import OpenAI
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    USE_GEMINI = False
    print("[Interaction] Gemini unavailable, falling back to OpenAI GPT.")

# ── BigQuery ──────────────────────────────────────────────────────────────────
GCP_PROJECT_ID   = os.environ.get("GCP_PROJECT_ID")
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", "weather_monitor")
BIGQUERY_TABLE   = os.environ.get("BIGQUERY_TABLE", "sensor_data")
FULL_TABLE       = f"`{GCP_PROJECT_ID}.{BIGQUERY_DATASET}.{BIGQUERY_TABLE}`"

bq_client = bigquery.Client(project=GCP_PROJECT_ID)


# ─── BigQuery Queries ─────────────────────────────────────────────────────────

def _run_query(sql: str) -> list[dict]:
    """Executes a BigQuery SQL query and returns rows as list of dicts."""
    try:
        rows = bq_client.query(sql).result()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"[BQ] Query error: {e}")
        return []


def get_average_for_day(metric: str, days_ago: int = 0) -> float | None:
    """Average of a metric for a given day (0=today, 1=yesterday, etc.)."""
    date = (datetime.utcnow() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    sql = f"""
        SELECT AVG({metric}) AS val
        FROM {FULL_TABLE}
        WHERE DATE(timestamp) = '{date}'
    """
    result = _run_query(sql)
    return round(result[0]["val"], 1) if result and result[0]["val"] is not None else None


def get_max_for_day(metric: str, days_ago: int = 0) -> float | None:
    """Maximum of a metric for a given day."""
    date = (datetime.utcnow() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    sql = f"""
        SELECT MAX({metric}) AS val
        FROM {FULL_TABLE}
        WHERE DATE(timestamp) = '{date}'
    """
    result = _run_query(sql)
    return round(result[0]["val"], 1) if result and result[0]["val"] is not None else None


def did_metric_exceed(metric: str, threshold: float, days_ago: int = 0) -> bool:
    """Returns True if a metric ever exceeded a threshold on the given day."""
    date = (datetime.utcnow() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    sql = f"""
        SELECT COUNT(*) AS cnt
        FROM {FULL_TABLE}
        WHERE DATE(timestamp) = '{date}'
          AND {metric} > {threshold}
    """
    result = _run_query(sql)
    return result[0]["cnt"] > 0 if result else False


def get_latest_values() -> dict:
    """Returns the most recent row from the sensor table."""
    sql = f"""
        SELECT temperature_indoor, temperature_outdoor, humidity, air_quality, timestamp
        FROM {FULL_TABLE}
        ORDER BY timestamp DESC
        LIMIT 1
    """
    result = _run_query(sql)
    return result[0] if result else {}


# ─── LLM Helpers ──────────────────────────────────────────────────────────────

INTENT_PROMPT = """
You extract structured intent from questions about a home weather monitor.
Respond ONLY with a valid JSON object. No markdown, no explanation.

JSON fields:
- "intent": one of ["get_average", "get_max", "did_exceed", "current", "unknown"]
- "metric": one of ["temperature_indoor", "temperature_outdoor", "humidity", "air_quality"] or null
- "days_ago": integer (0=today, 1=yesterday, 2=two days ago)
- "threshold": float only for "did_exceed", else null

Examples:
"Quelle était la température hier ?"
→ {"intent":"get_average","metric":"temperature_indoor","days_ago":1,"threshold":null}

"Est-ce que l'humidité a dépassé 50% il y a 2 jours ?"
→ {"intent":"did_exceed","metric":"humidity","days_ago":2,"threshold":50.0}

"Quelle est la température actuelle ?"
→ {"intent":"current","metric":"temperature_indoor","days_ago":0,"threshold":null}

"What was the max air quality today?"
→ {"intent":"get_max","metric":"air_quality","days_ago":0,"threshold":null}
"""

ANSWER_PROMPT = """
You are a friendly home weather assistant.
Answer in the same language as the user's question (French or English).
Be concise — 1 to 2 sentences max. Use the data provided.
If data is null or unavailable, say so politely.
"""


def _call_llm(system: str, user: str) -> str:
    """Calls Gemini or OpenAI GPT depending on availability."""
    prompt = f"{system}\n\nUser: {user}"
    if USE_GEMINI:
        response = gemini_model.generate_content(prompt)
        return response.text.strip()
    else:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": user},
            ],
            temperature=0.0,
        )
        return response.choices[0].message.content.strip()


def parse_intent(user_text: str) -> dict:
    """Extracts structured intent from a natural language question."""
    try:
        raw = _call_llm(INTENT_PROMPT, user_text)
        # Strip possible markdown fences
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"[Intent] Parse error: {e}")
        return {"intent": "unknown"}


def generate_natural_answer(user_question: str, data: dict) -> str:
    """Generates a spoken answer from raw query data."""
    try:
        context = f"User question: {user_question}\nSensor data: {json.dumps(data, default=str)}"
        return _call_llm(ANSWER_PROMPT, context)
    except Exception as e:
        print(f"[Answer] Generation error: {e}")
        return "Désolé, je n'ai pas pu générer une réponse."


# ─── Main Handler ─────────────────────────────────────────────────────────────

def handle_question(user_text: str) -> str:
    """
    Full pipeline: parse intent → query BigQuery → generate natural answer.
    Returns answer string (ready to pass to tts_handler.speak()).
    """
    print(f"[Interaction] ❓ Question: '{user_text}'")

    parsed    = parse_intent(user_text)
    intent    = parsed.get("intent", "unknown")
    metric    = parsed.get("metric")
    days_ago  = parsed.get("days_ago", 0)
    threshold = parsed.get("threshold")

    raw_data = {}

    if intent == "get_average" and metric:
        val = get_average_for_day(metric, days_ago)
        raw_data = {"metric": metric, "days_ago": days_ago, "average": val}

    elif intent == "get_max" and metric:
        val = get_max_for_day(metric, days_ago)
        raw_data = {"metric": metric, "days_ago": days_ago, "max": val}

    elif intent == "did_exceed" and metric and threshold is not None:
        exceeded = did_metric_exceed(metric, threshold, days_ago)
        raw_data = {"metric": metric, "threshold": threshold, "days_ago": days_ago, "exceeded": exceeded}

    elif intent == "current":
        raw_data = get_latest_values()

    else:
        return (
            "Désolé, je n'ai pas compris. Essayez : "
            "« quelle était la température hier ? » ou "
            "« est-ce que l'humidité a dépassé 50% ? »"
        )

    return generate_natural_answer(user_text, raw_data)


# ─── Test ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tests = [
        "Quelle était la température intérieure hier ?",
        "Est-ce que l'humidité a dépassé 50% il y a 2 jours ?",
        "Quelle est la qualité de l'air maintenant ?",
        "What was the max outdoor temperature today?",
    ]
    for q in tests:
        print(f"\nQ: {q}")
        print(f"A: {handle_question(q)}")
