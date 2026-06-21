import { useEffect, useState } from "react";
import { 
  getSettingsOverview,
  regenerateApiKey,
  updateProfile
 } from "../../services/client/settingsService";
import { mockSettingsData } from "../../utils/client/mockSettingsData";

export const useSettings = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSettings = async () => {
      try {
        const res = await getSettingsOverview();

        setData({
          profile: res?.profile || mockSettingsData.profile,
          api_key: res?.api_key || mockSettingsData.api_key,
        });

        setError(null);
      } catch (err) {
        console.warn("⚠️ Using mock settings data:", err.message);

        setData(mockSettingsData);
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  const regenerateKey = async () => {
    alert("🔑 API Key regenerated (mock)");
  };

  const updateProfile = async (email) => {
    alert(`👤 Profile updated to ${email} (mock)`);
  };

  return {
    data,
    loading,
    error,
    regenerateKey,
    updateProfile,
  };
};