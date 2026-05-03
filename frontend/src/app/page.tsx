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
    time: new Date(item.time).toLocaleString(),
    temp: item.temp,
  }));

  return (
    <div style={{ background: "#111", color: "white", padding: 20 }}>
      {/* CURRENT WEATHER */}
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
            <XAxis dataKey="time" hide />
            <YAxis />
            <Tooltip />
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