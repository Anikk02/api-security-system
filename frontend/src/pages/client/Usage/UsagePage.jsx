import React from "react";

import { useUsage } from "../../../hooks/client/useUsage";

// 🔹 Components
import UsageHeader from "../../../components/client/usage/UsageHeader/UsageHeader";
import TopUsers from "../../../components/client/usage/TopUsers/TopUsers";
import ApiKeyUsage from "../../../components/client/usage/ApiKeyUsage/ApiKeyUsage";
import PeakUsageTime from "../../../components/client/usage/PeakUsageTime/PeakUsageTime";
import UsageTrend from "../../../components/client/usage/UsageTrend/UsageTrend";

// 🔹 UI
import SkeletonCard from "../../../components/shared/Skeleton/SkeletonCard";

import "./UsagePage.css";

function UsagePage() {
  const { data, loading, error } = useUsage();

  // ============================
  // 🔄 Loading
  // ============================
  if (loading) {
    return (
      <div className="usage-container">
        <SkeletonCard />
        <SkeletonCard />
        <SkeletonCard />
      </div>
    );
  }

  // ============================
  // ❌ Error
  // ============================
  if (error && !data) {
    return (
      <div className="usage-container">
        <p className="error-text">Failed to load usage data</p>
      </div>
    );
  }

  return (
    <div className="usage-container animate-fade-in">
      {/* ============================
          🧠 Header
      ============================ */}
      <UsageHeader
        title="📊 API Usage Analytics"
        subtitle="Understand how your API is consumed by users and integrations"
      />

      {/* ============================
          📈 Usage Trend
      ============================ */}
      <h2 className="usage-section-title">📈 Usage Trend</h2>
      <UsageTrend trend={data?.trend} />

      {/* ============================
          ⏱ Peak Usage
      ============================ */}
      <h2 className="usage-section-title">⏱ Peak Usage</h2>
      <PeakUsageTime trend={data?.trend} />

      {/* ============================
          👥 + 🔑 Grid
      ============================ */}
      <div className="usage-grid">
        <div>
          <h2 className="usage-section-title">👥 Top Users</h2>
          <TopUsers users={data?.top_users} />
        </div>

        <div>
          <h2 className="usage-section-title">🔑 API Key Usage</h2>
          <ApiKeyUsage apiKeys={data?.api_keys} />
        </div>
      </div>
    </div>
  );
}

export default UsagePage;