"use client";

import { create } from "zustand";

import {
  ApiError,
  getMe,
  login,
  logout,
  normalizeUser,
  register,
} from "@/lib/api";
import type {
  AuthMeResponse,
  AuthSessionResponse,
  User,
  UserStats,
} from "@/types/api";

export type AuthStatus = "checking" | "authed" | "unauth";

export interface AuthState {
  status: AuthStatus;
  user: User | null;
  stats: UserStats | null;
  loading: boolean;
  error: string | null;

  isAuthenticated: () => boolean;
  bootstrap: () => Promise<AuthMeResponse | null>;
  fetchMe: () => Promise<AuthMeResponse | null>;
  register: (args: {
    email: string;
    password: string;
    displayName?: string;
  }) => Promise<AuthSessionResponse | null>;
  login: (args: {
    email: string;
    password: string;
  }) => Promise<AuthSessionResponse | null>;
  logout: () => Promise<void>;
}

let bootstrapPromise: Promise<AuthMeResponse | null> | null = null;

function mergeUser(
  prevUser: User | null,
  nextUser: User | null | undefined,
): User | null {
  if (!nextUser) return null;
  const normalized = normalizeUser(nextUser, {
    fallbackUsername: prevUser?.username,
  });
  if (prevUser?.id && normalized?.id && prevUser.id === normalized.id) {
    return { ...prevUser, ...normalized };
  }
  return normalized ?? null;
}

export const useAuthStore = create<AuthState>()((set, get) => ({
  status: "checking",
  user: null,
  stats: null,
  loading: false,
  error: null,

  isAuthenticated: () => get().status === "authed",

  bootstrap: async () => {
    if (bootstrapPromise) return bootstrapPromise;

    bootstrapPromise = (async () => {
      set({ status: "checking" });
      try {
        const res = await getMe();
        set((state) => ({
          user: mergeUser(state.user, res?.user),
          stats: res?.stats ?? null,
          status: res?.user ? "authed" : "unauth",
          error: null,
        }));
        return res;
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          set({ user: null, stats: null, status: "unauth", error: null });
          return null;
        }
        set({
          user: null,
          stats: null,
          status: "unauth",
          error: err instanceof Error ? err.message : String(err),
        });
        return null;
      } finally {
        bootstrapPromise = null;
      }
    })();

    return bootstrapPromise;
  },

  fetchMe: async () => {
    try {
      const res = await getMe();
      set((state) => ({
        user: mergeUser(state.user, res?.user),
        stats: res?.stats ?? null,
        status: res?.user ? "authed" : state.status,
        error: null,
      }));
      return res;
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        set({ user: null, stats: null, status: "unauth" });
        return null;
      }
      set({ error: err instanceof Error ? err.message : String(err) });
      return null;
    }
  },

  register: async ({ email, password, displayName }) => {
    set({ loading: true, error: null });
    try {
      const res = await register({ email, password, displayName });
      set((state) => ({
        user: mergeUser(state.user, res?.user),
        stats: res?.stats ?? null,
        status: res?.user ? "authed" : "unauth",
        loading: false,
        error: null,
      }));
      return res;
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : String(err),
      });
      throw err;
    }
  },

  login: async ({ email, password }) => {
    set({ loading: true, error: null });
    try {
      const res = await login({ email, password });
      set((state) => ({
        user: mergeUser(state.user, res?.user),
        stats: res?.stats ?? null,
        status: res?.user ? "authed" : "unauth",
        loading: false,
        error: null,
      }));
      return res;
    } catch (err) {
      set({
        loading: false,
        error: err instanceof Error ? err.message : String(err),
      });
      throw err;
    }
  },

  logout: async () => {
    set({ loading: true, error: null });
    try {
      await logout();
    } catch {
      // ignore logout errors
    } finally {
      set({
        user: null,
        stats: null,
        status: "unauth",
        loading: false,
        error: null,
      });
    }
  },
}));
