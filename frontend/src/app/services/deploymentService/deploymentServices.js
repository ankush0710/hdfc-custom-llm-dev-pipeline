import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const API = axios.create({
  baseURL: API_BASE_URL,
});

export const getDeployments = async () => {
  const response = await API.get("/deployments");
  return response.data;
};

export const getDeploymentById = async (deploymentId) => {
  const response = await API.get(`/deployments/${deploymentId}`);
  return response.data;
};

export const deployModel = async (payload) => {
  const response = await API.post("/deployments", payload);
  return response.data;
};

export const unloadModel = async (deploymentId) => {
  const response = await API.post(`/deployments/${deploymentId}/unload`);
  return response.data;
};

export const reloadModel = async (deploymentId) => {
  const response = await API.post(`/deployments/${deploymentId}/reload`);
  return response.data;
};

export const restartDeployment = async (deploymentId) => {
  const response = await API.post(`/deployments/${deploymentId}/restart`);
  return response.data;
};

export const startDeployment = async (deploymentId) => {
  const response = await API.post(`/deployments/${deploymentId}/start`);
  return response.data;
};

export const deleteDeployment = async (deploymentId) => {
  const response = await API.delete(`/deployments/${deploymentId}`);
  return response.data;
};
