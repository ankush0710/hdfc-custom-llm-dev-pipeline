import apiClient from "@/app/services/apiClient";
const API = apiClient;

export const getTrainingRuns = async () => {
  const response = await API.get("/training/runs", {
    headers: {
      "Cache-Control": "no-cache",
      Pragma: "no-cache",
    },
    params: {
      _t: Date.now(),
    },
  });
  return response.data;
};

export const getTrainingRunById = async (runId) => {
  const response = await API.get(`/training/runs/${runId}`);
  return response.data;
};

export const getTrainingRunDetail = async (runId) => {
  const response = await API.get(`/training/runs/${runId}/detail`);
  return response.data;
};

export const getTrainingRunLogs = async (runId) => {
  const response = await API.get(`/training/runs/${runId}/logs`);
  return response.data;
};

// =================  POST request to create new training and start training ===================
export const createTrainingRun = async (data) => {
  const response = await API.post("/training/runs", data);
  return response.data;
};

export const startTrainingRun = async (runId) => {
  const response = await API.post(`/training/runs/${runId}/start`);
  return response.data;
};

export const stopTrainingRun = async (runId) => {
  const response = await API.post(`/training/runs/${runId}/stop`);
  return response.data;
};
