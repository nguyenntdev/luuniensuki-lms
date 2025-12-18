"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import { normalizeUser, getMe, login, register } from "@/lib/api";

export const useAuthStore = create(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      stats: null,
      loading: false,
      error: null,

      isAuthenticated: () => Boolean(get().accessToken),

      logout: () => set({ accessToken: null, refreshToken: null, user: null, stats: null, error: null }),

      register: async ({ email, password, displayName }) => {
        set({ loading: true, error: null });
        try {
          const res = await register({ email, password, displayName });
          set({
            accessToken: res.access_token,
            refreshToken: res.refresh_token,
            user: res.user,
            loading: false,
          });
          await get().fetchMe();
          return res;
        } catch (err) {
          set({ loading: false, error: err instanceof Error ? err.message : String(err) });
          throw err;
        }
      },

      login: async ({ email, password }) => {
        set({ loading: true, error: null });
        try {
          const res = await login({ email, password });
          set({
            accessToken: res.access_token,
            refreshToken: res.refresh_token,
            user: res.user,
            loading: false,
          });
          await get().fetchMe();
          return res;
        } catch (err) {
          set({ loading: false, error: err instanceof Error ? err.message : String(err) });
          throw err;
        }
      },

      fetchMe: async () => {
        const token = get().accessToken;
        if (!token) return null;

        try {
          const res = await getMe({ token });
          set((state) => {
            const prevUser = state.user;
            const nextUser = res?.user ? normalizeUser(res.user, { fallbackUsername: prevUser?.username }) : res?.user;
            const shouldMerge = prevUser?.id && nextUser?.id && prevUser.id === nextUser.id;

            return {
              user: shouldMerge ? { ...prevUser, ...nextUser } : nextUser,
              stats: res.stats,
            };
          });
          return res;
        } catch (err) {
          set({ error: err instanceof Error ? err.message : String(err) });
          return null;
        }
      },
    }),
    {
      name: "luuniensuki-auth",
      version: 2,
      storage: createJSONStorage(() => localStorage),
      migrate: (persistedState, version) => {
        if (version >= 2) return persistedState;
        const user = persistedState?.user;
        if (!user) return persistedState;
        return { ...persistedState, user: normalizeUser(user) };
      },
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
    }
  )
);
