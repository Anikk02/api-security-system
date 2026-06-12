import { useEffect, useState, useCallback } from 'react';
import websocketService from '../../services/client/websocketService';

export const useWebSocket = (eventTypes = []) => {
  const [data, setData] = useState({});
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    const handleConnected = () => setIsConnected(true);
    const handleDisconnected = () => setIsConnected(false);
    const handleError = (err) => setError(err);
    
    websocketService.on('connected', handleConnected);
    websocketService.on('disconnected', handleDisconnected);
    websocketService.on('error', handleError);
    
    eventTypes.forEach(eventType => {
      const handler = (payload) => {
        setData(prev => ({ ...prev, [eventType]: payload }));
      };
      websocketService.on(eventType, handler);
    });
    
    websocketService.connect();
    
    return () => {
      websocketService.off('connected', handleConnected);
      websocketService.off('disconnected', handleDisconnected);
      websocketService.off('error', handleError);
      eventTypes.forEach(eventType => {
        websocketService.off(eventType, () => {});
      });
      websocketService.disconnect();
    };
  }, [eventTypes.join(',')]);

  const send = useCallback((type, payload) => {
    websocketService.send(type, payload);
  }, []);

  return { data, isConnected, error, send };
};