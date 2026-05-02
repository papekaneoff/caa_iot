"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from "recharts";

type WeatherPoint = {
  timestamp: string;
  temperature: number;
  humidity: number;
  pressure: number;
  tvoc: number;
  eco2: number;
};

export default function WeatherCharts() {
  const [data, setData] = useState<WeatherPoint[]>([]);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_DJANGO_API_URL}/api/weather/`)
      .then((res) => res.json())
      .then(setData);
  }, []);

  const renderChart = (
    key: string,
    color: string,
    title: string,
    yDomain?: [number, number]
  ) => (
    <div style={{ width: "100%", height: 300, marginBottom: 40 }}>
      <h3>{title}</h3>
      <ResponsiveContainer>
        <LineChart data={data}>
          <XAxis
            dataKey="timestamp"
            tickFormatter={(t) => new Date(t).toLocaleTimeString()}
          />
          <YAxis domain={yDomain ?? ["auto", "auto"]} />
          <Tooltip />

          <Line type="monotone" dataKey={key} stroke={color} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );

  return (
    <div style={{ background: "#111", color: "white", padding: 20 }}>
      {renderChart("temperature", "#ff7300", "Temperature")}
      {renderChart("humidity", "#00c49f", "Humidity")}
      {renderChart("pressure", "#8884d8", "Pressure", [950, 990])}
      {renderChart("tvoc", "#ff4d4f", "TVOC")}
      {renderChart("eco2", "#52c41a", "eCO₂")}
    </div>
  );
}