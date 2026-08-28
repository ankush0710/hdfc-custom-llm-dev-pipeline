import apiClient from "@/app/services/apiClient";
const API = apiClient;

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
