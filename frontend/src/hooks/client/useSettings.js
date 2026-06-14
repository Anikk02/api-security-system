import { useEffect, useState } from 'react';
import * as settingsService from '../../services/client/settingsService';

export const useSettings = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSettings = async () => {
    try {
      const res = await settingsService.getSettingsOverview();
      setData(res.data);
    } catch (err) {
      console.error('Failed to fetch settings', err);
    } finally {
      setLoading(false);
    }
  };

  const regenerateKey = async () => {
    const res = await settingsService.regenerateApiKey();
    return res.data;
  };

  const updateProfile = async (email) => {
    await settingsService.updateProfile({ email });
    await fetchSettings();
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  return { data, loading, regenerateKey, updateProfile };
};