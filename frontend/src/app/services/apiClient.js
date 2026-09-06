import axios from "axios";
import { toast } from "sonner";

function resolveApiBaseUrl() {
  const raw = process.env.NEXT_PUBLIC_API_URL;
  if (!raw || typeof raw !== "string") {
    return "http://127.0.0.1:8000";
  }

  // If multiple URLs were entered separated by comma, take the first non-empty URL
  const candidate = raw.includes(",")
    ? raw.split(",").map((s) => s.trim()).filter(Boolean)[0]
    : raw.trim();

  if (!candidate) {
    return "http://127.0.0.1:8000";
  }

  // Replace 0.0.0.0 with 127.0.0.1 because browsers cannot route to 0.0.0.0
  let sanitized = candidate.replace("0.0.0.0", "127.0.0.1").replace(/\/+$/, "");

  // Validate that it forms a valid URL
  try {
    new URL(sanitized);
    return sanitized;
  } catch {
    console.warn(`[apiClient] Invalid NEXT_PUBLIC_API_URL "${raw}". Falling back to http://127.0.0.1:8000`);
    return "http://127.0.0.1:8000";
  }
}

const API_BASE_URL = resolveApiBaseUrl();

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
    // If sending FormData, do not set application/json to let Axios/browser set multipart/form-data boundary
    if (typeof FormData !== "undefined" && config.data instanceof FormData) {
      delete config.headers["Content-Type"];
    }
    return config;
  },
  (error) => Promise.reject(error)
);


export function getApiErrorMessage(error, fallback = "An unexpected error occurred.") {
  if (!error) return fallback;
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || `${d.loc?.join(".")}: ${d.msg}`).join("; ");
  }
  if (detail && typeof detail === "object") {
    return detail.message || JSON.stringify(detail);
  }
  if (error?.response?.data?.message) {
    return error.response.data.message;
  }
  if (error?.message) {
    return error.message;
  }
  return fallback;
}

// Response Interceptor: Handle 401 Unauthorized & 403 Forbidden globally
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (typeof window !== "undefined") {
      const status = error?.response?.status;
      const url = error?.config?.url || "";
      const isAuthRoute = url.includes("/auth/login") || url.includes("/auth/signup");

      if (status === 401 && !isAuthRoute) {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
        window.dispatchEvent(new Event("auth:unauthorized"));
        if (!window.location.pathname.startsWith("/login")) {
          window.location.href = "/login";
        }
      } else if (status === 403 && !isAuthRoute) {
        const msg = getApiErrorMessage(error, "Access Denied: You do not have permission to perform this action.");
        toast.error("Permission Denied", { description: msg });
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
