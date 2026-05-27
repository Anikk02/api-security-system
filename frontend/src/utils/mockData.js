export const generateMockTrafficData = () => {
  const now = Date.now();
  return Array.from({ length: 15 }, (_, i) => ({
    time: now - (14 - i) * 60000,
    requests: Math.floor(Math.random() * 100) + 20,
    anomalies: Math.floor(Math.random() * 30),
    blocked: Math.floor(Math.random() * 15)
  }));
};

export const generateMockSuspiciousUsers = () => [
  { id: 'Bot-10554096', violations: 25, threatScore: 0.88, status: 'Scanning', ip: '192.168.1.1', lastSeen: new Date() },
  { id: 'Anon-44939162', violations: 18, threatScore: 0.92, status: 'Rapid Hits', ip: '192.168.1.2', lastSeen: new Date() },
  { id: 'user-johndoe@example.com', violations: 12, threatScore: 0.79, status: 'OS Scanning', ip: '192.168.1.3', lastSeen: new Date() },
  { id: 'Guest-34915749', violations: 10, threatScore: 0.76, status: 'Scanning', ip: '192.168.1.4', lastSeen: new Date() },
  { id: 'user-bob@example.com', violations: 9, threatScore: 0.72, status: 'Pattern Match', ip: '192.168.1.5', lastSeen: new Date() }
];

export const generateMockAlerts = () => [
  { id: 1, ip: '192.168.1.100', score: 0.95, type: 'DDoS Attack', timestamp: new Date() },
  { id: 2, ip: '192.168.1.101', score: 0.88, type: 'SQL Injection', timestamp: new Date() },
  { id: 3, ip: '192.168.1.102', score: 0.76, type: 'Rate Limit Exceeded', timestamp: new Date() },
  { id: 4, ip: '192.168.1.103', score: 0.71, type: 'Suspicious Pattern', timestamp: new Date() }
];

export const generateMockStats = () => ({
  requestsPerSecond: 2.7,
  requestsTrend: 0.22,
  violationsDetected: 128,
  violationsTrend: 56,
  suspiciousSessions: 33,
  sessionsTrend: 33,
  trafficComposition: {
    normal: 0.54,
    bots: 0.32,
    suspicious: 0.14
  }
});