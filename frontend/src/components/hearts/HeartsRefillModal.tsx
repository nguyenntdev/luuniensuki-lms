"use client";

import { useEffect, useState, type ReactNode } from "react";
import { X, Heart, Gem, Clock, Sparkles } from "lucide-react";
import useHeartsStore from "@/stores/heartsStore";

type RefillType = "gems" | "streak_freeze";

interface HeartsRefillModalProps {
  isOpen: boolean;
  onClose?: () => void;
  onSuccess?: (result: unknown) => void;
}

export default function HeartsRefillModal({ isOpen, onClose, onSuccess }: HeartsRefillModalProps) {
  const hearts = useHeartsStore((state) => state.hearts);
  const maxHearts = useHeartsStore((state) => state.maxHearts);
  const refillHearts = useHeartsStore((state) => state.refillHearts);
  const consumeStreakFreeze = useHeartsStore((state) => state.useStreakFreeze);
  const isLoading = useHeartsStore((state) => state.isLoading);
  const error = useHeartsStore((state) => state.error);

  const [refillType, setRefillType] = useState<RefillType | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

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

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose?.();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isOpen, onClose]);

  const handleRefill = async (type: RefillType) => {
    if (isProcessing || isLoading) return;

    setRefillType(type);
    setIsProcessing(true);

    try {
      let result;
      if (type === "streak_freeze") {
        result = await consumeStreakFreeze();
      } else {
        result = await refillHearts(type);
      }

      onSuccess?.(result);
      setTimeout(() => {
        onClose?.();
      }, 500);
    } catch (err) {
      console.error("Refill failed:", err);
    } finally {
      setIsProcessing(false);
      setRefillType(null);
    }
  };

  if (!isOpen) return null;

  const heartsNeeded = maxHearts - hearts;

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
            aria-labelledby="hearts-refill-title"
            className="relative w-full max-w-md overflow-hidden rounded-3xl border border-border bg-card/90 backdrop-blur-xl shadow-elegant"
          >
            <div className="absolute -top-16 -right-16 h-56 w-56 rounded-full bg-red-500/10 blur-3xl pointer-events-none" />
            <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-primary/10 blur-3xl pointer-events-none" />

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
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-500/10 mb-4">
                  <Heart className="w-8 h-8 text-red-500 fill-red-500" />
                </div>
                <h2
                  id="hearts-refill-title"
                  className="text-2xl font-bold text-foreground"
                >
                  Out of Hearts
                </h2>
                <p className="text-sm text-muted-foreground mt-2">
                  You need hearts to continue learning. Refill to keep going!
                </p>
              </div>

              <div className="space-y-3 mb-6">
                <RefillOption
                  icon={<Gem className="w-5 h-5" />}
                  title="Refill with Gems"
                  description={`Refill ${heartsNeeded} heart${heartsNeeded !== 1 ? "s" : ""}`}
                  cost="350 gems"
                  onClick={() => handleRefill("gems")}
                  isLoading={isProcessing && refillType === "gems"}
                  disabled={isProcessing}
                  primary
                />

                <RefillOption
                  icon={<Sparkles className="w-5 h-5" />}
                  title="Dùng vé giữ chuỗi"
                  description="Restore all hearts"
                  cost="1 freeze"
                  onClick={() => handleRefill("streak_freeze")}
                  isLoading={isProcessing && refillType === "streak_freeze"}
                  disabled={isProcessing}
                />

                <RefillOption
                  icon={<Clock className="w-5 h-5" />}
                  title="Wait for Refill"
                  description="1 heart every 4 hours"
                  onClick={onClose}
                  disabled={isProcessing}
                  secondary
                />
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-sm text-destructive">
                  {error}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

interface RefillOptionProps {
  icon: ReactNode;
  title: string;
  description: string;
  cost?: string;
  onClick?: () => void;
  isLoading?: boolean;
  disabled?: boolean;
  primary?: boolean;
  secondary?: boolean;
}

function RefillOption({
  icon,
  title,
  description,
  cost,
  onClick,
  isLoading = false,
  disabled = false,
  primary = false,
  secondary = false,
}: RefillOptionProps) {
  const baseClasses = "w-full p-4 rounded-xl border transition-all duration-200 text-left";
  const hoverClasses = !disabled
    ? "hover:scale-[1.02] hover:shadow-md cursor-pointer"
    : "opacity-60 cursor-not-allowed";

  let colorClasses = "border-border bg-muted/20 hover:bg-muted/40";
  if (primary) {
    colorClasses = "border-primary/50 bg-primary/10 hover:bg-primary/20";
  } else if (secondary) {
    colorClasses = "border-border bg-card hover:bg-muted/20";
  }

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${hoverClasses} ${colorClasses}`}
    >
      <div className="flex items-center gap-3">
        <div className={`flex-shrink-0 ${primary ? "text-primary" : "text-foreground"}`}>
          {icon}
        </div>
        <div className="flex-1">
          <div className={`font-medium ${primary ? "text-primary" : "text-foreground"}`}>
            {title}
          </div>
          <div className="text-xs text-muted-foreground mt-0.5">
            {description}
          </div>
        </div>
        {cost && (
          <div className="text-sm font-semibold text-foreground">
            {cost}
          </div>
        )}
        {isLoading && (
          <div className="flex-shrink-0">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>
    </button>
  );
}
