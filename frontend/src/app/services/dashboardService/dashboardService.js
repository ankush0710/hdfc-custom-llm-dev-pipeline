import apiClient from "@/app/services/apiClient";
const API = apiClient;

export const getDashboardStats = async (params = {}) => {
  const response = await API.get("/pipeline/dashboard/stats", { params });
  return response.data;
};

/**
 * Fetches all system activities with backend pagination and optional filtering.
 * @param {Object} params - { limit: 10, offset: 0, event_type: "training_completed" }
 */
export const getActivities = async (params = {}) => {
  const response = await API.get("/pipeline/activities", { params });
  return response.data;
};

/**
 * Fetches structured training performance metrics for charting.
 * @param {number|null} runId - optional specific training run ID
 */
export const getTrainingPerformance = async (runId = null) => {
  const params = runId ? { run_id: runId } : {};
  const response = await API.get("/pipeline/training-performance", { params });
  return response.data;
};

/**
 * Fetches all available training runs for telemetry selection.
 */
export const getTrainingPerformanceRuns = async () => {
  const response = await API.get("/pipeline/training-performance/runs");
  return response.data;
};

