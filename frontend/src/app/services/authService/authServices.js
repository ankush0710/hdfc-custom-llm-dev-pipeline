import apiClient from "@/app/services/apiClient";

export const signup = async (payload) => {
  const cleanPayload = {
    full_name: payload?.full_name ? String(payload.full_name).trim() : "",
    email: payload?.email ? String(payload.email).trim().toLowerCase() : "",
    password: payload?.password ? String(payload.password) : "",
    confirm_password: payload?.confirm_password ? String(payload.confirm_password) : "",
  };
  const response = await apiClient.post("/auth/signup", cleanPayload);
  return response.data;
};


export const login = async (payload) => {
  try {
    const cleanPayload = {
      email: payload?.email
        ? String(payload.email).trim().toLowerCase()
        : "",
      password: payload?.password
        ? String(payload.password)
        : "",
    };

    console.log("Login payload:", {
      email: cleanPayload.email,
      passwordLength: cleanPayload.password.length,
    });

    const response = await apiClient.post("/auth/login", cleanPayload);


    return response.data;
  } catch (error) {
    throw error;
  }
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

