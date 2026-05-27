import React from 'react';
import {
  LineChart,
  Line,
  Area,
  AreaChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import { CHART_CONFIG } from '../../utils/constants';
import './TrafficChart.css';

const TrafficChart = ({ data, title = 'Live Traffic Overview' }) => {
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="chart-tooltip">
          <p className="chart-tooltip__time">
            {new Date(label).toLocaleTimeString()}
          </p>
          {payload.map((entry, index) => (
            <p key={index} className="chart-tooltip__value" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="traffic-chart card">
      <h3 className="traffic-chart__title">{title}</h3>
      <div className="traffic-chart__container">
        <ResponsiveContainer width="100%" height={400}>
          <AreaChart data={data}>
            <defs>
              <linearGradient id="requestsGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="anomaliesGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
            <XAxis 
              dataKey="time" 
              tickFormatter={(time) => new Date(time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              stroke="#6b6b6b"
            />
            <YAxis stroke="#6b6b6b" />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Area
              type="monotone"
              dataKey="requests"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#requestsGradient)"
              name="Requests"
            />
            <Area
              type="monotone"
              dataKey="anomalies"
              stroke="#ef4444"
              strokeWidth={2}
              fill="url(#anomaliesGradient)"
              name="Anomalies"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default TrafficChart;