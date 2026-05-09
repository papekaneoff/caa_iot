"use client";

import { useEffect, useState } from "react";
import { ValueType } from "recharts/types/component/DefaultTooltipContent";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

type SensorPoint = {
  timestamp: string;
  temperature_c: number;
  temperature_f: number;
  humidity: number;
  pressure: number;
  tvoc: number;
  eco2: number;
};

type SensorUIPoint = {
  timestamp: string;
  temperature: number;
  humidity: number;
  pressure: number;
  tvoc: number;
  eco2: number;
};

type WeatherFull = {
  current: {
    city: string;
    temp_c: number;
    temp_f: number;
    feels_like_c: number;
    feels_like_f: number;
    temp_min_c: number;
    temp_min_f: number;
    temp_max_c: number;
    temp_max_f: number;
    humidity: number;
    pressure: number;
    description: string;
    icon: string;
    wind_speed_ms: number;
    wind_speed_mph: number;
    clouds: number;
    sunrise: number;
    sunset: number;
    visibility_m: number | null;
    visibility_miles: number | null;
  };
  forecast: {
    time: string;
    temp_c: number;
    temp_f: number;
    humidity: number;
    pop?: number;
    wind_speed?: number;
    description?: string;
  }[];
};

const formatTime = (ts: number) =>
  new Date(ts * 1000).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

export default function WeatherDashboard() {
  const [sensorData, setSensorData] = useState<SensorPoint[]>([]);
  const [weather, setWeather] = useState<WeatherFull | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [city, setCity] = useState("Lausanne");
  const [unit, setUnit] = useState<"metric" | "imperial">("metric");

  const formatValue = (v: ValueType | undefined, unit: string) => {
    if (v == null) return "N/A";
    return `${v} ${unit}`;
  };

  const sensorMeta = {
    temperature: {
      label: "Temperature Indoor",
      unit: unit === "metric" ? "°C" : "°F",
      format: (v: number) =>
        unit === "metric" ? v : v * 1.8 + 32,
    },
    humidity: { label: "Humidity Indoor", unit: "%", format: (v: number) => v },
    pressure: { label: "Pressure Indoor", unit: "hPa", format: (v: number) => v },
    tvoc: { label: "TVOC Indoor", unit: "ppb", format: (v: number) => v },
    eco2: { label: "eCO₂ Indoor", unit: "ppm", format: (v: number) => v },
  };

  const convertedSensorData: SensorUIPoint[] = sensorData.map((d) => ({
    timestamp: d.timestamp,
    temperature:
      unit === "metric"
        ? d.temperature_c
        : d.temperature_f,
    humidity: d.humidity,
    pressure: d.pressure,
    tvoc: d.tvoc,
    eco2: d.eco2,
  }));

  const convertTemp = (c: number) =>
    unit === "metric" ? c : c * 1.8 + 32;

  const fetchWeather = async (selectedCity: string): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_DJANGO_API_URL}/api/openweather/?city=${encodeURIComponent(selectedCity)}`
      );

      if (!res.ok) {
        throw new Error("Failed to fetch weather");
      }

      const result = await res.json();
      setWeather(result);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Unknown error occurred");
      }
    }
    finally {
      setLoading(false);
    }
  };

  const handleSearch = () => {
    fetchWeather(city);
  };

  useEffect(() => {
    // sensor / IoT data
    fetch(`${process.env.NEXT_PUBLIC_DJANGO_API_URL}/api/sensor/`)
      .then((res) => res.json())
      .then(setSensorData);

    // full weather data
    fetch(
      `${process.env.NEXT_PUBLIC_DJANGO_API_URL}/api/openweather/?city=Lausanne`
    )
      .then((res) => res.json())
      .then(setWeather);
  }, []);

  const renderChart = (
    data: SensorUIPoint[],
    dataKey: keyof SensorUIPoint,
    color: string,
    title: string,
    unit: string,
    yDomain?: [number, number]
  ) => (
    <div style={{ width: "100%", height: 300, marginBottom: 40 }}>
      <h3 style={{ marginBottom: 12 }}>
        {title} ({unit})
      </h3>

      <ResponsiveContainer>
        <LineChart data={data}>
          <XAxis
            dataKey="timestamp"
            tickFormatter={(t) =>
              new Date(t.replace(" UTC", "Z")).toLocaleString([], {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })
            }
            minTickGap={40}
          />

          <YAxis />

          <Tooltip
            contentStyle={{
              backgroundColor: "#1f1f1f",
              border: "1px solid #333",
              borderRadius: 12,
              color: "#fff",
            }}
            labelStyle={{
              color: "#aaa",
              marginBottom: 8,
              display: "block",
            }}
            formatter={(value, name) => {
              if (value == null) return ["—", name];

              if (name === "temperature") {
                return [
                  `${convertTemp(Number(value)).toFixed(1)} ${unit === "metric" ? "°C" : "°F"}`,
                  "Temperature",
                ];
              }

              if (name === "humidity") return [`${value}%`, "Humidity"];
              if (name === "pressure") return [`${value} hPa`, "Pressure"];
              if (name === "tvoc") return [`${value} ppb`, "TVOC"];
              if (name === "eco2") return [`${value} ppm`, "eCO₂"];

              return [value, String(name)];
            }}
          />

          <Line
            type="monotone"
            dataKey={dataKey}
            stroke="#ff7300"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );

  if (!weather) return <div style={{ padding: 20 }}>Loading...</div>;

  const isMetric = unit === "metric";

  const currentTemp = isMetric
    ? weather.current.temp_c
    : weather.current.temp_f;

  const feelsLike = isMetric
    ? weather.current.feels_like_c
    : weather.current.feels_like_f;

  const tempMin = isMetric
    ? weather.current.temp_min_c
    : weather.current.temp_min_f;

  const tempMax = isMetric
    ? weather.current.temp_max_c
    : weather.current.temp_max_f;

  const windSpeed = isMetric
    ? weather.current.wind_speed_ms
    : weather.current.wind_speed_mph;

  const visibility = isMetric
    ? weather.current.visibility_m
    : weather.current.visibility_miles;

  const forecastTempKey = isMetric ? "temp_c" : "temp_f";

  const tempUnit = isMetric ? "°C" : "°F";
  const windUnit = isMetric ? "m/s" : "mph";
  const visibilityUnit = isMetric ? "m" : "miles";

  const forecastData = weather.forecast.map((item) => ({
    time: item.time,
    temp_c: item.temp_c,
    temp_f: item.temp_f,
    humidity: item.humidity,
    pop: item.pop ? item.pop * 100 : 0, // convert to %
  }));

  return (
    <div style={{ background: "#111", color: "white", padding: 20 }}>
      {/* CURRENT WEATHER */}
      <input
        value={city}
        onChange={(e) => setCity(e.target.value)}
        placeholder="Enter city"
        style={{ padding: 8, marginRight: 10 }}
      />

      <button onClick={handleSearch} disabled={loading}>
        {loading ? "Loading..." : "Get Weather Forecast"}
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <button
        onClick={() => setUnit("metric")}
        style={{
          marginLeft: 10,
          background: unit === "metric" ? "#444" : "#222",
          color: "white",
          padding: "8px 12px",
        }}
      >
        °C
      </button>

      <button
        onClick={() => setUnit("imperial")}
        style={{
          marginLeft: 5,
          background: unit === "imperial" ? "#444" : "#222",
          color: "white",
          padding: "8px 12px",
        }}
      >
        °F
      </button>

      <h2>{weather.current.city}</h2>
      <div style={{ marginBottom: 30 }}>
        <img
          src={`https://openweathermap.org/img/wn/${weather.current.icon}@2x.png`}
          alt="weather icon"
        />

        <div>
          🌡️ {currentTemp}{tempUnit}
          {" "}
          (feels {feelsLike}{tempUnit})
        </div>
        <div>
          📉 Min: {tempMin}{tempUnit}
          {" | "}
          📈 Max: {tempMax}{tempUnit}
        </div>

        <div>💧 Humidity: {weather.current.humidity}%</div>
        <div>🎈 Pressure: {weather.current.pressure} hPa</div>

        <div>
          🌬️ Wind: {windSpeed} {windUnit}
        </div>
        <div>☁️ Clouds: {weather.current.clouds}%</div>

        <div>
          👁️ Visibility: {visibility ?? "N/A"} {visibilityUnit}
        </div>

        <div>🌅 Sunrise: {formatTime(weather.current.sunrise)}</div>
        <div>🌇 Sunset: {formatTime(weather.current.sunset)}</div>

        <div style={{ textTransform: "capitalize" }}>
          ☁️ {weather.current.description}
        </div>
      </div>

      {/* FORECAST CHART */}
      <div style={{ width: "100%", height: 300, marginBottom: 50 }}>
        <h3>Forecast Overview</h3>

        <ResponsiveContainer>
          <LineChart data={forecastData}>
            <XAxis
              dataKey="time"
              tickFormatter={(t) =>
                new Date(t).toLocaleString([], {
                  weekday: "short",
                  hour: "2-digit",
                  minute: "2-digit",
                })
              }
              minTickGap={30}
            />

            <YAxis />

            <Tooltip
              contentStyle={{
                backgroundColor: "#1f1f1f",
                border: "1px solid #333",
                borderRadius: 12,
                color: "#fff",
              }}
              labelStyle={{
                color: "#aaa",
                marginBottom: 8,
                display: "block",
              }}
              labelFormatter={(label) =>
                new Date(label).toLocaleString([], {
                  weekday: "short",
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })
              }
              formatter={(value, name) => {
                if (value == null) return ["—", name];

                switch (name) {
                  case "humidity":
                    return [`${value}%`, "Humidity"];
                  case "pop":
                    return [`${value}%`, "Rain Chance"];
                  case forecastTempKey:
                    return [`${value}${tempUnit}`, "Temperature"];
                  default:
                    return [value, String(name)];
                }
              }}
            />

            {/* Temperature */}
            <Line
              type="monotone"
              dataKey={forecastTempKey}
              stroke="#ff7300"
              dot={false}
            />

            {/* Humidity */}
            <Line
              type="monotone"
              dataKey="humidity"
              stroke="#00c49f"
              dot={false}
            />

            {/* Rain probability */}
            <Line
              type="monotone"
              dataKey="pop"
              stroke="#1890ff"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* SENSOR CHARTS */}
      {renderChart(
        convertedSensorData,
        "temperature",
        "#ff7300",
        `Temperature Indoor`,
        unit === "metric" ? "°C" : "°F"
      )}
      {renderChart(convertedSensorData, "humidity", "#00c49f", "Humidity Indoor", "%")}
      {renderChart(convertedSensorData, "pressure", "#8884d8", "Pressure Indoor", "hPa")}
      {renderChart(convertedSensorData, "tvoc", "#ff4d4f", "TVOC Indoor", "ppb")}
      {renderChart(convertedSensorData, "eco2", "#52c41a", "eCO₂ Indoor", "ppm")}
    </div>
  );
}