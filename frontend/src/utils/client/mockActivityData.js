const mockActivityData = {
  // 🔴 Timeline
  timeline: [
    {
      time: "10:15",
      event: "Suspicious token usage",
      description: "Multiple invalid JWT tokens detected",
      severity: "CRITICAL",
      ip: "192.168.1.100"
    },
    {
      time: "10:10",
      event: "Rate limit triggered",
      description: "Traffic spike exceeding threshold",
      severity: "MEDIUM",
      ip: "192.168.1.101"
    },
    {
      time: "10:05",
      event: "Multiple failed logins",
      description: "5 failed login attempts in 1 minute",
      severity: "HIGH",
      ip: "192.168.1.102"
    }
  ],

  // 📊 Endpoints
  endpoints: [
    {
      endpoint: "/login",
      percentage: 41.0,
      requests: 1200,
      blocked: 190,
      risk: "HIGH"
    },
    {
      endpoint: "/api/products",
      percentage: 25.0,
      requests: 800,
      blocked: 45,
      risk: "MEDIUM"
    },
    {
      endpoint: "/checkout",
      percentage: 20.0,
      requests: 600,
      blocked: 30,
      risk: "LOW"
    },
    {
      endpoint: "/profile",
      percentage: 10.0,
      requests: 300,
      blocked: 15,
      risk: "LOW"
    }
  ],

  // 📈 Trends
  trend: [
    { time: "10:15", allowed: 10, throttled: 0, blocked: 25 },
    { time: "10:10", allowed: 15, throttled: 0, blocked: 80 },
    { time: "10:05", allowed: 20, throttled: 0, blocked: 45 },
    { time: "10:00", allowed: 25, throttled: 0, blocked: 20 },
    { time: "09:55", allowed: 18, throttled: 0, blocked: 12 }
  ],

  // 🧠 Insights
  insights: {
    attackStatus: "under_attack",
    anomalyScore: 45.0,
    riskLevel: "HIGH"
  },

  // 📊 Metrics
  metrics: {
    totalRequests: 2900,
    blockedRequests: 280,
    throttledRequests: 0,
    successRate: 90.34
  },

  // 🛡️ NEW: Health Score (backend-aligned)
  healthScore: 90.34,

  // 🚨 Peak Attack
  peak: {
    time: "10:10",
    blocked: 80,
    endpoint: "/login",
    severity: "SEVERE"
  },

  // 🎯 NEW: Top Endpoint (backend-aligned)
  topEndpoint: {
    endpoint: "/login",
    requests: 1200,
    percentage: 41.0
  },

  // 🧠 Patterns
  patterns: [
    { endpoint: "/login", percentage: 45.0 },
    { endpoint: "/api/products", percentage: 25.0 },
    { endpoint: "/checkout", percentage: 20.0 },
    { endpoint: "/profile", percentage: 10.0 }
  ],

  // 🔗 SPIKE CORRELATIONS
  correlations: [
    {
      peak_time: "10:10",
      blocked: 80,
      target: "/login"
    },
    {
      peak_time: "09:55",
      blocked: 28,
      target: "/api/products"
    },
    {
      peak_time: "10:05",
      blocked: 45,
      target: "/login"
    }
  ]
};

export default mockActivityData;