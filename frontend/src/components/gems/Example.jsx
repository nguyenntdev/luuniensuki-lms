"use client";

import { useState } from "react";
import { GemsDisplay, GemsShopModal } from "@/components/gems";
import useGemsStore, { GEM_AMOUNTS } from "@/stores/gemsStore";

/**
 * Example usage of Gems system components
 * 
 * This example demonstrates:
 * 1. Displaying gem balance with animated counter
 * 2. Opening gems shop modal
 * 3. Awarding gems for actions
 */
export default function GemsExample() {
  const [shopOpen, setShopOpen] = useState(false);
  const addGems = useGemsStore((state) => state.addGems);
  const gems = useGemsStore((state) => state.gems);

  const handleCompleteLesson = () => {
    addGems(GEM_AMOUNTS.COMPLETE_LESSON, "Completed lesson");
  };

  const handlePerfectQuiz = () => {
    addGems(GEM_AMOUNTS.PERFECT_QUIZ, "Perfect quiz score");
  };

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-2xl mx-auto space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-4">Gems System Example</h1>
          <p className="text-muted-foreground">
            Demo of the gems gamification system
          </p>
        </div>

        {/* Gems Display */}
        <div className="p-6 rounded-xl border border-border bg-card">
          <h2 className="text-xl font-semibold mb-4">Gems Display</h2>
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">Small:</span>
                <GemsDisplay size="sm" />
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">Medium:</span>
                <GemsDisplay size="md" />
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">Large:</span>
                <GemsDisplay size="lg" />
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm text-muted-foreground">
                  Clickable:
                </span>
                <GemsDisplay onClick={() => setShopOpen(true)} />
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-muted-foreground mb-1">
                Current Balance
              </div>
              <div className="text-3xl font-bold text-blue-500">
                {gems.toLocaleString()}
              </div>
            </div>
          </div>
        </div>

        {/* Award Gems Actions */}
        <div className="p-6 rounded-xl border border-border bg-card">
          <h2 className="text-xl font-semibold mb-4">Award Gems</h2>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={handleCompleteLesson}
              className="px-4 py-3 rounded-lg bg-green-500/10 border border-green-500/50 text-green-500 hover:bg-green-500/20 transition-colors"
            >
              Complete Lesson (+{GEM_AMOUNTS.COMPLETE_LESSON})
            </button>
            <button
              onClick={handlePerfectQuiz}
              className="px-4 py-3 rounded-lg bg-purple-500/10 border border-purple-500/50 text-purple-500 hover:bg-purple-500/20 transition-colors"
            >
              Perfect Quiz (+{GEM_AMOUNTS.PERFECT_QUIZ})
            </button>
            <button
              onClick={() =>
                addGems(GEM_AMOUNTS.DAILY_GOAL, "Reached daily goal")
              }
              className="px-4 py-3 rounded-lg bg-blue-500/10 border border-blue-500/50 text-blue-500 hover:bg-blue-500/20 transition-colors"
            >
              Daily Goal (+{GEM_AMOUNTS.DAILY_GOAL})
            </button>
            <button
              onClick={() =>
                addGems(GEM_AMOUNTS.STREAK_7_DAYS, "7 day streak bonus")
              }
              className="px-4 py-3 rounded-lg bg-orange-500/10 border border-orange-500/50 text-orange-500 hover:bg-orange-500/20 transition-colors"
            >
              7 Day Streak (+{GEM_AMOUNTS.STREAK_7_DAYS})
            </button>
          </div>
        </div>

        {/* Shop Button */}
        <div className="p-6 rounded-xl border border-border bg-card text-center">
          <h2 className="text-xl font-semibold mb-4">Gems Shop</h2>
          <p className="text-sm text-muted-foreground mb-4">
            Spend your gems on power-ups and bonuses
          </p>
          <button
            onClick={() => setShopOpen(true)}
            className="px-6 py-3 rounded-lg bg-primary text-primary-foreground font-semibold hover:opacity-90 transition-opacity"
          >
            Open Shop
          </button>
        </div>

        {/* Gems Shop Modal */}
        <GemsShopModal
          isOpen={shopOpen}
          onClose={() => setShopOpen(false)}
          onPurchase={(item) => console.log("Purchased:", item)}
        />
      </div>
    </div>
  );
}

