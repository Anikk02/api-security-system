import axios from "axios";
import  mockActivityData  from "../../utils/client/mockActivityData";

const USE_MOCK = import.meta.env.VITE_USE_MOCK === "true";

export const activityService = {
  getActivity: async () => {
    console.log("🚀 activityService called");

    if (USE_MOCK) {
        console.log("🧪 MOCK MODE ACTIVE");
        return mockActivityData;
    }

    try {
        console.log("🌐 Calling API...");
        const res = await axios.get("/api/dashboard/activity");
        return res.data;

    } catch (error) {
        console.log("❌ API FAILED → FALLBACK");
        return mockActivityData;
    }
  },
};