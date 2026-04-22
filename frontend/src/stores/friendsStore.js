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

export const useFriendsStore = create((set, get) => ({
  friends: [],
  requests: [],
  loading: false,
  error: null,

  fetchFriends: async () => {
    set({ loading: true, error: null });
    try {
      const data = await getFriends();
      set({ friends: data.friends || [], loading: false });
      return data.friends || [];
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  fetchRequests: async () => {
    set({ loading: true, error: null });
    try {
      const data = await getFriendRequests();
      set({ requests: data.requests || [], loading: false });
      return data.requests || [];
    } catch (error) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  sendRequest: async (toUserId) => {
    set({ loading: true, error: null });
    try {
      await sendFriendRequest(toUserId);
      set({ loading: false });
    } catch (error) {
      set({ error: error.message, loading: false });
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
      set({ error: error.message, loading: false });
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
      set({ error: error.message, loading: false });
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
      set({ error: error.message, loading: false });
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

