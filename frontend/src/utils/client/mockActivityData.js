const mockActivityData = {
  // ============================
  // 🔥 Timeline (Threat events)
  // ============================
  timeline: [
    {
      time: "10:05",
      event: "Multiple failed logins",
      severity: "high",
      description: "Brute force attempt detected",
      ip: "192.168.1.10",
    },
    {
      time: "10:10",
      event: "Rate limit triggered",
      severity: "medium",
      description: "Too many requests from single IP",
      ip: "192.168.1.22",
    },
    {
      time: "10:15",
      event: "Suspicious token usage",
      severity: "critical",
      description: "JWT misuse detected",
      ip: "10.0.0.5",
    },
  ],

  // ============================
  // 🎯 Endpoint distribution
  // ============================
  endpoints: [
    {
      endpoint: "/login",
      percentage: 45,
      requests: 1200,
      blocked: 400,
      risk: "high",
    },
    {
      endpoint: "/api/products",
      percentage: 25,
      requests: 800,
      blocked: 50,
      risk: "low",
    },
    {
      endpoint: "/checkout",
      percentage: 20,
      requests: 600,
      blocked: 120,
      risk: "medium",
    },
    {
      endpoint: "/profile",
      percentage: 10,
      requests: 300,
      blocked: 20,
      risk: "low",
    },
  ],

  // ============================
  // 📈 Trend (Core chart)
  // ============================
  trend: [
    { time: "10:00", allowed: 100, throttled: 20, blocked: 10 },
    { time: "10:05", allowed: 90, throttled: 30, blocked: 25 },
    { time: "10:10", allowed: 70, throttled: 50, blocked: 80 }, // 🔥 spike
    { time: "10:15", allowed: 60, throttled: 40, blocked: 60 },
    { time: "10:20", allowed: 80, throttled: 20, blocked: 15 },
  ],

  // ============================
  // 🚨 Insights (NEW)
  // ============================
  insights: {
    attackStatus: "HIGH", // LOW | MEDIUM | HIGH | CRITICAL
    anomalyScore: 0.82,   // 0–1 scale
    riskLevel: "HIGH",
  },

  // ============================
  // 📊 System metrics (NEW)
  // ============================
  metrics: {
    totalRequests: 2900,
    blockedRequests: 605,
    throttledRequests: 160,
    successRate: 72, // %
  },

  // ============================
  // ⚡ Peak attack (NEW)
  // ============================
  peak: {
    time: "10:10",
    blocked: 80,
    endpoint: "/login",
  },

  // ============================
  // 🧠 Patterns (NEW)
  // ============================
  patterns: [
    {
      type: "Brute Force",
      endpoint: "/login",
      severity: "high",
      occurrences: 120,
    },
    {
      type: "Token Abuse",
      endpoint: "/api/auth",
      severity: "critical",
      occurrences: 60,
    },
  ],

  // ============================
  // 🔗 Correlation (NEW)
  // ============================
  correlations: [
    {
      spikeTime: "10:10",
      affectedEndpoints: ["/login", "/checkout"],
    },
  ],
};

export default mockActivityData;