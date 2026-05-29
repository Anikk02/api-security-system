import React, { useState, useEffect } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  RadarChart,
  Radar,
  ComposedChart,
  Line,
  Area
} from 'recharts';
import { TrendingUp, TrendingDown, Shield, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { CHART_CONFIG, RISK_LEVELS, RISK_COLORS } from '../../utils/constants';
import { dashboardService } from '../../services/dashboardService';
import './RiskChart.css';

const RiskChart = ({ 
  type = 'pie', 
  title = 'Risk Distribution',
  height = 300,
  showLegend = true,
  showTooltip = true,
  animated = true,
  refreshInterval = 30000  // Auto-refresh every 30 seconds
}) => {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [riskMetrics, setRiskMetrics] = useState(null);

  // Fetch real data from backend
  const fetchRiskData = async () => {
    try {
      setLoading(true);
      
      // Fetch suspicious users to calculate risk distribution
      const suspiciousUsers = await dashboardService.getSuspiciousUsers(50);
      
      // Calculate risk distribution from real data
      const riskCounts = {
        low: 0,
        medium: 0,
        high: 0,
        critical: 0
      };
      
      suspiciousUsers.forEach(user => {
        const score = user.threatScore || 0;
        if (score >= 0.9) {
          riskCounts.critical++;
        } else if (score >= 0.7) {
          riskCounts.high++;
        } else if (score >= 0.4) {
          riskCounts.medium++;
        } else {
          riskCounts.low++;
        }
      });
      
      const total = suspiciousUsers.length || 1; // Avoid division by zero
      
      // Build real chart data
      const realChartData = [
        { 
          name: 'Low Risk', 
          value: Math.round((riskCounts.low / total) * 100),
          color: RISK_COLORS[RISK_LEVELS.LOW], 
          count: riskCounts.low,
          percentage: Math.round((riskCounts.low / total) * 100)
        },
        { 
          name: 'Medium Risk', 
          value: Math.round((riskCounts.medium / total) * 100),
          color: RISK_COLORS[RISK_LEVELS.MEDIUM], 
          count: riskCounts.medium,
          percentage: Math.round((riskCounts.medium / total) * 100)
        },
        { 
          name: 'High Risk', 
          value: Math.round((riskCounts.high / total) * 100),
          color: RISK_COLORS[RISK_LEVELS.HIGH], 
          count: riskCounts.high,
          percentage: Math.round((riskCounts.high / total) * 100)
        },
        { 
          name: 'Critical', 
          value: Math.round((riskCounts.critical / total) * 100),
          color: RISK_COLORS[RISK_LEVELS.CRITICAL], 
          count: riskCounts.critical,
          percentage: Math.round((riskCounts.critical / total) * 100)
        }
      ];
      
      setChartData(realChartData);
      setRiskMetrics({
        totalUsers: suspiciousUsers.length,
        avgRiskScore: suspiciousUsers.reduce((sum, u) => sum + (u.threatScore || 0), 0) / total,
        ...riskCounts
      });
      setError(null);
      
    } catch (err) {
      console.error('Failed to fetch risk data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchRiskData();
  }, []);

  // Auto-refresh
  useEffect(() => {
    const interval = setInterval(() => {
      fetchRiskData();
    }, refreshInterval);
    
    return () => clearInterval(interval);
  }, [refreshInterval]);

  // Calculate time series from decision logs (mock for now, can be enhanced)
  const getTimeSeriesData = () => {
    // This would ideally come from /api/dashboard/traffic endpoint
    // For now, use data from the traffic chart or return empty
    return [
      { time: '00:00', low: 45, medium: 22, high: 8, critical: 3, total: 78 },
      { time: '02:00', low: 38, medium: 18, high: 6, critical: 2, total: 64 },
      { time: '04:00', low: 32, medium: 15, high: 5, critical: 2, total: 54 },
      { time: '06:00', low: 48, medium: 25, high: 10, critical: 4, total: 87 },
      { time: '08:00', low: 78, medium: 42, high: 18, critical: 8, total: 146 },
      { time: '10:00', low: 95, medium: 58, high: 28, critical: 12, total: 193 },
      { time: '12:00', low: 88, medium: 52, high: 24, critical: 10, total: 174 },
      { time: '14:00', low: 92, medium: 55, high: 26, critical: 11, total: 184 },
      { time: '16:00', low: 85, medium: 48, high: 22, critical: 9, total: 164 },
      { time: '18:00', low: 72, medium: 38, high: 16, critical: 7, total: 133 },
      { time: '20:00', low: 62, medium: 32, high: 14, critical: 6, total: 114 },
      { time: '22:00', low: 52, medium: 26, high: 10, critical: 4, total: 92 }
    ];
  };

  // Calculate radar data from real metrics
  const getRadarData = () => {
    if (!riskMetrics) return [];
    
    return [
      { subject: 'Low Risk Users', value: riskMetrics.low || 0, fullMark: 100 },
      { subject: 'Medium Risk', value: riskMetrics.medium || 0, fullMark: 100 },
      { subject: 'High Risk', value: riskMetrics.high || 0, fullMark: 100 },
      { subject: 'Critical', value: riskMetrics.critical || 0, fullMark: 100 },
      { subject: 'Avg Risk Score', value: Math.round((riskMetrics.avgRiskScore || 0) * 100), fullMark: 100 },
      { subject: 'Total Threats', value: (riskMetrics.high || 0) + (riskMetrics.critical || 0), fullMark: 100 }
    ];
  };

  // Get radial bar data from real chart data
  const getRadialData = () => {
    return chartData.map(item => ({
      name: item.name,
      value: item.value,
      fill: item.color
    }));
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="risk-chart__tooltip">
          <p className="risk-chart__tooltip-title">{payload[0].payload.name || label}</p>
          {payload.map((entry, index) => (
            <div key={index} className="risk-chart__tooltip-item">
              <span 
                className="risk-chart__tooltip-color" 
                style={{ backgroundColor: entry.color || entry.payload.color }}
              />
              <span className="risk-chart__tooltip-label">{entry.name || 'Value'}:</span>
              <span className="risk-chart__tooltip-value">
                {entry.value}
                {entry.payload.percentage && '%'}
                {entry.payload.count && ` (${entry.payload.count} users)`}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  const renderPieChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          labelLine={false}
          label={showLegend ? undefined : (entry) => `${entry.name}: ${entry.value}%`}
          outerRadius={height * 0.35}
          innerRadius={height * 0.2}
          paddingAngle={2}
          dataKey="value"
          animationBegin={animated ? 0 : -1}
          animationDuration={animated ? CHART_CONFIG.ANIMATION_DURATION : 0}
        >
          {chartData.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={entry.color || entry.fill}
              stroke="var(--bg-card)"
              strokeWidth={2}
            />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        {showLegend && (
          <Legend 
            verticalAlign="bottom" 
            height={36}
            formatter={(value, entry) => (
              <span style={{ color: 'var(--text-secondary)' }}>{value}</span>
            )}
          />
        )}
      </PieChart>
    </ResponsiveContainer>
  );

  const renderBarChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={getTimeSeriesData()}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
        <XAxis dataKey="time" stroke="var(--text-secondary)" />
        <YAxis stroke="var(--text-secondary)" />
        <Tooltip content={<CustomTooltip />} />
        {showLegend && <Legend />}
        <Bar dataKey="low" stackId="a" fill={RISK_COLORS[RISK_LEVELS.LOW]} name="Low Risk" />
        <Bar dataKey="medium" stackId="a" fill={RISK_COLORS[RISK_LEVELS.MEDIUM]} name="Medium Risk" />
        <Bar dataKey="high" stackId="a" fill={RISK_COLORS[RISK_LEVELS.HIGH]} name="High Risk" />
        <Bar dataKey="critical" stackId="a" fill={RISK_COLORS[RISK_LEVELS.CRITICAL]} name="Critical" />
      </BarChart>
    </ResponsiveContainer>
  );

  const renderRadialBarChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <RadialBarChart 
        cx="50%" 
        cy="50%" 
        innerRadius="20%" 
        outerRadius="80%" 
        barSize={20} 
        data={getRadialData()}
        startAngle={180}
        endAngle={0}
      >
        <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
        <RadialBar
          minAngle={15}
          label={{ fill: 'var(--text-primary)', position: 'insideStart' }}
          background
          clockWise
          dataKey="value"
        />
        <Legend 
          iconSize={10} 
          layout="vertical" 
          verticalAlign="middle" 
          align="right"
          formatter={(value) => <span style={{ color: 'var(--text-secondary)' }}>{value}</span>}
        />
        <Tooltip content={<CustomTooltip />} />
      </RadialBarChart>
    </ResponsiveContainer>
  );

  const renderRadarChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart cx="50%" cy="50%" outerRadius="80%" data={getRadarData()}>
        <PolarGrid stroke="var(--border-color)" />
        <PolarAngleAxis dataKey="subject" stroke="var(--text-secondary)" tick={{ fill: 'var(--text-secondary)' }} />
        <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="var(--text-secondary)" />
        <Radar
          name="Risk Metrics"
          dataKey="value"
          stroke="var(--accent-info)"
          fill="var(--accent-info)"
          fillOpacity={0.3}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
      </RadarChart>
    </ResponsiveContainer>
  );

  const renderComposedChart = () => (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={getTimeSeriesData()}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
        <XAxis dataKey="time" stroke="var(--text-secondary)" />
        <YAxis stroke="var(--text-secondary)" />
        <Tooltip content={<CustomTooltip />} />
        <Legend />
        <Area type="monotone" dataKey="total" fill="var(--accent-info)" fillOpacity={0.2} stroke="var(--accent-info)" name="Total Requests" />
        <Line type="monotone" dataKey="high" stroke={RISK_COLORS[RISK_LEVELS.HIGH]} strokeWidth={2} name="High Risk" dot={false} />
        <Line type="monotone" dataKey="critical" stroke={RISK_COLORS[RISK_LEVELS.CRITICAL]} strokeWidth={2} name="Critical" dot={false} />
      </ComposedChart>
    </ResponsiveContainer>
  );

  const renderStatsCards = () => (
    <div className="risk-chart__stats">
      {chartData.map((item, index) => (
        <div key={index} className="risk-chart__stat-card">
          <div className="risk-chart__stat-header">
            <div 
              className="risk-chart__stat-icon"
              style={{ 
                background: `${item.color}20`,
                color: item.color
              }}
            >
              {item.name === 'Low Risk' && <CheckCircle size={20} />}
              {item.name === 'Medium Risk' && <Clock size={20} />}
              {(item.name === 'High Risk' || item.name === 'Critical') && <AlertTriangle size={20} />}
            </div>
            <span className="risk-chart__stat-name">{item.name}</span>
          </div>
          <div className="risk-chart__stat-value">{item.value}%</div>
          <div className="risk-chart__stat-bar">
            <div 
              className="risk-chart__stat-bar-fill"
              style={{ 
                width: `${item.value}%`,
                backgroundColor: item.color
              }}
            />
          </div>
          {item.count !== undefined && (
            <div className="risk-chart__stat-count">{item.count} users</div>
          )}
        </div>
      ))}
    </div>
  );

  const renderChart = () => {
    if (loading) {
      return (
        <div className="risk-chart__loading">
          <div className="risk-chart__loading-spinner" />
          <p>Loading risk data...</p>
        </div>
      );
    }
    
    if (error) {
      return (
        <div className="risk-chart__error">
          <AlertTriangle size={24} />
          <p>Failed to load risk data</p>
          <button onClick={fetchRiskData}>Retry</button>
        </div>
      );
    }
    
    switch(type) {
      case 'pie':
        return renderPieChart();
      case 'bar':
        return renderBarChart();
      case 'radial':
        return renderRadialBarChart();
      case 'radar':
        return renderRadarChart();
      case 'composed':
        return renderComposedChart();
      case 'stats':
        return renderStatsCards();
      default:
        return renderPieChart();
    }
  };

  // Calculate trend from real data
  const getHighRiskPercentage = () => {
    const highRiskItem = chartData.find(d => d.name === 'High Risk');
    return highRiskItem?.value || 0;
  };

  return (
    <div className="risk-chart card">
      <div className="risk-chart__header">
        <div className="risk-chart__title-section">
          <Shield size={20} className="risk-chart__header-icon" />
          <h3 className="risk-chart__title">{title}</h3>
        </div>
        <div className="risk-chart__metrics">
          <div className="risk-chart__metric">
            <TrendingUp size={14} />
            <span>High Risk: {getHighRiskPercentage()}%</span>
          </div>
          <div className="risk-chart__metric">
            <AlertTriangle size={14} />
            <span>Critical: {chartData.find(d => d.name === 'Critical')?.value || 0}%</span>
          </div>
        </div>
      </div>
      <div className="risk-chart__content">
        {renderChart()}
      </div>
    </div>
  );
};

export default RiskChart;