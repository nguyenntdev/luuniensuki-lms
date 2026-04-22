"use client";

import { useEffect, useMemo, useRef, useState } from "react";

const STORAGE_KEY = "hasSeenOnboarding";

const DEFAULT_SLIDES = [
  {
    title: "Di Sản Trong Tầm Tay",
    description: "Chào mừng bạn đến với Luuniensuki...",
    icon: "🏛️",
  },
  {
    title: "Trải Nghiệm 3D Chân Thực",
    description: "Tương tác trực tiếp với mô hình 3D...",
    icon: "🔍",
  },
  {
    title: "Hành Trình Kiến Thức",
    description: "Tiếp cận lịch sử qua quy trình...",
    icon: "🎓",
  },
  {
    title: "Chinh Phục Thử Thách",
    description: "Tích lũy điểm kinh nghiệm (XP)...",
    icon: "🏆",
  },
];

function safeGetItem(key) {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function safeSetItem(key, value) {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // ignore
  }
}

export default function OnboardingModal({ slides = DEFAULT_SLIDES, storageKey = STORAGE_KEY }) {
  const totalSteps = slides?.length ?? 0;

  const [isReady, setIsReady] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  const primaryButtonRef = useRef(null);

  const isLastStep = useMemo(() => stepIndex >= totalSteps - 1, [stepIndex, totalSteps]);
  const step = useMemo(() => slides?.[stepIndex], [slides, stepIndex]);

  useEffect(() => {
    const hasSeen = safeGetItem(storageKey) === "true";
    setIsOpen(!hasSeen);
    setIsReady(true);
  }, [storageKey]);

  useEffect(() => {
    if (!isOpen) return;
    setStepIndex(0);
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    primaryButtonRef.current?.focus?.();
  }, [isOpen, stepIndex]);

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
        safeSetItem(storageKey, "true");
        setIsOpen(false);
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [isOpen, storageKey]);

  const close = () => {
    safeSetItem(storageKey, "true");
    setIsOpen(false);
  };

  const next = () => {
    setStepIndex((prev) => Math.min(prev + 1, Math.max(totalSteps - 1, 0)));
  };

  if (!isReady || !isOpen || !step || totalSteps === 0) return null;

  return (
    <div className="fixed inset-0 z-[100]">
      <div
        className="fixed inset-0 bg-background/80 backdrop-blur-sm"
        onClick={close}
        aria-hidden="true"
      />

      <div className="fixed inset-0 overflow-y-auto">
        <div className="flex min-h-full items-center justify-center px-4 py-6">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="onboarding-title"
            aria-describedby="onboarding-description"
            className="relative w-full max-w-lg overflow-hidden rounded-3xl border border-border bg-card/90 backdrop-blur-xl shadow-elegant"
          >
            <div className="absolute -top-16 -right-16 h-56 w-56 rounded-full bg-primary/10 blur-3xl pointer-events-none" />
            <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-full bg-bronze/10 blur-3xl pointer-events-none" />

            <div className="relative p-6 sm:p-8">
              <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-primary/20 to-bronze/10 shadow-xl shadow-primary/10 border border-primary/20">
                <span className="text-4xl" aria-hidden="true">
                  {step.icon}
                </span>
              </div>

              <div key={stepIndex} className="mt-6 text-center animate-in fade-in slide-in-from-bottom-4 duration-300">
                <h2
                  id="onboarding-title"
                  className="text-2xl sm:text-3xl font-display font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-primary to-amber-300"
                >
                  {step.title}
                </h2>
                <p
                  id="onboarding-description"
                  className="mt-3 text-sm sm:text-base leading-relaxed text-muted-foreground text-vietnamese"
                >
                  {step.description}
                </p>
              </div>

              <div className="mt-8 flex items-center justify-between gap-3">
                <button
                  type="button"
                  onClick={close}
                  className="rounded-xl px-3 py-2 text-sm font-semibold text-muted-foreground hover:text-foreground hover:bg-muted/40 transition-colors focus-ring"
                >
                  Skip
                </button>

                <div className="flex items-center gap-2" aria-label="Onboarding progress">
                  {slides.map((_, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setStepIndex(idx)}
                      className={[
                        "h-2.5 w-2.5 rounded-full transition-colors",
                        idx === stepIndex ? "bg-primary" : "bg-muted/60 hover:bg-muted",
                      ].join(" ")}
                      aria-label={`Go to step ${idx + 1}`}
                    />
                  ))}
                </div>

                {isLastStep ? (
                  <button
                    ref={primaryButtonRef}
                    type="button"
                    onClick={close}
                    className="inline-flex items-center justify-center rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors focus-ring"
                  >
                    Done
                  </button>
                ) : (
                  <button
                    ref={primaryButtonRef}
                    type="button"
                    onClick={next}
                    className="inline-flex items-center justify-center rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 transition-colors focus-ring"
                  >
                    Next
                  </button>
                )}
              </div>

              <div className="mt-3 text-center text-xs text-muted-foreground font-medium tabular-nums">
                {stepIndex + 1} / {totalSteps}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
