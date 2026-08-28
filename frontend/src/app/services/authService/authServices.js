import apiClient from "@/app/services/apiClient";

export const signup = async (payload) => {
  const response = await apiClient.post("/auth/signup", payload);
  return response.data;
};

export const login = async (payload) => {
  const response = await apiClient.post("/auth/login", payload);
  return response.data;
};

export const getMe = async () => {
  const response = await apiClient.get("/auth/me");
  return response.data;
};

export const logout = async () => {
  const response = await apiClient.post("/auth/logout");
  return response.data;
};

export const getUsers = async () => {
  const response = await apiClient.get("/auth/users");
  return response.data;
};

export const updateUserRole = async (userId, role) => {
  const response = await apiClient.put(`/auth/users/${userId}/role`, { role });
  return response.data;
};

export const updateUserStatus = async (userId, isActive) => {
  const response = await apiClient.patch(`/auth/users/${userId}/status`, { is_active: isActive });
  return response.data;
};

