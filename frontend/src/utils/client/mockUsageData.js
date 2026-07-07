export const mockUsageData = {
  // ============================
  // 👤 Top Users
  // ============================
  top_users: [
    { user_id: "user_123456", requests: 5200 },
    { user_id: "user_987654", requests: 4100 },
    { user_id: "user_456789", requests: 2900 },
    { user_id: "user_321654", requests: 1800 },
  ],

  // ============================
  // 🔑 API Key Usage
  // ============================
  api_keys: [
    { key: "abc123xyz789", requests: 12000 },
    { key: "def456uvw000", requests: 9000 },
    { key: "ghi789rst111", requests: 6500 },
  ],

  // ============================
  // 📦 Endpoint Usage
  // ============================
  endpoints: [
    { endpoint: "/orders", requests: 8000 },
    { endpoint: "/login", requests: 6000 },
    { endpoint: "/products", requests: 4500 },
    { endpoint: "/checkout", requests: 3000 },
    { endpoint: "/profile", requests: 1500 },
  ],

  // ============================
  // ⏱ Peak Usage (derived from trend)
  // ============================
  peak_time: {
    time: "12:00",
    requests: 950,
  },

  // ============================
  // 📈 Usage Trend (time-based)
  // ============================
  trend: [
    { time: "09:00", requests: 120 },
    { time: "10:00", requests: 300 },
    { time: "11:00", requests: 600 },
    { time: "12:00", requests: 950 }, // peak
    { time: "13:00", requests: 700 },
    { time: "14:00", requests: 500 },
    { time: "15:00", requests: 350 },
  ],
};