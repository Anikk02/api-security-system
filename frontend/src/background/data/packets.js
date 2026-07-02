// frontend/src/background/data/packets.js
export const samplePackets = [
  {
    id: 1,
    endpoint: '/api/data',
    ip: '192.168.1.10',
    method: 'GET',
    riskScore: 23,
    trustScore: 87,
    status: 'Allowed',
    timestamp: '14:24:31'
  },
  {
    id: 2,
    endpoint: '/api/login',
    ip: '172.16.0.5',
    method: 'POST',
    riskScore: 45,
    trustScore: 65,
    status: 'Challenge',
    timestamp: '14:24:30'
  },
  {
    id: 3,
    endpoint: '/api/admin',
    ip: '120.85.12.44',
    method: 'GET',
    riskScore: 78,
    trustScore: 34,
    status: 'Blocked',
    timestamp: '14:24:29'
  }
];

export const generateRandomPacket = () => {
  const endpoints = ['/api/data', '/api/login', '/api/admin', '/api/user', '/api/transfer'];
  const ips = ['192.168.1.10', '172.16.0.5', '120.85.12.44', '203.0.113.25', '198.51.100.7'];
  const methods = ['GET', 'POST', 'PUT', 'DELETE'];
  const statuses = ['Allowed', 'Blocked', 'Throttled'];
  
  return {
    id: Date.now(),
    endpoint: endpoints[Math.floor(Math.random() * endpoints.length)],
    ip: ips[Math.floor(Math.random() * ips.length)],
    method: methods[Math.floor(Math.random() * methods.length)],
    riskScore: Math.floor(Math.random() * 100),
    trustScore: Math.floor(Math.random() * 100),
    status: statuses[Math.floor(Math.random() * statuses.length)],
    timestamp: new Date().toLocaleTimeString()
  };
};