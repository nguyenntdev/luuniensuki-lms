"use client";

import { useEffect, useState } from "react";
import { getDailyGoal, updateDailyGoal } from "@/lib/api";
import useDailyGoalStore, {
  GOAL_LEVELS,
  type GoalLevelKey,
} from "@/stores/dailyGoalStore";
import { useAuthStore } from "@/stores/authStore";

export default function DailyGoalCard() {
  const user = useAuthStore((s) => s.user);
  const {
    goalLevel,
    currentXp,
    isCompleted,
    getGoalConfig,
    getProgressPercentage,
    getRemainingXp,
    getTimeUntilMidnight,
    setGoalLevel,
    resetIfNeeded,
  } = useDailyGoalStore();

  const [showGoalSelector, setShowGoalSelector] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);
  const [timeRemaining, setTimeRemaining] = useState<{ hours: number; minutes: number }>({ hours: 0, minutes: 0 });

  useEffect(() => {
    resetIfNeeded();
  }, [resetIfNeeded]);

  useEffect(() => {
    let cancelled = false;

    async function syncGoalLevelFromServer() {
      if (!user) return;
      try {
        const response = (await getDailyGoal()) as { goal_level?: string };
        if (cancelled) return;

        const serverLevel = String(
          response?.goal_level || ""
        ).toUpperCase() as GoalLevelKey;
        if (GOAL_LEVELS[serverLevel] && serverLevel !== goalLevel) {
          setGoalLevel(serverLevel);
        }
      } catch {
        // Keep local store value when API is unavailable.
      }
    }

    syncGoalLevelFromServer();

    return () => {
      cancelled = true;
    };
  }, [user, goalLevel, setGoalLevel]);

  useEffect(() => {
    const updateTime = () => {
      const time = getTimeUntilMidnight();
      setTimeRemaining(time);
    };
    updateTime();
    const interval = setInterval(updateTime, 60000);
    return () => clearInterval(interval);
  }, [getTimeUntilMidnight]);

  useEffect(() => {
    if (isCompleted && !showCelebration) {
      setShowCelebration(true);
      setTimeout(() => setShowCelebration(false), 3000);
    }
  }, [isCompleted, showCelebration]);

  const goalConfig = getGoalConfig();
  const progressPercentage = getProgressPercentage();
  const remainingXp = getRemainingXp();

  const handleGoalChange = (level: string) => {
    setGoalLevel(level as GoalLevelKey);
    setShowGoalSelector(false);

    if (user) {
      updateDailyGoal(level).catch(() => null);
    }
  };

  return (
    <div className="bg-card rounded-xl shadow-lg overflow-hidden">
      {showCelebration && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-fade-in">
          <div className="bg-gradient-to-br from-yellow-400 to-orange-500 p-8 rounded-3xl shadow-2xl transform scale-95 animate-bounce-in text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h3 className="text-2xl font-bold text-white mb-2">Chúc mừng!</h3>
            <p className="text-white text-lg">
              Bạn đã hoàn thành mục tiêu hôm nay
            </p>
            <div className="mt-4 text-yellow-100 text-sm">+20 Gems</div>
          </div>
        </div>
      )}

      <div className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-bold text-foreground">
              Mục Tiêu Hôm Nay
            </h3>
            <p className="text-sm text-muted-foreground">
              Còn {timeRemaining.hours}h {timeRemaining.minutes}m
            </p>
          </div>
          <button
            onClick={() => setShowGoalSelector(!showGoalSelector)}
            className="text-2xl hover:scale-110 transition-transform"
            title="Đổi mục tiêu"
          >
            {goalConfig.emoji}
          </button>
        </div>

        <div className="relative flex items-center justify-center mb-4">
          <svg className="w-40 h-40 transform -rotate-90">
            <circle
              cx="80"
              cy="80"
              r="70"
              stroke="currentColor"
              strokeWidth="10"
              fill="none"
              className="text-muted"
            />
            <circle
              cx="80"
              cy="80"
              r="70"
              stroke="currentColor"
              strokeWidth="10"
              fill="none"
              strokeDasharray={`${2 * Math.PI * 70}`}
              strokeDashoffset={`${2 * Math.PI * 70 * (1 - progressPercentage / 100)}`}
              className={`transition-all duration-500 ${
                isCompleted
                  ? "text-success"
                  : progressPercentage >= 80
                    ? "text-primary"
                    : "text-info"
              }`}
              strokeLinecap="round"
            />
          </svg>

          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <div className="text-3xl font-bold text-foreground">
              {currentXp}
              <span className="text-xl text-muted-foreground">
                /{goalConfig.xp}
              </span>
            </div>
            <div className="text-sm text-muted-foreground">XP</div>
          </div>
        </div>

        <div className="text-center mb-4">
          {isCompleted ? (
            <div className="flex items-center justify-center gap-2 text-success font-semibold">
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <span>Hoàn thành!</span>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              Còn{" "}
              <span className="font-semibold text-primary">
                {remainingXp} XP
              </span>{" "}
              nữa
            </p>
          )}
        </div>

        {showGoalSelector && (
          <div className="border-t border-border pt-4 space-y-2">
            <p className="text-sm font-semibold text-foreground mb-3">
              Chọn mục tiêu:
            </p>
            {Object.entries(GOAL_LEVELS).map(([key, config]) => (
              <button
                key={key}
                onClick={() => handleGoalChange(key)}
                className={`w-full flex items-center justify-between p-3 rounded-lg border-2 transition-all ${
                  goalLevel === key
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-primary/50"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{config.emoji}</span>
                  <div className="text-left">
                    <div className="font-semibold text-foreground">
                      {config.name}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {config.description}
                    </div>
                  </div>
                </div>
                {goalLevel === key && (
                  <svg
                    className="w-5 h-5 text-primary"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
