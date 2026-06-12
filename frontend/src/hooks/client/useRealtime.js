import { useState, useEffect, useRef, useCallback } from 'react';

export const useRealtime = (fetchFunction, interval = 5000, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);
  const isMounted = useRef(true);

  const fetchData = useCallback(async () => {
    try {
      const result = await fetchFunction();
      if (isMounted.current) {
        setData(result);
        setError(null);
        setLoading(false);
      }
    } catch (err) {
      if (isMounted.current) {
        setError(err);
        setLoading(false);
      }
    }
  }, [fetchFunction]);

  useEffect(() => {
    isMounted.current = true;
    
    fetchData();
    
    if (interval > 0 && !options.disabled) {
      intervalRef.current = setInterval(fetchData, interval);
    }
    
    return () => {
      isMounted.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchData, interval, options.disabled]);

  const refetch = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
};