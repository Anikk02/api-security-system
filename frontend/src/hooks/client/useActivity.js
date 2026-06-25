import { useFetch } from "./useFetch";
import { activityService } from "../../services/client/activityService";
import { useEffect, useState } from "react";

export const useActivity = () => {
  // 🔹 Initial API load (returns all activity data)
  const { data: initialData, loading, error } = useFetch(
    activityService.getActivity
  );

  // 🔹 Combined state
  const [data, setData] = useState({
    timeline: [],
    endpoints: [],
    trend: [],
    insights: null,
    metrics: null,
    peak: null,
    patterns: [],
    correlations: [],  // 🔗 SPIKE CORRELATIONS - KEY INSIGHT
    topEndpoint: null,
    healthScore: null,
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
        insights: initialData.insights || null,
        metrics: initialData.metrics || null,
        peak: initialData.peak || null,
        patterns: initialData.patterns || [],
        correlations: initialData.correlations || [],  // 🔗 SPIKE CORRELATIONS
        topEndpoint: initialData.topEndpoint || null,
        healthScore: typeof initialData.healthScore === 'number' ? initialData.healthScore : null,
      });
    }
  }, [initialData]);

  // ============================
  // 🔄 Auto-refresh every 10 minutes
  // ============================
  useEffect(() => {
    const refreshInterval = setInterval(() => {
      activityService.getActivity().then((newData) => {
        if (newData) {
          setData({
            timeline: newData.timeline || [],
            endpoints: newData.endpoints || [],
            trend: newData.trend || [],
            insights: newData.insights || null,
            metrics: newData.metrics || null,
            peak: newData.peak || null,
            patterns: newData.patterns || [],
            correlations: newData.correlations || [],
            topEndpoint: newData.topEndpoint || null,
            healthScore: typeof newData.healthScore === 'number' ? newData.healthScore : null,
          });
        }
      });
    }, 600000); // 10 minutes (600,000 ms)

    return () => clearInterval(refreshInterval);
  }, []);

  return { data, loading, error: error && !initialData };
};