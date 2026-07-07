import axios from "axios";

// 🔹 Create axios instance (recommended)
const api = axios.create({
  baseURL: "/api", // change to full URL if needed
  timeout: 5000,
});

export const usageService = {
  getUsage: async () => {
    try {
      const res = await api.get("/usage");

      // ✅ Basic structure validation
      if (!res.data) {
        throw new Error("Invalid API response");
      }

      return res.data;
    } catch (error) {
      console.error("Usage API error:", error.message);

      // ❗ Let hook handle fallback
      throw error;
    }
  },
};