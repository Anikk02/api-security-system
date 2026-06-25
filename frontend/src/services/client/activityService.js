import axios from "axios";
import mockActivityData from "../../utils/client/mockActivityData";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export const activityService = {
  getActivity: async (window = 600) => {
    console.log("🚀 activityService called");

    if (USE_MOCK) {
      console.log("🧪 MOCK MODE ACTIVE");
      return mockActivityData;
    }

    try {
      console.log("🌐 Calling API: /api/dashboard/activity");

      // 🔐 Get token (adjust if you store differently)
      const token = localStorage.getItem("access_token");

      const res = await axios.get("/api/dashboard/activity", {
        params: {
          window: window, // ✅ only window
        },
        headers: {
          Authorization: `Bearer ${token}`, // ✅ REQUIRED
        },
      });

      // 🔗 Debug logs (keep, they’re useful)
      if (res.data?.correlations?.length > 0) {
        console.log("🔗 Spike Correlations:", res.data.correlations);
        const top = res.data.correlations[0];
        console.log(
          `🎯 Peak at ${top.peak_time}: ${top.target} → ${top.blocked} blocked`
        );
      }

      return res.data;

    } catch (error) {
      console.error("❌ API FAILED:", error?.response?.data || error.message);
      console.log("📦 Using mock data as fallback");
      return mockActivityData;
    }
  },
};