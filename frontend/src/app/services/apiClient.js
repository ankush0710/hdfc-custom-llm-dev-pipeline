import axios from "axios";
import { toast } from "sonner";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request Interceptor: Attach JWT Bearer Token automatically
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== "undefined") {
      const token = localStorage.getItem("token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Handle 401 Unauthorized & 403 Forbidden globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (typeof window !== "undefined") {
      const status = error?.response?.status;
      const isAuthRoute = error?.config?.url?.includes("/auth/login") || error?.config?.url?.includes("/auth/signup");

      if (status === 401 && !isAuthRoute) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        window.dispatchEvent(new Event("auth:unauthorized"));
        if (!window.location.pathname.startsWith("/login")) {
          window.location.href = "/login";
        }
      } else if (status === 403) {
        const msg = error?.response?.data?.detail || "Access Denied: You do not have permission to perform this action.";
        toast.error("Permission Denied", { description: msg });
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
