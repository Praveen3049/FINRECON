"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from "react";
import { AuthUser, UserRole } from "./types";
import { api } from "./api";

export const ROLE_ROUTE_PERMISSIONS: Record<UserRole, string[]> = {
  USER: ["/", "/ingestion", "/crypto", "/ai-assistant"],
  AUDITOR: ["/", "/reconciliation", "/exceptions", "/crypto", "/audit", "/ai-assistant"],
  MANAGER: ["/", "/ingestion", "/entities", "/reconciliation", "/exceptions", "/crypto", "/audit", "/ai-assistant"],
};

export const ROUTE_TITLES: Record<string, string> = {
  "/": "Command Center Dashboard",
  "/ingestion": "Multi-Source Data Ingestion",
  "/entities": "Deterministic Entity Resolution",
  "/reconciliation": "Multi-Pass Reconciliation Engine",
  "/exceptions": "Exception Investigation Workbench",
  "/crypto": "Crypto Ledger & Gas Variance",
  "/audit": "Cryptographic Audit Trail",
  "/ai-assistant": "AI Investigation Assistant",
};

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string, role?: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (roles: UserRole | UserRole[]) => boolean;
  canAccessRoute: (path: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize session from localStorage and revalidate
  useEffect(() => {
    let mounted = true;

    const initAuth = async () => {
      try {
        if (typeof window !== "undefined") {
          const storedToken = localStorage.getItem("finrecon_token");
          const storedUserRaw = localStorage.getItem("finrecon_user");

          if (storedToken && storedUserRaw) {
            try {
              const parsedUser = JSON.parse(storedUserRaw) as AuthUser;
              if (mounted) {
                setToken(storedToken);
                setUser(parsedUser);
              }
            } catch {
              localStorage.removeItem("finrecon_user");
            }
          }

          if (storedToken) {
            // Background revalidation with backend
            try {
              const freshUser = await api.getMe();
              if (mounted) {
                setUser(freshUser);
              }
            } catch (err: any) {
              if (err?.response?.status === 401) {
                if (mounted) {
                  setUser(null);
                  setToken(null);
                  localStorage.removeItem("finrecon_token");
                  localStorage.removeItem("finrecon_user");
                }
              }
            }
          }
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    initAuth();

    // Listen for global 401 expiration events emitted by Axios interceptor
    const handleAuthExpired = () => {
      setUser(null);
      setToken(null);
      localStorage.removeItem("finrecon_token");
      localStorage.removeItem("finrecon_user");
    };

    window.addEventListener("finrecon_auth_expired", handleAuthExpired);
    return () => {
      mounted = false;
      window.removeEventListener("finrecon_auth_expired", handleAuthExpired);
    };
  }, []);

  const login = useCallback(async (email: string, password: string, role?: string) => {
    const res = await api.login({ email, password, role });
    setUser(res.user);
    setToken(res.access_token);
  }, []);

  const signup = useCallback(async (name: string, email: string, password: string) => {
    const res = await api.signup({ name, email, password });
    setUser(res.user);
    setToken(res.access_token);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.logout();
    } finally {
      setUser(null);
      setToken(null);
    }
  }, []);

  const hasRole = useCallback((roles: UserRole | UserRole[]) => {
    if (!user) return false;
    const roleList = Array.isArray(roles) ? roles : [roles];
    return roleList.includes(user.role);
  }, [user]);

  const canAccessRoute = useCallback((path: string) => {
    if (path === "/login") return true;
    if (!user) return false;
    const allowed = ROLE_ROUTE_PERMISSIONS[user.role] || [];
    return allowed.includes(path);
  }, [user]);

  const value = useMemo(() => ({
    user,
    token,
    isAuthenticated: Boolean(user && token),
    isLoading,
    login,
    signup,
    logout,
    hasRole,
    canAccessRoute,
  }), [user, token, isLoading, login, signup, logout, hasRole, canAccessRoute]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
