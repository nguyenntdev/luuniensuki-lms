"use client";

import React, { useState } from "react";
import {
  BookOpen,
  ScrollText,
  HelpCircle,
  AlertTriangle,
  Info,
  Sparkles,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { ImperialBadge } from "./ImperialBadge";

export type CalloutType =
  | "evidence"
  | "guiding_question"
  | "uncertainty"
  | "warning"
  | "info";

export interface CalloutBoxProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "title"> {
  type?: CalloutType;
  title?: React.ReactNode;
  question?: string;
  source?: string;
  citation?: string;
  archivalUnit?: string;
  epistemicStatus?: "verified" | "probable" | "disputed" | "uncertain";
  icon?: React.ReactNode;
  action?: React.ReactNode;
  collapsible?: boolean;
  defaultOpen?: boolean;
}

const TYPE_CONFIG = {
  evidence: {
    borderColor: "border-ln-blue/40",
    bgGradient: "bg-gradient-to-br from-ln-blue/5 via-ln-surface to-ln-surface-muted/30",
    accentBorder: "border-l-4 border-l-ln-blue",
    iconBg: "bg-ln-blue/15 text-ln-blue",
    defaultIcon: ScrollText,
    defaultLabel: "Chứng cứ lịch sử & Nguồn sơ cấp",
    badgeVariant: "blue" as const,
  },
  guiding_question: {
    borderColor: "border-ln-gold/50",
    bgGradient: "bg-gradient-to-br from-ln-gold/10 via-ln-surface to-ln-bg-soft",
    accentBorder: "border-l-4 border-l-ln-gold",
    iconBg: "bg-ln-gold/20 text-ln-gold",
    defaultIcon: Sparkles,
    defaultLabel: "Câu hỏi dẫn dắt nghiên cứu",
    badgeVariant: "gold" as const,
  },
  uncertainty: {
    borderColor: "border-ln-red/40",
    bgGradient: "bg-gradient-to-br from-ln-red/8 via-ln-surface to-ln-surface-muted/30",
    accentBorder: "border-l-4 border-l-ln-red",
    iconBg: "bg-ln-red/15 text-ln-red",
    defaultIcon: AlertTriangle,
    defaultLabel: "Lưu ý kiểm chứng & Nghi vấn sử liệu",
    badgeVariant: "vermilion" as const,
  },
  warning: {
    borderColor: "border-ln-red/45",
    bgGradient: "bg-gradient-to-br from-ln-red/10 via-ln-surface to-ln-surface-muted/40",
    accentBorder: "border-l-4 border-l-ln-red",
    iconBg: "bg-ln-red/15 text-ln-red",
    defaultIcon: AlertTriangle,
    defaultLabel: "Cảnh báo bảo tồn & Hiện trạng",
    badgeVariant: "vermilion" as const,
  },
  info: {
    borderColor: "border-ln-border-strong/50",
    bgGradient: "bg-gradient-to-br from-ln-surface-muted/40 via-ln-surface to-ln-bg-soft",
    accentBorder: "border-l-4 border-l-ln-border-strong",
    iconBg: "bg-ln-surface-muted text-ln-ink-muted",
    defaultIcon: Info,
    defaultLabel: "Ghi chú tư liệu học thuật",
    badgeVariant: "ink" as const,
  },
};

export function CalloutBox({
  type = "info",
  title,
  question,
  source,
  citation,
  archivalUnit,
  epistemicStatus,
  icon,
  action,
  collapsible = false,
  defaultOpen = true,
  className,
  children,
  ...props
}: CalloutBoxProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [copied, setCopied] = useState(false);

  const config = TYPE_CONFIG[type] || TYPE_CONFIG.info;
  const DefaultIcon = config.defaultIcon;

  const handleCopyCitation = () => {
    const citationText = citation || (typeof children === "string" ? children : "");
    const fullText = source
      ? `[Trích nguồn: ${source}${archivalUnit ? ` — ${archivalUnit}` : ""}] "${citationText}"`
      : citationText;

    if (navigator?.clipboard) {
      navigator.clipboard.writeText(fullText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const epistemicBadgeText = epistemicStatus === "verified"
    ? "Đã xác thực"
    : epistemicStatus === "probable"
    ? "Khả tín cao"
    : epistemicStatus === "disputed"
    ? "Còn tranh luận"
    : epistemicStatus === "uncertain"
    ? "Chưa xác minh"
    : null;

  return (
    <aside
      className={cn(
        "relative rounded-xl border p-5 sm:p-6 transition-all duration-200",
        config.borderColor,
        config.bgGradient,
        config.accentBorder,
        "shadow-[0_4px_16px_-4px_rgba(42,36,29,0.06)] dark:shadow-[0_4px_16px_-4px_rgba(0,0,0,0.4)]",
        className,
      )}
      {...props}
    >
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ln-border/60 pb-3">
        <div className="flex items-center gap-2.5">
          <span
            className={cn(
              "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg shadow-xs",
              config.iconBg,
            )}
          >
            {icon ? icon : <DefaultIcon className="h-4 w-4" />}
          </span>

          <div className="flex items-center gap-2">
            <ImperialBadge
              variant={config.badgeVariant}
              size="xs"
              appearance="subtle"
            >
              {config.defaultLabel}
            </ImperialBadge>

            {epistemicBadgeText && (
              <ImperialBadge
                variant={
                  epistemicStatus === "verified"
                    ? "green"
                    : epistemicStatus === "disputed" || epistemicStatus === "uncertain"
                    ? "vermilion"
                    : "gold"
                }
                size="xs"
                appearance="outline"
                dot
              >
                {epistemicBadgeText}
              </ImperialBadge>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {action}

          {(citation || source) && (
            <button
              type="button"
              onClick={handleCopyCitation}
              aria-label="Sao chép trích dẫn nguồn"
              title="Sao chép trích dẫn"
              className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs text-ln-ink-muted hover:bg-ln-surface-muted hover:text-ln-ink transition-colors"
            >
              {copied ? (
                <>
                  <Check className="h-3.5 w-3.5 text-ln-green" />
                  <span className="text-ln-green font-medium">Đã chép</span>
                </>
              ) : (
                <>
                  <Copy className="h-3.5 w-3.5" />
                  <span>Chép nguồn</span>
                </>
              )}
            </button>
          )}

          {collapsible && (
            <button
              type="button"
              onClick={() => setIsOpen(!isOpen)}
              aria-label={isOpen ? "Thu gọn hộp thoại" : "Mở rộng hộp thoại"}
              className="rounded-md p-1 text-ln-ink-muted hover:bg-ln-surface-muted hover:text-ln-ink transition-colors"
            >
              {isOpen ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      {isOpen && (
        <div className="mt-4 space-y-3">
          {/* Custom title if provided */}
          {title && (
            <h4 className="font-serif font-bold text-base sm:text-lg text-ln-ink leading-snug">
              {title}
            </h4>
          )}

          {/* Guiding Question display */}
          {question && (
            <div className="rounded-lg border border-ln-gold/30 bg-ln-surface/80 p-4 shadow-inner">
              <p className="text-[11px] font-bold uppercase tracking-wider text-ln-gold mb-1">
                Vấn đề cốt lõi / Nghi vấn trọng tâm:
              </p>
              <h3 className="font-serif text-lg sm:text-xl font-bold italic text-ln-ink leading-relaxed">
                &ldquo;{question}&rdquo;
              </h3>
            </div>
          )}

          {/* Direct Citation block */}
          {citation && (
            <blockquote className="rounded-lg border-l-2 border-ln-blue/60 bg-ln-bg-soft/70 px-4 py-3 text-sm italic text-ln-ink leading-relaxed">
              &ldquo;{citation}&rdquo;
            </blockquote>
          )}

          {/* Body Content */}
          {children && (
            <div className="text-xs sm:text-sm text-ln-ink leading-relaxed space-y-2">
              {children}
            </div>
          )}

          {/* Source Attribution Footer */}
          {(source || archivalUnit) && (
            <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-ln-border/40 text-xs text-ln-ink-muted">
              {source && (
                <div className="flex items-center gap-1.5 font-medium">
                  <BookOpen className="h-3.5 w-3.5 text-ln-ink-muted/80 shrink-0" />
                  <span>Xuất xứ: {source}</span>
                </div>
              )}
              {archivalUnit && (
                <span className="italic text-[11px]">
                  Cơ quan bảo quản: {archivalUnit}
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </aside>
  );
}
