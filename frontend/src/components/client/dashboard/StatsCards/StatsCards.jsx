// src/components/client/dashboard/StatsCards/StatsCards.jsx
import React from 'react';
import './StatsCards.css';
import { TrendingUp, TrendingDown, Minus, Activity, AlertTriangle, Users, Shield } from 'lucide-react';

const StatsCards = ({ stats }) => {
  if (!stats) return null;

  const {
    requestsPerSecond = 0,
    requestsTrend = 0,
    violationsDetected = 0,
    violationsTrend = 0,
    suspiciousSessions = 0,
    sessionsTrend = 0,
    avgRiskScore = 0,
    riskTrend = 0,
    trafficComposition = { normal: 0, suspicious: 0, high_risk: 0 }
  } = stats;

  const getTrendIcon = (trend) => {
    if (trend > 0) return <TrendingUp className="trend-up" size={16} />;
    if (trend < 0) return <TrendingDown className="trend-down" size={16} />;
    return <Minus className="trend-neutral" size={16} />;
  };

  const getTrendColor = (trend) => {
    if (trend > 0) return 'trend-up';
    if (trend < 0) return 'trend-down';
    return 'trend-neutral';
  };

  const statsData = [
    {
      label: 'Requests / sec',
      value: requestsPerSecond,
      trend: requestsTrend,
      subValue: `${trafficComposition.high_risk || 0}% high risk`,
      icon: <Activity size={20} className="stat-icon" />
    },
    {
      label: 'Violations / min',
      value: violationsDetected,
      trend: violationsTrend,
      subValue: `${trafficComposition.suspicious || 0}% suspicious`,
      icon: <AlertTriangle size={20} className="stat-icon" />
    },
    {
      label: 'Suspicious Sessions',
      value: suspiciousSessions,
      trend: sessionsTrend,
      subValue: `${trafficComposition.normal || 0}% normal traffic`,
      icon: <Users size={20} className="stat-icon" />
    },
    {
      label: 'Avg Risk Score',
      value: avgRiskScore.toFixed(2),
      trend: riskTrend,
      subValue: `${riskTrend > 0 ? '+' : ''}${riskTrend}% vs last min`,
      icon: <Shield size={20} className="stat-icon" />
    }
  ];

  return (
    <div className="stats-container">
      {statsData.map((stat, index) => (
        <div key={index} className="stat-card">
          <div className="stat-header">
            <div className="stat-label-wrapper">
              {stat.icon}
              <span className="stat-label">{stat.label}</span>
            </div>
            <span className={`trend-value ${getTrendColor(stat.trend)}`}>
              {getTrendIcon(stat.trend)}
              {stat.trend > 0 ? '+' : ''}{stat.trend}%
            </span>
          </div>
          <div className="stat-value">{stat.value}</div>
          <div className="stat-sub-value">{stat.subValue}</div>
        </div>
      ))}
    </div>
  );
};

export default StatsCards;