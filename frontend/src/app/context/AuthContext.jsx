"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { login as apiLogin, signup as apiSignup, getMe, logout as apiLogout } from "@/app/services/authService/authServices";

const AuthContext = createContext({
  user: null,
  token: null,
  role: "VIEWER",
  isAuthenticated: false,
  loading: true,
  login: async () => {},
  signup: async () => {},
  logout: () => {},
  hasRole: () => false,
});

const PUBLIC_ROUTES = ["/login", "/signup"];

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  // Load session from localStorage on client load
  const initAuth = useCallback(async () => {
    try {
      if (typeof window !== "undefined") {
        const storedToken = localStorage.getItem("token");
        const storedUser = localStorage.getItem("user");

        if (storedToken) {
          setToken(storedToken);
          if (storedUser) {
            setUser(JSON.parse(storedUser));
          }
          // Verify token validity with backend GET /auth/me
          try {
            const me = await getMe();
            setUser(me);
            localStorage.setItem("user", JSON.stringify(me));
          } catch (err) {
            console.error("Session verification failed:", err);
            localStorage.removeItem("token");
            localStorage.removeItem("user");
            setToken(null);
            setUser(null);
          }
        }
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    initAuth();

    // Listen for unauthorized 401 events dispatched from apiClient
    const handleUnauthorized = () => {
      setUser(null);
      setToken(null);
      localStorage.removeItem("token");
      localStorage.removeItem("user");
    };

    if (typeof window !== "undefined") {
      window.addEventListener("auth:unauthorized", handleUnauthorized);
      return () => window.removeEventListener("auth:unauthorized", handleUnauthorized);
    }
  }, [initAuth]);

  // Handle route protection redirects
  useEffect(() => {
    if (loading) return;

    const isPublic = PUBLIC_ROUTES.includes(pathname);
    const isAuth = Boolean(token && user);

    if (!isAuth && !isPublic) {
      router.replace("/login");
    } else if (isAuth && isPublic) {
      router.replace("/");
    }
  }, [loading, token, user, pathname, router]);

  const login = async (email, password) => {
    const res = await apiLogin({ email, password });
    const { access_token, user: loggedUser } = res;

    setToken(access_token);
    setUser(loggedUser);
    localStorage.setItem("token", access_token);
    localStorage.setItem("user", JSON.stringify(loggedUser));

    router.replace("/");
    return loggedUser;
  };

  const signup = async (full_name, email, password, confirm_password) => {
    const registeredUser = await apiSignup({
      full_name,
      email,
      password,
      confirm_password,
    });
    return registeredUser;
  };

  const logout = async () => {
    try {
      await apiLogout();
    } catch (err) {
      // Ignore network errors on logout
    } finally {
      setUser(null);
      setToken(null);
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      router.replace("/login");
    }
  };

  const refreshProfile = useCallback(async () => {
    try {
      const me = await getMe();
      setUser(me);
      if (typeof window !== "undefined") {
        localStorage.setItem("user", JSON.stringify(me));
      }
      return me;
    } catch (err) {
      console.error("Profile refresh failed:", err);
      return null;
    }
  }, []);

  const hasRole = useCallback(
    (...allowedRoles) => {
      if (!user || !user.role) return false;
      const rawRole = user.role.toUpperCase();
      const currentRole = rawRole === "DATA_SCIENTIST" ? "DS" : rawRole;
      if (currentRole === "ADMIN") return true;

      const normalizedAllowed = allowedRoles.map((r) => {
        const up = r.toUpperCase();
        return up === "DATA_SCIENTIST" ? "DS" : up;
      });

      return normalizedAllowed.includes(currentRole);
    },
    [user]
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role: (user?.role?.toUpperCase() === "DATA_SCIENTIST" ? "DS" : user?.role?.toUpperCase()) || "VIEWER",
        isAuthenticated: Boolean(token && user),
        loading,
        login,
        signup,
        logout,
        hasRole,
        refreshProfile,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);
