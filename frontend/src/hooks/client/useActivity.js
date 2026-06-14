import { useFetch } from "./useFetch";
import { useWebSocket } from "./useWebSocket";
import { activityService } from "../../services/client/activityService";
import { useEffect, useState } from "react";

export const useActivity = () => {
  // 🔹 Initial API load
  const { data: initialData, loading, error } = useFetch(
    activityService.getActivity
  );

  // 🔹 WebSocket live updates
  const { data: wsData } = useWebSocket([
    "activity_trend",
    "activity_timeline",
    "activity_endpoints"
  ]);

  // 🔹 Combined state
  const [data, setData] = useState({
    timeline: [],
    endpoints: [],
    trend: [],
  });

  // ============================
  // 🧠 Merge API → Base state
  // ============================
  useEffect(() => {
    if (initialData) {
      setData({
        timeline: initialData.timeline || [],
        endpoints: initialData.endpoints || [],
        trend: initialData.trend || [],
      });
    }
  }, [initialData]);

  // ============================
  // ⚡ Merge WebSocket updates
  // ============================
  useEffect(() => {
    if (!wsData) return;

    setData((prev) => ({
      timeline: wsData.activity_timeline || prev.timeline,
      endpoints: wsData.activity_endpoints || prev.endpoints,
      trend: wsData.activity_trend
        ? [...prev.trend, wsData.activity_trend].slice(-20)
        : prev.trend,
    }));
  }, [wsData]);

  return { data, loading, error: error && !initialData };
};