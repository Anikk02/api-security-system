// frontend/src/background/hooks/usePackets.js
import { useState, useCallback, useRef } from 'react';

export const usePackets = () => {
  const [packets, setPackets] = useState([]);
  const maxPackets = 10;

  const generatePacket = useCallback(() => {
    const endpoints = ['/api/data', '/api/login', '/api/admin', '/api/user', '/api/transfer'];
    const ips = ['192.168.1.10', '172.16.0.5', '120.85.12.44', '203.0.113.25', '198.51.100.7'];
    const methods = ['GET', 'POST', 'PUT', 'DELETE'];
    const statuses = ['Allowed', 'Blocked', 'Throttled'];
    
    const packet = {
      id: Date.now() + Math.random(),
      endpoint: endpoints[Math.floor(Math.random() * endpoints.length)],
      ip: ips[Math.floor(Math.random() * ips.length)],
      method: methods[Math.floor(Math.random() * methods.length)],
      riskScore: Math.floor(Math.random() * 100),
      trustScore: Math.floor(Math.random() * 100),
      status: statuses[Math.floor(Math.random() * statuses.length)],
      timestamp: new Date().toLocaleTimeString()
    };

    setPackets(prev => {
      const newPackets = [...prev, packet];
      // Keep only last maxPackets
      return newPackets.slice(-maxPackets);
    });
    
    return packet;
  }, []);

  return { packets, generatePacket };
};