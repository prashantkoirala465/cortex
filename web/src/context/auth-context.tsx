"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { apiFetch, withAuth } from "@/lib/api";

type User = {
  id: string;
  email: string;
  created_at: string;
};

export type AuthFetch = (path: string, options?: RequestInit) => Promise<unknown>;

type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  /** fetch wrapper that attaches the current access token and
   * transparently retries once after a silent refresh on a 401 */
  authFetch: AuthFetch;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const accessTokenRef = useRef<string | null>(null);

  const fetchMe = useCallback(async (token: string) => {
    const me = (await apiFetch("/auth/me", { headers: withAuth(token) })) as User;
    setUser(me);
    return me;
  }, []);

  const refresh = useCallback(async (): Promise<string | null> => {
    try {
      const body = (await apiFetch("/auth/refresh", { method: "POST" })) as {
        access_token: string;
      };
      accessTokenRef.current = body.access_token;
      return body.access_token;
    } catch {
      accessTokenRef.current = null;
      return null;
    }
  }, []);

  useEffect(() => {
    // refresh-token rotation is single-use, so if this effect ever runs
    // twice concurrently (React StrictMode's dev double-invoke, or a fast
    // remount), the losing call must not clobber state the winning call
    // already set - hence the `active` guard below.
    let active = true;

    (async () => {
      const token = await refresh();
      if (!active) return;

      if (token) {
        try {
          await fetchMe(token);
        } catch {
          if (!active) return;
          accessTokenRef.current = null;
          setUser(null);
        }
      }
      if (active) setIsLoading(false);
    })();

    return () => {
      active = false;
    };
  }, [refresh, fetchMe]);

  const login = useCallback(
    async (email: string, password: string) => {
      const body = (await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      })) as { access_token: string };
      accessTokenRef.current = body.access_token;
      await fetchMe(body.access_token);
    },
    [fetchMe],
  );

  const registerUser = useCallback(
    async (email: string, password: string) => {
      const body = (await apiFetch("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      })) as { access_token: string };
      accessTokenRef.current = body.access_token;
      await fetchMe(body.access_token);
    },
    [fetchMe],
  );

  const logout = useCallback(async () => {
    try {
      await apiFetch("/auth/logout", { method: "POST" });
    } finally {
      accessTokenRef.current = null;
      setUser(null);
    }
  }, []);

  const authFetch = useCallback(
    async (path: string, options: RequestInit = {}) => {
      try {
        return await apiFetch(path, {
          ...options,
          headers: { ...withAuth(accessTokenRef.current), ...options.headers },
        });
      } catch (err) {
        const status = (err as { status?: number }).status;
        if (status !== 401) throw err;

        const token = await refresh();
        if (!token) {
          setUser(null);
          throw err;
        }
        return apiFetch(path, {
          ...options,
          headers: { ...withAuth(token), ...options.headers },
        });
      }
    },
    [refresh],
  );

  return (
    <AuthContext.Provider
      value={{ user, isLoading, login, register: registerUser, logout, authFetch }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
