import apiClient from "@/app/services/apiClient";
const API = apiClient;

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
