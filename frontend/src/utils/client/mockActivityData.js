export const mockActivityData = {
  timeline: [
    {
      time: "10:05",
      event: "Multiple failed logins",
      severity: "high",
      description: "Brute force attempt detected",
    },
    {
      time: "10:10",
      event: "Rate limit triggered",
      severity: "medium",
      description: "Too many requests from single IP",
    },
    {
      time: "10:15",
      event: "Suspicious token usage",
      severity: "high",
      description: "JWT misuse detected",
    },
  ],

  endpoints: [
    { endpoint: "/login", percentage: 45, requests: 1200 },
    { endpoint: "/api/products", percentage: 25, requests: 800 },
    { endpoint: "/checkout", percentage: 20, requests: 600 },
    { endpoint: "/profile", percentage: 10, requests: 300 },
  ],

  trend: [
    { time: "10:00", allowed: 100, throttled: 20, blocked: 10 },
    { time: "10:05", allowed: 90, throttled: 30, blocked: 25 },
    { time: "10:10", allowed: 70, throttled: 50, blocked: 80 }, // spike
    { time: "10:15", allowed: 60, throttled: 40, blocked: 60 },
  ],
};