"use client";

import { useEffect, useState } from "react";
import { useDailyMissionsStore } from "@/stores/dailyMissionsStore";
import { useAuthStore } from "@/stores/authStore";
import Skeleton from "@/components/Skeleton";

interface Mission {
  name: string;
  description?: string;
  mission_type?: string;
  target_count: number;
  xp_reward: number;
}

interface UserMission {
  id: string | number;
  mission: Mission;
  progress_percentage?: number;
  is_completed?: boolean;
  current_count: number;
}

const MISSION_TYPE_ICONS: Record<string, string> = {
  lesson: "📚",
  quiz: "✍️",
  discovery: "🔍",
  streak: "🔥",
  exam: "🎓",
  practice: "💪",
};

const MISSION_TYPE_COLORS: Record<string, string> = {
  lesson: "text-blue-600",
  quiz: "text-purple-600",
  discovery: "text-green-600",
  streak: "text-orange-600",
  exam: "text-red-600",
  practice: "text-indigo-600",
};

export default function DailyMissionsCard() {
  const status = useAuthStore((s) => s.status);
  const missions = useDailyMissionsStore((s) => s.missions);
  const loading = useDailyMissionsStore((s) => s.loading);
  const error = useDailyMissionsStore((s) => s.error);
  const totalXpToday = useDailyMissionsStore((s) => s.totalXpToday);
  const completedCount = useDailyMissionsStore((s) => s.completedCount);
  const totalCount = useDailyMissionsStore((s) => s.totalCount);
  const fetchMissions = useDailyMissionsStore((s) => s.fetchMissions);
  const getTimeUntilMidnight = useDailyMissionsStore(
    (s) => s.getTimeUntilMidnight
  );

  const [timeRemaining, setTimeRemaining] = useState<{ hours: number; minutes: number }>({ hours: 0, minutes: 0 });

  useEffect(() => {
    if (status === "authed") {
      fetchMissions();
    }
  }, [status, fetchMissions]);

  useEffect(() => {
    const updateTimer = () => {
      const time = getTimeUntilMidnight();
      setTimeRemaining({ hours: time.hours, minutes: time.minutes });
    };

    updateTimer();
    const interval = setInterval(updateTimer, 60000);
    return () => clearInterval(interval);
  }, [getTimeUntilMidnight]);

  if (status !== "authed") return null;

  return (
    <div className="rounded-2xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-baseline justify-between">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Nhiệm vụ hàng ngày
          </div>
          <div className="mt-1 text-lg font-display font-semibold text-foreground">
            {loading ? (
              <Skeleton className="h-4 w-32" />
            ) : (
              `${completedCount}/${totalCount} hoàn thành`
            )}
          </div>
        </div>
        {!loading && (
          <div className="text-right">
            <div className="text-xs text-muted-foreground">
              Làm mới sau
            </div>
            <div className="text-sm font-display font-semibold text-foreground tabular-nums">
              {timeRemaining.hours}h {timeRemaining.minutes}m
            </div>
          </div>
        )}
      </div>

      {error ? (
        <div className="mt-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
          {error}
        </div>
      ) : null}

      {loading ? (
        <div className="mt-4 space-y-3">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : missions.length > 0 ? (
        <div className="mt-4 space-y-3">
          {(missions as unknown as UserMission[]).map((userMission) => {
            const mission = userMission.mission;
            const missionType = mission.mission_type || "lesson";
            const icon = MISSION_TYPE_ICONS[missionType] || "📝";
            const colorClass = MISSION_TYPE_COLORS[missionType] || "text-gray-600";
            const progressPercent = userMission.progress_percentage || 0;
            const isCompleted = userMission.is_completed;

            return (
              <div
                key={userMission.id}
                className={`rounded-xl border ${
                  isCompleted
                    ? "border-green-200 bg-green-50/50"
                    : "border-border bg-secondary/30"
                } p-4 transition-all`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="text-2xl">{icon}</div>
                    <div className="flex-1 min-w-0">
                      <div
                        className={`text-sm font-semibold ${
                          isCompleted ? "text-green-700" : "text-foreground"
                        }`}
                      >
                        {mission.name}
                      </div>
                      <div
                        className={`mt-1 text-xs ${
                          isCompleted ? "text-green-600" : "text-muted-foreground"
                        }`}
                      >
                        {mission.description}
                      </div>
                      <div className="mt-2 flex items-center gap-2">
                        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                          <div
                            className={`h-full transition-all ${
                              isCompleted ? "bg-green-500" : "bg-primary"
                            }`}
                            style={{ width: `${progressPercent}%` }}
                          />
                        </div>
                        <div className="text-xs font-display tabular-nums text-muted-foreground">
                          {userMission.current_count}/{mission.target_count}
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="text-right flex flex-col items-end gap-1">
                    <div className={`text-sm font-semibold ${colorClass}`}>
                      +{mission.xp_reward} XP
                    </div>
                    {isCompleted && (
                      <div className="text-xs font-semibold text-green-600">
                        ✓ Đã hoàn thành
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="mt-4 text-sm text-muted-foreground text-center py-6">
          Không có nhiệm vụ nào hôm nay.
        </div>
      )}

      {totalXpToday > 0 && !loading && (
        <div className="mt-4 pt-4 border-t border-border">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold text-muted-foreground">
              Tổng XP hôm nay
            </div>
            <div className="text-lg font-display font-bold text-primary">
              +{totalXpToday} XP
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

