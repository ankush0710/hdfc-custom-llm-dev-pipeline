import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const API = axios.create({
  baseURL: API_BASE_URL,
});

/**
 * Fetches aggregate dashboard statistics from the backend.
 * Returns real DB counts: datasets, models, training runs (active/completed/failed),
 * evaluations, avg evaluation score, active deployments, and recent activity feed.
 * No hardcoded fallback values.
 */
export const getDashboardStats = async () => {
  const response = await API.get("/pipeline/dashboard/stats");
  return response.data;
};
