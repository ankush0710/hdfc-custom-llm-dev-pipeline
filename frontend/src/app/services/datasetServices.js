import axios from "axios";

const API = axios.create({ baseURL: "http://127.0.0.1:8000" });

export const uploadDataset = async (formData) => {
  const response = await API.post("/datasets/upload-dataset", formData);

  return response.data;
};

export const getDataset = async () => {
  const response = await API.get("/datasets");
  return response.data;
};

export const getDatasetById = async (id) => {
  const response = await API.get(`/datasets/${id}`);
  return response.data;
};

export const deleteDataset = async (id) => {
  const response = await API.delete(`/datasets/${id}`);

  return response.data;
};
