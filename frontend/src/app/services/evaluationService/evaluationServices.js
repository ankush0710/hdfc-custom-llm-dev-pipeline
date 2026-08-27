import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const API = axios.create({
  baseURL: API_BASE_URL,
});

export const getEvaluations = async (runId = null) => {
  const params = runId ? { run_id: runId } : {};
  const response = await API.get("/evaluations", { params });
  return response.data;
};

export const getEvaluationStats = async () => {
  const response = await API.get("/evaluations/stats");
  return response.data;
};

export const getEvaluationById = async (evaluationId) => {
  const response = await API.get(`/evaluations/${evaluationId}`);
  return response.data;
};

export const getEvaluationDetail = async (evaluationId) => {
  const response = await API.get(`/evaluations/${evaluationId}/detail`);
  return response.data;
};

export const createEvaluation = async (data) => {
  const response = await API.post("/evaluations", data);
  return response.data;
};

export const startEvaluation = async (evaluationId) => {
  const response = await API.post(`/evaluations/${evaluationId}/start`);
  return response.data;
};
