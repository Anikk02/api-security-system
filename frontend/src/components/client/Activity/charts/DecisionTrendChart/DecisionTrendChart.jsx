import React, { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
  ReferenceDot,
} from "recharts";
import { useNavigate } from "react-router-dom";
import "./DecisionTrendChart.css";

function DecisionTrendChart({ initialData = [] }) {
  const [data, setData] = useState(initialData);
  const navigate = useNavigate();

  // ================================
  // ⚡ 1. Real-time WebSocket
  // ================================
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/activity");

    ws.onmessage = (event) => {
      const newPoint = JSON.parse(event.data);

      setData((prev) => {
        const updated = [...prev, newPoint];
        return updated.slice(-20); // keep last 20 points
      });
    };

    ws.onerror = () => {
      console.log("WebSocket error");
    };

    return () => ws.close();
  }, []);

  // ================================
  // 🧠 2. Smart Anomaly Detection
  // ================================
  const avgBlocked =
    data.reduce((sum, d) => sum + d.blocked, 0) /
    (data.length || 1);

  const anomalies = data.filter(
    (d) => d.blocked > avgBlocked * 2
  );

  const isUnderAttack = anomalies.length > 0;

  // ================================
  // 🎯 3. Click → Correlate with Logs
  // ================================
  const handleSpikeClick = (point) => {
    navigate(
      `/logs?time=${encodeURIComponent(point.time)}&type=attack`
    );
  };

  return (
    <div
      className={`decision-card ${
        isUnderAttack ? "attack-mode" : ""
      }`}
    >
      <h2 className="decision-title">
        📈 Decision Trends{" "}
        {isUnderAttack && (
          <span className="attack-badge">⚠️ ATTACK DETECTED</span>
        )}
      </h2>

      {data.length === 0 ? (
        <p className="decision-empty">
          No activity data available
        </p>
      ) : (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />

            <XAxis dataKey="time" stroke="#a0a0a0" />
            <YAxis stroke="#a0a0a0" />

            <Tooltip
              contentStyle={{
                background: "#1e1e1e",
                border: "1px solid #2a2a2a",
                color: "#fff",
              }}
            />

            <Legend />

            {/* Allowed */}
            <Line
              type="monotone"
              dataKey="allowed"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
            />

            {/* Throttled */}
            <Line
              type="monotone"
              dataKey="throttled"
              stroke="#f59e0b"
              strokeWidth={2}
              dot={false}
            />

            {/* Blocked */}
            <Line
              type="monotone"
              dataKey="blocked"
              stroke="#ef4444"
              strokeWidth={2}
              dot={false}
            />

            {/* 🔥 Anomaly Points */}
            {anomalies.map((a, i) => (
              <ReferenceDot
                key={i}
                x={a.time}
                y={a.blocked}
                r={6}
                fill="#ef4444"
                stroke="#fff"
                onClick={() => handleSpikeClick(a)}
                style={{ cursor: "pointer" }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

export default DecisionTrendChart;