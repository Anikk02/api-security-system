import React, { useState, useEffect, useCallback } from 'react';
import { Activity, AlertTriangle, Users, Zap } from 'lucide-react';
import StatCard from '../../components/StatCard/StatCard';
import TrafficChart from '../../components/TrafficChart/TrafficChart';
import DecisionTable from '../../components/DecisionTable/DecisionTable';
import ViolatorMap from '../../components/ViolatorMap/ViolatorMap';
import RiskChart from '../../components/RiskChart/RiskChart';
import { dashboardService } from '../../services/dashboardService';
import { useWebSocket } from '../../hooks/useWebSocket';
import toast from 'react-hot-toast';
import './Dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [trafficData, setTrafficData] = useState([]);
  const [users, setUsers] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [selectedViolator, setSelectedViolator] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // WebSocket for real-time updates
  const { data: wsData, isConnected } = useWebSocket(['new_alert', 'stats_update']);
  
  // Single function to load all dashboard data
  const loadDashboardData = useCallback(async () => {
    try {
      // Load all data in parallel but with controlled concurrency
      const [statsData, traffic, suspiciousUsers, recentAlerts] = await Promise.all([
        dashboardService.getStats(),
        dashboardService.getTrafficData('15m'),
        dashboardService.getSuspiciousUsers(10),
        dashboardService.getRecentAlerts(5)
      ]);
      
      setStats(statsData);
      setTrafficData(traffic);
      setUsers(suspiciousUsers);
      setAlerts(recentAlerts);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);
  
  // Initial load
  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);
  
  // Polling every 15 seconds (reduced frequency)
  useEffect(() => {
    const interval = setInterval(() => {
      loadDashboardData();
    }, 15000); // 15 seconds instead of multiple intervals
    
    return () => clearInterval(interval);
  }, [loadDashboardData]);
  
  // Handle WebSocket updates (only for real-time pushes)
  useEffect(() => {
    if (wsData.stats_update) {
      setStats(prev => ({ ...prev, ...wsData.stats_update }));
    }
    
    if (wsData.new_alert) {
      // Add new alert to the list
      setAlerts(prev => [wsData.new_alert, ...prev].slice(0, 10));
      toast.error(`New alert: ${wsData.new_alert.type} from ${wsData.new_alert.ip}`, {
        duration: 5000,
      });
      // Refresh data to keep everything in sync
      loadDashboardData();
    }
  }, [wsData, loadDashboardData]);
  
  const handleViolatorClick = (violator) => {
    setSelectedViolator(violator);
    toast.info(`Viewing details for ${violator.id}`, { duration: 3000 });
  };
  
  const statCards = stats ? [
    { title: 'Requests Per Second', value: stats.requestsPerSecond, trend: stats.requestsTrend, icon: Zap, color: 'info' },
    { title: 'Violations Detected', value: stats.violationsDetected, trend: stats.violationsTrend, icon: AlertTriangle, color: 'danger' },
    { title: 'Suspicious Sessions', value: stats.suspiciousSessions, trend: stats.sessionsTrend, icon: Users, color: 'warning' },
  ] : [];
  
  if (loading) {
    return (
      <div className="dashboard">
        <div className="dashboard__header">
          <h1 className="dashboard__title">Security Dashboard</h1>
          <div className="dashboard__status dashboard__status--connected">
            <div className="dashboard__status-dot" />
            <span>Loading...</span>
          </div>
        </div>
        <div className="dashboard-loading">
          <div className="dashboard-loading__spinner"></div>
          <p>Loading security data...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="dashboard">
      <div className="dashboard__header">
        <h1 className="dashboard__title">Security Dashboard</h1>
        <div className={`dashboard__status ${isConnected ? 'dashboard__status--connected' : 'dashboard__status--disconnected'}`}>
          <div className="dashboard__status-dot" />
          <span>{isConnected ? 'Live Monitoring Active' : 'Connecting...'}</span>
        </div>
      </div>
      
      <div className="dashboard__stats">
        {statCards.map((card, index) => (
          <StatCard key={index} {...card} />
        ))}
      </div>
      
      {/* Live Violator Map */}
      <ViolatorMap 
        violators={users}
        onViolatorClick={handleViolatorClick}
      />
      
      <div className="dashboard__charts">
        <TrafficChart data={trafficData} />
      </div>
      
      <div className="dashboard__risk-charts">
        <RiskChart type="pie" title="Risk Distribution" height={350} />
        <RiskChart type="radar" title="Risk Metrics Analysis" height={350} />
      </div>
      
      <div className="dashboard__table">
        <DecisionTable data={users} title="Suspicious Users" />
      </div>
    </div>
  );
};

export default Dashboard;