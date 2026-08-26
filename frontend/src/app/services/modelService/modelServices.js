import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const API = axios.create({
  baseURL: API_BASE_URL,
});

export const getModels = async () => {
  const response = await API.get("/models");
  return response.data;
};

export const getModelById = async (modelId) => {
  const response = await API.get(`/models/${modelId}`);
  return response.data;
};

export const getModelDetail = async (modelId) => {
  const response = await API.get(`/models/${modelId}/detail`);
  return response.data;
};

export const registerModel = async (data) => {
  const response = await API.post("/models", data);
  return response.data;
};

export const updateModelStatus = async (modelId, status) => {
  const response = await API.patch(`/models/${modelId}/status`, { status });
  return response.data;
};
