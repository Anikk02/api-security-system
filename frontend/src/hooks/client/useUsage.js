import { useEffect, useState } from "react";
import { usageService } from "../../services/client/usageService";
import { mockUsageData } from "../../utils/client/mockUsageData";

export const useUsage = () => {
  const [data, setData] = useState({
    top_users: [],
    api_keys: [],
    endpoints: [],
    trend: [],
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchUsage = async () => {
      try {
        const res = await usageService.getUsage();

        // ✅ Use API data if available
        if (res) {
          setData({
            top_users: res.top_users || mockUsageData.top_users,
            api_keys: res.api_keys || mockUsageData.api_keys,
            endpoints: res.endpoints || mockUsageData.endpoints,
            trend: res.trend || mockUsageData.trend,
          });
        } else {
          throw new Error("Empty response");
        }

        setError(null);
      } catch (err) {
        console.warn("⚠️ Using mock usage data:", err.message);

        // ✅ Full fallback
        setData({
          top_users: mockUsageData.top_users,
          api_keys: mockUsageData.api_keys,
          endpoints: mockUsageData.endpoints,
          trend: mockUsageData.trend,
        });

        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchUsage();
  }, []);

  return { data, loading, error };
};