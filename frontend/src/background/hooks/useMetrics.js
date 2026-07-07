// frontend/src/background/hooks/useMetrics.js
import { useState, useCallback } from 'react';

export const useMetrics = () => {
  const [metrics, setMetrics] = useState({
    requests: 152231,
    blocked: 283,
    threats: 51
  });

  const updateMetrics = useCallback((packet) => {
    setMetrics(prev => ({
      requests: prev.requests + 1,
      blocked: packet.status === 'Blocked' ? prev.blocked + 1 : prev.blocked,
      threats: packet.riskScore > 70 ? prev.threats + 1 : prev.threats
    }));
  }, []);

  return { metrics, updateMetrics };
};