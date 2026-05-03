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
    humidity: number;
    description: string;
  };
  forecast: {
    time: string;
    temp: number;
  }[];
};

export default function WeatherDashboard() {
  const [sensorData, setSensorData] = useState<WeatherPoint[]>([]);
  const [weather, setWeather] = useState<WeatherFull | null>(null);
  const [data, setData] = useState(null);
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
      setData(result);
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
    time: item.time, // keep raw ISO / dt_txt
    temp: item.temp,
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
        {loading ? "Loading..." : "Get Weather"}
      </button>

      {error && <p style={{ color: "red" }}>{error}</p>}

      <h2>{weather.current.city}</h2>
      <div style={{ marginBottom: 30 }}>
        🌡️ {weather.current.temp}°C <br />
        💧 {weather.current.humidity}% <br />
        ☁️ {weather.current.description}
      </div>

      {/* FORECAST CHART */}
      <div style={{ width: "100%", height: 300, marginBottom: 50 }}>
        <h3>Forecast Temperature</h3>
        <ResponsiveContainer>
          <LineChart data={forecastData}>
            <XAxis
              dataKey="time"
              tickFormatter={(t) =>
                new Date(t).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })
              }
              minTickGap={20}
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
            />
            <Line
              type="monotone"
              dataKey="temp"
              stroke="#ff7300"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* SENSOR CHARTS */}
      {renderChart("temperature", "#ff7300", "Temperature")}
      {renderChart("humidity", "#00c49f", "Humidity")}
      {renderChart("pressure", "#8884d8", "Pressure", [950, 990])}
      {renderChart("tvoc", "#ff4d4f", "TVOC")}
      {renderChart("eco2", "#52c41a", "eCO₂")}
    </div>
  );
}