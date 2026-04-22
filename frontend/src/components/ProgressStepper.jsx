"use client";

import { Check, Lock, Eye, BookOpen, Trophy } from "lucide-react";

/**
 * ProgressStepper - Visual progress indicator for motif learning
 *
 * Shows 3 steps: Khám Phá (discovered), Bài Học (learned), Trắc Nghiệm (mastered)
 * Each step shows XP reward and current completion status
 */

const STEPS = [
    {
        key: "discovered",
        label: "Khám Phá",
        labelEn: "Discover",
        xp: 25,
        icon: Eye,
        description: "Tìm thấy họa tiết",
    },
    {
        key: "learned",
        label: "Bài Học",
        labelEn: "Lesson",
        xp: 50,
        icon: BookOpen,
        description: "Hoàn thành bài học",
    },
    {
        key: "mastered",
        label: "Trắc Nghiệm",
        labelEn: "Quiz",
        xp: 75,
        icon: Trophy,
        description: "Đạt điểm cao trong quiz",
    },
];

// Map status to step index
const STATUS_TO_STEP = {
    hidden: -1,
    discovered: 0,
    learned: 1,
    mastered: 2,
};

export default function ProgressStepper({
    status = "hidden",
    compact = false,
    showXP = true,
    className = ""
}) {
    const currentStepIndex = STATUS_TO_STEP[status] ?? -1;

    return (
        <div className={`w-full ${className}`}>
            <div className="flex items-center justify-between">
                {STEPS.map((step, index) => {
                    const isCompleted = index <= currentStepIndex;
                    const isCurrent = index === currentStepIndex + 1;
                    const isLocked = index > currentStepIndex + 1;
                    const StepIcon = step.icon;

                    return (
                        <div key={step.key} className="flex items-center flex-1">
                            {/* Step Circle */}
                            <div className="flex flex-col items-center">
                                <div
                                    className={[
                                        "relative flex items-center justify-center rounded-full border-2 transition-all duration-300",
                                        compact ? "w-8 h-8" : "w-10 h-10",
                                        isCompleted
                                            ? "bg-primary border-primary text-primary-foreground"
                                            : isCurrent
                                            ? "bg-primary/10 border-primary text-primary animate-pulse"
                                            : "bg-muted border-border text-muted-foreground",
                                    ].join(" ")}
                                >
                                    {isCompleted ? (
                                        <Check className={compact ? "w-4 h-4" : "w-5 h-5"} />
                                    ) : isLocked ? (
                                        <Lock className={compact ? "w-3 h-3" : "w-4 h-4"} />
                                    ) : (
                                        <StepIcon className={compact ? "w-4 h-4" : "w-5 h-5"} />
                                    )}
                                </div>

                                {/* Step Label */}
                                {!compact && (
                                    <div className="mt-2 text-center">
                                        <div
                                            className={[
                                                "text-xs font-medium whitespace-nowrap",
                                                isCompleted
                                                    ? "text-primary"
                                                    : isCurrent
                                                    ? "text-foreground"
                                                    : "text-muted-foreground",
                                            ].join(" ")}
                                        >
                                            {step.label}
                                        </div>
                                        {showXP && (
                                            <div
                                                className={[
                                                    "text-[10px] mt-0.5",
                                                    isCompleted
                                                        ? "text-primary/70"
                                                        : "text-muted-foreground/70",
                                                ].join(" ")}
                                            >
                                                +{step.xp} XP
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Connecting Line */}
                            {index < STEPS.length - 1 && (
                                <div
                                    className={[
                                        "flex-1 h-0.5 mx-2",
                                        compact ? "mx-1" : "mx-3",
                                        index < currentStepIndex
                                            ? "bg-primary"
                                            : index === currentStepIndex
                                            ? "bg-gradient-to-r from-primary to-border"
                                            : "bg-border",
                                    ].join(" ")}
                                />
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Compact mode tooltip hint */}
            {compact && (
                <div className="mt-1 text-center">
                    <span className="text-[10px] text-muted-foreground">
                        {currentStepIndex >= 2
                            ? "Đã thành thạo! 🎉"
                            : currentStepIndex >= 1
                            ? "Hoàn thành quiz để thành thạo"
                            : currentStepIndex >= 0
                            ? "Đọc bài học để tiếp tục"
                            : "Khám phá để bắt đầu"}
                    </span>
                </div>
            )}
        </div>
    );
}

// Compact inline version for lists
export function ProgressStepperInline({ status = "hidden", className = "" }) {
    const currentStepIndex = STATUS_TO_STEP[status] ?? -1;

    return (
        <div className={`flex items-center gap-1 ${className}`}>
            {STEPS.map((step, index) => {
                const isCompleted = index <= currentStepIndex;

                return (
                    <div
                        key={step.key}
                        className={[
                            "w-2 h-2 rounded-full transition-colors",
                            isCompleted ? "bg-primary" : "bg-border",
                        ].join(" ")}
                        title={`${step.label}: ${isCompleted ? "Hoàn thành" : "Chưa hoàn thành"}`}
                    />
                );
            })}
        </div>
    );
}

// Progress bar version
export function ProgressBar({ status = "hidden", className = "" }) {
    const currentStepIndex = STATUS_TO_STEP[status] ?? -1;
    const progressPercent = ((currentStepIndex + 1) / STEPS.length) * 100;

    return (
        <div className={`w-full ${className}`}>
            <div className="h-1.5 bg-border rounded-full overflow-hidden">
                <div
                    className="h-full bg-primary rounded-full transition-all duration-500"
                    style={{ width: `${Math.max(0, progressPercent)}%` }}
                />
            </div>
        </div>
    );
}
