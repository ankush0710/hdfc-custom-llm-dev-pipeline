import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const API = axios.create({
  baseURL: API_BASE_URL,
});

export const uploadDataset = async (formData) => {
  const response = await API.post("/datasets/upload-dataset", formData);
  return response.data;
};

export const getDataset = async () => {
  const response = await API.get("/datasets");
  return response.data;
};

export const getDatasets = getDataset;

export const getDatasetById = async (id) => {
  const response = await API.get(`/datasets/${id}`);
  return response.data;
};

export const deleteDataset = async (id) => {
  const response = await API.delete(`/datasets/${id}`);
  return response.data;
};

export const getDatasetVersions = async (datasetId) => {
  const response = await API.get(`/datasets/${datasetId}/versions`);
  return response.data;
};

export const downloadDatasetFile = async (datasetId, filename = "dataset_file") => {
  const response = await API.get(`/datasets/${datasetId}/download`, {
    responseType: "blob",
  });
  
  // Create a blob URL and trigger download
  const blob = new Blob([response.data]);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  link.parentNode.removeChild(link);
  window.URL.revokeObjectURL(url);
  return true;
};

export const downloadVersionFile = async (versionId, filename = "dataset_version_file") => {
  const response = await API.get(`/datasets/versions/${versionId}/download`, {
    responseType: "blob",
  });
  
  const blob = new Blob([response.data]);
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  link.parentNode.removeChild(link);
  window.URL.revokeObjectURL(url);
  return true;
};

export const startProcessingJob = async (
  datasetVersionId,
  operations = ["clean", "remove_duplicate", "detect_pii", "deidentify_pii"]
) => {
  const response = await API.post("/data-processing/jobs", {
    dataset_version_id: Number(datasetVersionId),
    operations: Array.isArray(operations)
      ? operations
      : ["clean", "remove_duplicate", "detect_pii", "deidentify_pii"],
  });
  return response.data;
};

export const getProcessingJobStatus = async (jobId) => {
  const response = await API.get(`/data-processing/jobs/${jobId}`);
  return response.data;
};

export const getVersionQualityMetrics = async (versionId) => {
  try {
    const response = await API.get(`/data-processing/versions/${versionId}/metrics`);
    return response.data;
  } catch {
    return null;
  }
};
