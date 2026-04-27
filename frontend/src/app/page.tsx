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
};

const [data, setData] = useState<WeatherPoint[]>([]);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_DJANGO_API_URL}/api/weather/`)
      .then((res) => res.json())
      .then(setData);
  }, []);

  const renderChart = (
    key: string,
    color: string,
    title: string
  ) => (
    <div style={{ width: "100%", height: 300, marginBottom: 40 }}>
      <h3>{title}</h3>
      <ResponsiveContainer>
        <LineChart data={data}>
          <XAxis
            dataKey="timestamp"
            tickFormatter={(t) => new Date(t).toLocaleTimeString()}
          />
          <YAxis />
          <Tooltip />

          <Line
            type="monotone"
            dataKey={key}
            stroke={color}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}