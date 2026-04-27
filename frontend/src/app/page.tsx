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

export default function WeatherChart() {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_DJANGO_API_URL}/api/weather/`)
      .then((res) => res.json())
      .then(setData);
  }, []);

  return (
    <div style={{ width: "100%", height: 400 }}>
      <h2>Weather Data</h2>

      <ResponsiveContainer>
        <LineChart data={data}>
          <XAxis dataKey="timestamp" hide />
          <YAxis />
          <Tooltip />

          <Line
            type="monotone"
            dataKey="temperature"
            stroke="#ff7300"
          />

          <Line
            type="monotone"
            dataKey="humidity"
            stroke="#387908"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}