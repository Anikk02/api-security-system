import React, { useState, useEffect } from 'react';
import { Activity, AlertTriangle, Users, Zap } from 'lucide-react';
import StatCard from '../../components/StatCard/StatCard';
import TrafficChart from '../../components/TrafficChart/TrafficChart';
import RiskChart from '../../components/RiskChart/RiskChart';
import DecisionTable from '../../components/DecisionTable/DecisionTable';
import ViolatorMap from '../../components/ViolatorMap/ViolatorMap';
import { dashboardService } from '../../services/dashboardService';
import { useRealtime } from '../../hooks/useRealtime';
import { useWebSocket } from '../../hooks/useWebSocket';
import toast from 'react-hot-toast';
import './Dashboard.css';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [trafficData, setTrafficData] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedViolator, setSelectedViolator] = useState(null);
  
  // WebSocket for real-time updates
  const { data: wsData, isConnected } = useWebSocket(['new_alert', 'stats_update', 'new_violator']);
  
  // Fetch initial data
  const { data: initialStats } = useRealtime(dashboardService.getStats, 5000);
  const { data: initialTraffic } = useRealtime(dashboardService.getTrafficData, 10000);
  const { data: initialUsers } = useRealtime(dashboardService.getSuspiciousUsers, 30000);
  
  useEffect(() => {
    if (initialStats) setStats(initialStats);
    if (initialTraffic) setTrafficData(initialTraffic);
    if (initialUsers) setUsers(initialUsers);
  }, [initialStats, initialTraffic, initialUsers]);
  
  // Handle WebSocket updates
  useEffect(() => {
    if (wsData.stats_update) {
      setStats(prev => ({ ...prev, ...wsData.stats_update }));
      toast.success('Stats updated in real-time');
    }
    
    if (wsData.new_alert) {
      toast.error(`New alert: ${wsData.new_alert.type} from ${wsData.new_alert.ip}`, {
        duration: 5000,
      });
    }
    
    if (wsData.new_violator) {
      toast(`New violator detected in ${wsData.new_violator.location}`, {
        icon: '🌍',
        duration: 4000,
      });
    }
  }, [wsData]);
  
  const handleViolatorClick = (violator) => {
    setSelectedViolator(violator);
    toast.info(`Viewing details for ${violator.id}`, { duration: 3000 });
  };
  
  const statCards = stats ? [
    { title: 'Requests Per Second', value: stats.requestsPerSecond, trend: stats.requestsTrend, icon: Zap, color: 'info' },
    { title: 'Violations Detected', value: stats.violationsDetected, trend: stats.violationsTrend, icon: AlertTriangle, color: 'danger' },
    { title: 'Suspicious Sessions', value: stats.suspiciousSessions, trend: stats.sessionsTrend, icon: Users, color: 'warning' },
  ] : [];
  
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
      
      <div className="dashboard__table">
        <DecisionTable data={users} />
      </div>
      <div className="dashboard__risk-charts">
        <RiskChart type="pie" title="Risk Distribution by Category" height={350} />
        <RiskChart type="radar" title="Risk Metrics Analysis" height={350} />
      </div>
    </div>
  );
};

export default Dashboard;