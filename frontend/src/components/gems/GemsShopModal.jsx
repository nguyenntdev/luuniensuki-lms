"use client";

import { useEffect, useState } from "react";
import { X, Gem, Heart, Snowflake, Lightbulb, Zap } from "lucide-react";
import useGemsStore from "@/stores/gemsStore";
import useHeartsStore from "@/stores/heartsStore";
import toast from "react-hot-toast";

const SHOP_ITEMS = [
  {
    id: "heart_refill",
    icon: Heart,
    title: "Refill Hearts",
    description: "Instantly refill all your hearts",
    cost: 25,
    color: "text-red-500",
    bgColor: "bg-red-500/10",
    borderColor: "border-red-500/50",
  },
  {
    id: "streak_freeze",
    icon: Snowflake,
    title: "Vé giữ chuỗi",
    description: "Protect your streak for 1 day",
    cost: 50,
    color: "text-cyan-500",
    bgColor: "bg-cyan-500/10",
    borderColor: "border-cyan-500/50",
  },
  {
    id: "quiz_hint",
    icon: Lightbulb,
    title: "Quiz Hint",
    description: "Nhận gợi ý cho câu hỏi trắc nghiệm khó",
    cost: 5,
    color: "text-yellow-500",
    bgColor: "bg-yellow-500/10",
    borderColor: "border-yellow-500/50",
  },
  {
    id: "double_xp",
    icon: Zap,
    title: "Double XP Boost",
    description: "2x XP for the next 30 minutes",
    cost: 100,
    color: "text-purple-500",
    bgColor: "bg-purple-500/10",
    borderColor: "border-purple-500/50",
  },
];

export default function GemsShopModal({ isOpen, onClose, onPurchase }) {
  const gems = useGemsStore((state) => state.gems);
  const spendGems = useGemsStore((state) => state.spendGems);
  const canAfford = useGemsStore((state) => state.canAfford);
  const refillHearts = useHeartsStore((state) => state.refillHearts);
  const [purchasing, setPurchasing] = useState(null);

  useEffect(() => {
    if (!isOpen) return;

    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = prevOverflow;
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    const onKeyDown = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose?.();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isOpen, onClose]);

  const handlePurchase = async (item) => {
    if (purchasing) return;
    if (!canAfford(item.cost)) {
      toast.error("Not enough gems!", {
        icon: "💎",
        duration: 3000,
      });
      return;
    }

    setPurchasing(item.id);

    try {
      // Handle specific item purchases
      if (item.id === "heart_refill") {
        await refillHearts("gems");
      }

      // Spend gems
      spendGems(item.cost, item.title);

      toast.success(`${item.title} purchased!`, {
        icon: "✨",
        duration: 3000,
      });

      onPurchase?.(item);

      // Close modal after short delay
      setTimeout(() => {
        onClose?.();
      }, 500);
    } catch (err) {
      console.error("Purchase failed:", err);
      toast.error(err.message || "Purchase failed. Please try again.", {
        icon: "❌",
        duration: 4000,
      });
    } finally {
      setPurchasing(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100]">
      <div
        className="fixed inset-0 bg-background/80 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
      />

      <div className="fixed inset-0 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center px-4 py-6">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="gems-shop-title"
            className="relative w-full max-w-2xl overflow-hidden rounded-3xl border border-border bg-card/90 backdrop-blur-xl shadow-elegant"
          >
            <div className="absolute -top-16 -right-16 h-56 w-56 rounded-full bg-blue-500/10 blur-3xl pointer-events-none" />
            <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-purple-500/10 blur-3xl pointer-events-none" />

            <div className="relative p-6 sm:p-8">
              <button
                type="button"
                onClick={onClose}
                className="absolute right-4 top-4 inline-flex h-9 w-9 items-center justify-center rounded-xl text-muted-foreground hover:text-foreground hover:bg-muted/40 transition-colors focus-ring"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>

              <div className="text-center mb-6">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-blue-500/10 mb-4">
                  <Gem className="w-8 h-8 text-blue-500 fill-blue-400" />
                </div>
                <h2
                  id="gems-shop-title"
                  className="text-2xl sm:text-3xl font-bold text-foreground"
                >
                  Gems Shop
                </h2>
                <p className="text-sm text-muted-foreground mt-2">
                  Your balance:{" "}
                  <span className="font-semibold text-blue-500">
                    {gems.toLocaleString()} gems
                  </span>
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {SHOP_ITEMS.map((item) => (
                  <ShopItem
                    key={item.id}
                    item={item}
                    onPurchase={() => handlePurchase(item)}
                    canAfford={canAfford(item.cost)}
                    isPurchasing={purchasing === item.id}
                    disabled={!!purchasing}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function ShopItem({ item, onPurchase, canAfford, isPurchasing, disabled }) {
  const Icon = item.icon;

  const baseClasses =
    "w-full p-5 rounded-2xl border-2 transition-all duration-200 text-left";
  const hoverClasses =
    !disabled && canAfford
      ? "hover:scale-[1.02] hover:shadow-lg cursor-pointer"
      : "";
  const disabledClasses = !canAfford ? "opacity-50 cursor-not-allowed" : "";

  return (
    <button
      type="button"
      onClick={onPurchase}
      disabled={disabled || !canAfford}
      className={`${baseClasses} ${hoverClasses} ${disabledClasses} ${item.bgColor} ${item.borderColor}`}
    >
      <div className="flex flex-col gap-3">
        <div className="flex items-start gap-3">
          <div className={`flex-shrink-0 ${item.color}`}>
            <Icon className="w-7 h-7" strokeWidth={2} />
          </div>
          <div className="flex-1 min-w-0">
            <div className={`font-semibold ${item.color}`}>{item.title}</div>
            <div className="text-xs text-muted-foreground mt-1">
              {item.description}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2 border-t border-border/50">
          <div className="flex items-center gap-1.5">
            <Gem className="w-4 h-4 text-blue-500" />
            <span className="text-sm font-bold text-foreground">
              {item.cost}
            </span>
          </div>

          {isPurchasing ? (
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          ) : (
            <span
              className={`text-xs font-medium ${
                canAfford ? "text-green-500" : "text-red-500"
              }`}
            >
              {canAfford ? "Available" : "Not enough"}
            </span>
          )}
        </div>
      </div>
    </button>
  );
}

