import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const API = axios.create({
  baseURL: API_BASE_URL,
});

export const runInference = async (payload) => {
  const response = await API.post("/inference/predict", payload);
  return response.data;
};

export const getInferenceModels = async () => {
  const response = await API.get("/inference/models");
  return response.data;
};

export const unloadInferenceModel = async () => {
  const response = await API.post("/inference/unload");
  return response.data;
};
