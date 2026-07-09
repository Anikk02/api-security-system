import React from "react";
import { useActivity } from "../../../hooks/client/useActivity";
import DecisionTrendChart from "../../../components/client/activity/charts/DecisionTrendChart/DecisionTrendChart";
import EndpointDistribution from "../../../components/client/activity/charts/EndpointDistribution/EndpointDistribution";
import ThreatTimeline from "../../../components/client/activity/charts/ThreatTimeline/ThreatTimeline";
import AttackStatusBanner from "../../../components/client/activity/insights/AttackStatusBanner/AttackStatusBanner";
import RiskIndicator from "../../../components/client/activity/insights/RiskIndicator/RiskIndicator";
import TopEndpointCard from "../../../components/client/activity/widgets/TopEndpointCard/TopEndpointCard";
import PeakAttackCard from "../../../components/client/activity/widgets/PeakAttackCard/PeakAttackCard";
import SystemHealthCard from "../../../components/client/activity/widgets/SystemHealthCard/SystemHealthCard";
import AttackPatterns from "../../../components/client/activity/patterns/AttackPatterns/AttackPatterns";
import SpikeCorrelation from "../../../components/client/activity/patterns/SpikeCorrelation/SpikeCorrelation";
import SkeletonCard from "../../../components/shared/Skeleton/SkeletonCard";
import { Activity } from "lucide-react";
import "./ActivityPage.css";

function ActivityPage() {
  const { data, loading, error } = useActivity();

  if (loading) {
    return (
      <div className="activity-container">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="activity-container">
        <p className="error-text">
          <Activity size={20} />
          Failed to load activity data
        </p>
      </div>
    );
  }

  const trend = data?.trend || [];
  const endpoints = data?.endpoints || [];
  const timeline = data?.timeline || [];

  return (
    <div className="activity-container animate-fade-in">
      {/* Header */}
      <div className="activity-header">
        <h1>Activity Intelligence</h1>
        <p>Real-time API behavior monitoring</p>
      </div>

      {/* Insights */}
      <div className="activity-insights">
        <div className="activity-card">
          <AttackStatusBanner trend={trend} />
        </div>
        <div className="activity-card">
          <RiskIndicator trend={trend} />
        </div>
      </div>

      {/* Summary Widgets */}
      <div className="activity-summary">
        <div className="activity-card">
          <h3 className="activity-card-title">System Health</h3>
          <SystemHealthCard trend={trend} />
        </div>
        <div className="activity-card">
          <h3 className="activity-card-title">Peak Attack</h3>
          <PeakAttackCard trend={trend} />
        </div>
        <div className="activity-card">
          <h3 className="activity-card-title">Top Endpoint</h3>
          <TopEndpointCard endpoints={endpoints} topEndpoint={data.topEndpoint} />
        </div>
      </div>

      {/* Trend Chart */}
      <DecisionTrendChart initialData={trend} />

      {/* Charts Grid */}
      <div className="activity-grid">
        <ThreatTimeline events={timeline} />
        <EndpointDistribution data={endpoints} />
      </div>

      {/* Patterns */}
      <div className="activity-patterns">
        <div className="activity-card">
          <h3 className="activity-card-title">Attack Patterns</h3>
          <AttackPatterns endpoints={endpoints} />
        </div>
        <div className="activity-card">
          <h3 className="activity-card-title">Spike Correlation</h3>
          <SpikeCorrelation trend={trend} endpoints={endpoints} />
        </div>
      </div>
    </div>
  );
}

export default ActivityPage;