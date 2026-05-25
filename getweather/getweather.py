from google.cloud import bigquery
from datetime import datetime, timezone

client = bigquery.Client()
table_id = "esoteric-storm-496611-p0.weather.weather-data"

def ingest(request):
    request_json = request.get_json()

    if not request_json:
        return "Invalid JSON", 400

    timestamp = request_json["timestamp"]

    dt_utc = datetime(
        timestamp[0],  # year
        timestamp[1],  # month
        timestamp[2],  # day
        timestamp[4],  # hour
        timestamp[5],  # minute
        timestamp[6],  # second
        tzinfo=timezone.utc
    )

    iaq = request_json.get("iaq_baseline")
    iaq_baseline_1, iaq_baseline_2 = iaq

    rows = [{
        "device_id": request_json["device_id"],
        "temperature": request_json["temperature"],
        "humidity": request_json["humidity"],
        "pressure": request_json["pressure"],
        "timestamp": dt_utc.isoformat(),
        "tvoc": int(request_json.get("tvoc")),
        "eco2": int(request_json.get("eco2")),
        "h2": int(request_json.get("h2") or 0),
        "ethanol": int(request_json.get("ethanol")),
        "iaq_baseline_1": iaq_baseline_1,
        "iaq_baseline_2": iaq_baseline_2
    }]

    errors = client.insert_rows_json(table_id, rows)

    if errors == []:
        return "OK", 200
    else:
        return str(errors), 500
    