"use client";

import { create } from "zustand";
import {
  getDueReviewCards,
  submitReviewResult,
  getReviewStats,
  addCardToReviewDeck,
} from "@/lib/api";

export const usePracticeStore = create((set, get) => ({
  dueCards: [],
  currentCard: null,
  stats: null,
  loading: false,
  error: null,
  sessionCards: [],
  sessionResults: [],
  
  // Load due review cards
  loadDueCards: async (limit = 20) => {
    set({ loading: true, error: null });
    try {
      const data = await getDueReviewCards(limit);
      set({
        dueCards: data.cards || [],
        loading: false,
      });
      return data;
    } catch (error) {
      set({
        error: error.message || "Failed to load due cards",
        loading: false,
      });
      throw error;
    }
  },

  // Load review statistics
  loadStats: async () => {
    set({ loading: true, error: null });
    try {
      const stats = await getReviewStats();
      set({
        stats,
        loading: false,
      });
      return stats;
    } catch (error) {
      set({
        error: error.message || "Failed to load stats",
        loading: false,
      });
      throw error;
    }
  },

  // Start a practice session
  startSession: (cards) => {
    set({
      sessionCards: cards,
      sessionResults: [],
      currentCard: cards[0] || null,
    });
  },

  // Submit review for current card
  submitReview: async (quality) => {
    const { currentCard, sessionCards, sessionResults } = get();
    
    if (!currentCard) {
      throw new Error("No current card to review");
    }

    set({ loading: true, error: null });
    try {
      const result = await submitReviewResult(currentCard.id, quality);
      
      const newResults = [
        ...sessionResults,
        {
          cardId: currentCard.id,
          motifId: currentCard.motif_id,
          quality,
          result,
        },
      ];

      // Move to next card
      const currentIndex = sessionCards.findIndex(c => c.id === currentCard.id);
      const nextCard = sessionCards[currentIndex + 1] || null;

      set({
        sessionResults: newResults,
        currentCard: nextCard,
        loading: false,
      });

      return result;
    } catch (error) {
      set({
        error: error.message || "Failed to submit review",
        loading: false,
      });
      throw error;
    }
  },

  // Add a motif to review deck
  addToReviewDeck: async (motifId) => {
    set({ loading: true, error: null });
    try {
      const card = await addCardToReviewDeck(motifId);
      set({ loading: false });
      
      // Reload due cards to include the new one
      await get().loadDueCards();
      
      return card;
    } catch (error) {
      set({
        error: error.message || "Failed to add card to deck",
        loading: false,
      });
      throw error;
    }
  },

  // End current session
  endSession: () => {
    set({
      sessionCards: [],
      currentCard: null,
    });
  },

  // Get session progress
  getSessionProgress: () => {
    const { sessionCards, sessionResults } = get();
    return {
      total: sessionCards.length,
      completed: sessionResults.length,
      remaining: sessionCards.length - sessionResults.length,
    };
  },

  // Clear error
  clearError: () => set({ error: null }),

  // Reset store
  reset: () => set({
    dueCards: [],
    currentCard: null,
    stats: null,
    loading: false,
    error: null,
    sessionCards: [],
    sessionResults: [],
  }),
}));

