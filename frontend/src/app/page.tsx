"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

type WeatherPoint = {
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
    temp: number;
    feels_like: number;
    temp_min: number;
    temp_max: number;
    humidity: number;
    pressure: number;
    description: string;
    icon: string;
    wind_speed: number;
    clouds: number;
    sunrise: number;
    sunset: number;
    visibility: number | null;
  };
  forecast: {
    time: string;
    temp: number;
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
  const [sensorData, setSensorData] = useState<WeatherPoint[]>([]);
  const [weather, setWeather] = useState<WeatherFull | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [city, setCity] = useState("Lausanne");

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
    dataKey: keyof WeatherPoint,
    color: string,
    title: string,
    yDomain?: [number, number]
  ) => (
    <div style={{ width: "100%", height: 300, marginBottom: 40 }}>
      <h3>{title}</h3>
      <ResponsiveContainer>
        <LineChart data={sensorData}>
          <XAxis
            dataKey="timestamp"
            tickFormatter={(t) => new Date(t).toLocaleTimeString()}
          />
          <YAxis domain={yDomain ?? ["auto", "auto"]} />
          <Tooltip />
          <Line type="monotone" dataKey={dataKey} stroke={color} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );

  if (!weather) return <div style={{ padding: 20 }}>Loading...</div>;

  const forecastData = weather.forecast.map((item) => ({
    time: item.time,
    temp: item.temp,
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

      <h2>{weather.current.city}</h2>
      <div style={{ marginBottom: 30 }}>
        <img
          src={`https://openweathermap.org/img/wn/${weather.current.icon}@2x.png`}
          alt="weather icon"
        />

        <div>🌡️ {weather.current.temp}°C (feels {weather.current.feels_like}°C)</div>
        <div>📉 Min: {weather.current.temp_min}°C | 📈 Max: {weather.current.temp_max}°C</div>

        <div>💧 Humidity: {weather.current.humidity}%</div>
        <div>🎈 Pressure: {weather.current.pressure} hPa</div>

        <div>🌬️ Wind: {weather.current.wind_speed} m/s</div>
        <div>☁️ Clouds: {weather.current.clouds}%</div>

        <div>👁️ Visibility: {weather.current.visibility ?? "N/A"} m</div>

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
              labelFormatter={(label) =>
                new Date(label).toLocaleString([], {
                  weekday: "short",
                  hour: "2-digit",
                  minute: "2-digit",
                })
              }
              formatter={(value, name) => {
                if (name === "humidity") return [`${value}%`, "Humidity"];
                if (name === "pop") return [`${value}%`, "Rain Chance"];
                if (name === "temp") return [`${value}°C`, "Temperature"];
                return [value, name];
              }}
            />

            {/* Temperature */}
            <Line
              type="monotone"
              dataKey="temp"
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
      {renderChart("temperature", "#ff7300", "Temperature Indoor")}
      {renderChart("humidity", "#00c49f", "Humidity Indoor")}
      {renderChart("pressure", "#8884d8", "Pressure Indoor", [950, 990])}
      {renderChart("tvoc", "#ff4d4f", "TVOC Indoor")}
      {renderChart("eco2", "#52c41a", "eCO₂ Indoor")}
    </div>
  );
}