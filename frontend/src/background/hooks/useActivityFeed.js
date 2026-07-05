// frontend/src/background/hooks/useActivityFeed.js
import { useState, useCallback } from 'react';

export const useActivityFeed = () => {
  const [activities, setActivities] = useState([]);

  const addActivity = useCallback((packet) => {
    setActivities(prev => [packet, ...prev].slice(0, 20));
  }, []);

  return { activities, addActivity };
};