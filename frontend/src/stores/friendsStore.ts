"use client";

import { create } from "zustand";
import {
  getFriends,
  getFriendRequests,
  sendFriendRequest,
  acceptFriendRequest,
  rejectFriendRequest,
  removeFriend,
} from "@/lib/api";

export interface Friend {
  id: string | number;
  username?: string;
  display_name?: string;
  avatar_url?: string | null;
  [key: string]: unknown;
}

export interface FriendRequest {
  id: string | number;
  from_user_id?: string | number;
  to_user_id?: string | number;
  [key: string]: unknown;
}

interface FriendsState {
  friends: Friend[];
  requests: FriendRequest[];
  loading: boolean;
  error: string | null;
  fetchFriends: () => Promise<Friend[]>;
  fetchRequests: () => Promise<FriendRequest[]>;
  sendRequest: (toUserId: string | number) => Promise<void>;
  acceptRequest: (requestId: string | number) => Promise<void>;
  rejectRequest: (requestId: string | number) => Promise<void>;
  removeFriend: (friendId: string | number) => Promise<void>;
  reset: () => void;
}

const getErrorMessage = (error: unknown): string =>
  error instanceof Error ? error.message : String(error);

export const useFriendsStore = create<FriendsState>((set, get) => ({
  friends: [],
  requests: [],
  loading: false,
  error: null,

  fetchFriends: async () => {
    set({ loading: true, error: null });
    try {
      const data = (await getFriends()) as { friends?: Friend[] };
      set({ friends: data.friends || [], loading: false });
      return data.friends || [];
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
      throw error;
    }
  },

  fetchRequests: async () => {
    set({ loading: true, error: null });
    try {
      const data = (await getFriendRequests()) as {
        requests?: FriendRequest[];
      };
      set({ requests: data.requests || [], loading: false });
      return data.requests || [];
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
      throw error;
    }
  },

  sendRequest: async (toUserId) => {
    set({ loading: true, error: null });
    try {
      await sendFriendRequest(toUserId);
      set({ loading: false });
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
      throw error;
    }
  },

  acceptRequest: async (requestId) => {
    set({ loading: true, error: null });
    try {
      await acceptFriendRequest(requestId);
      // Refresh both friends and requests
      await get().fetchFriends();
      await get().fetchRequests();
      set({ loading: false });
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
      throw error;
    }
  },

  rejectRequest: async (requestId) => {
    set({ loading: true, error: null });
    try {
      await rejectFriendRequest(requestId);
      await get().fetchRequests();
      set({ loading: false });
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
      throw error;
    }
  },

  removeFriend: async (friendId) => {
    set({ loading: true, error: null });
    try {
      await removeFriend(friendId);
      await get().fetchFriends();
      set({ loading: false });
    } catch (error) {
      set({ error: getErrorMessage(error), loading: false });
      throw error;
    }
  },

  reset: () => {
    set({
      friends: [],
      requests: [],
      loading: false,
      error: null,
    });
  },
}));
