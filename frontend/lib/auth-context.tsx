"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { api, clearTokens, getStoredTokens, storeTokens } from "./api-client";
import type { User } from "./types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, organization?: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    const { access } = getStoredTokens();
    if (!access) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api.auth.me();
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Session bootstrap on mount: check for a stored token and resolve the
    // current user (or clear loading immediately if there's none).
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refreshUser();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const resp = await api.auth.login(email, password);
    storeTokens(resp.access_token, resp.refresh_token);
    setUser(resp.user);
  }, []);

  const register = useCallback(async (email: string, password: string, fullName: string, organization?: string) => {
    const resp = await api.auth.register(email, password, fullName, organization);
    storeTokens(resp.access_token, resp.refresh_token);
    setUser(resp.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.auth.logout();
    } catch {
      // ignore -- logging out client-side regardless
    }
    clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
