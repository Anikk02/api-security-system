import React from "react";

import ThreatTimeline from "../../../components/client/activity/ThreatTimeline/ThreatTimeline";
import EndpointDistribution from "../../../components/client/activity/EndpointDistribution/EndpointDistribution";
import DecisionTrendChart from "../../../components/client/activity/DecisionTrendChart/DecisionTrendChart";

import SkeletonCard from "../../../components/shared/Skeleton/SkeletonCard";
import { useActivity } from "../../../hooks/client/useActivity";

import "./ActivityPage.css";

function ActivityPage() {
  const { data, loading, error } = useActivity();

  // 🔄 Loading
  if (loading) {
    return (
      <div className="activity-container">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  // ❌ Error (only if NO data)
  if (error && !data) {
    return (
      <div className="activity-container">
        <p className="error-text">Failed to load activity data</p>
      </div>
    );
  }

  return (
    <div className="activity-container animate-fade-in">
      <h1 className="activity-title">📊 Activity Intelligence</h1>

      {/* 📈 Trend */}
      <DecisionTrendChart initialData={data?.trend || []} />

      {/* 🔥 Bottom */}
      <div className="activity-grid">
        <ThreatTimeline events={data?.timeline || []} />
        <EndpointDistribution data={data?.endpoints || []} />
      </div>
    </div>
  );
}

export default ActivityPage;