"use client";

import { Calendar, ShieldCheck, Clock, History, AlertCircle } from "lucide-react";
import type { TimelineEvent } from "@/lib/imperial/map-types";

interface TimelineStatusSectionProps {
  timeline: TimelineEvent[];
  monumentName: string;
}

export default function TimelineStatusSection({
  timeline,
  monumentName,
}: TimelineStatusSectionProps) {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-border p-6 text-center text-sm text-muted-foreground">
        Chưa có dữ liệu biên niên lịch sử thẩm định cho công trình này.
      </div>
    );
  }

  // Sort events chronologically if year exists
  const sorted = [...timeline].sort((a, b) => {
    const ya = typeof a.year === "number" ? a.year : parseInt(String(a.year || "0"), 10) || 0;
    const yb = typeof b.year === "number" ? b.year : parseInt(String(b.year || "0"), 10) || 0;
    return ya - yb;
  });

  return (
    <section aria-labelledby="timeline-heading" className="space-y-6">
      <div className="flex items-center justify-between border-b border-border/70 pb-3">
        <div className="flex items-center gap-2.5">
          <History className="h-5 w-5 text-primary" />
          <h2 id="timeline-heading" className="font-display text-xl font-bold tracking-tight text-foreground md:text-2xl">
            Dòng thời gian biến đổi & Mốc lịch sử
          </h2>
        </div>
        <span className="text-xs text-muted-foreground font-medium">
          {sorted.length} mốc thời gian đã thẩm định
        </span>
      </div>

      <p className="text-sm text-muted-foreground leading-relaxed">
        Diễn tiến niên đại từ khi khởi công, các lần trùng tu dưới triều Nguyễn, tác động của biến cố năm 1947, đến các mốc phục hồi bảo tồn đương đại.
      </p>

      {/* Vertical Timeline Tree */}
      <div className="relative pl-6 sm:pl-8 before:absolute before:bottom-0 before:top-2 before:left-[11px] sm:before:left-[15px] before:w-[2px] before:bg-gradient-to-b before:from-primary before:via-border before:to-muted space-y-8">
        {sorted.map((item, idx) => {
          const isWarDamage =
            String(item.year).includes("1947") ||
            String(item.year).includes("1968") ||
            item.event_title.toLowerCase().includes("hư hại") ||
            item.event_title.toLowerCase().includes("chiến tranh") ||
            item.event_title.toLowerCase().includes("thiêu rụi");

          const isRestoration =
            item.event_title.toLowerCase().includes("trùng tu") ||
            item.event_title.toLowerCase().includes("phục hồi") ||
            item.event_title.toLowerCase().includes("hoàn thành") ||
            item.event_title.toLowerCase().includes("unesco");

          return (
            <div key={idx} className="relative group">
              {/* Timeline Marker Dot */}
              <div
                className={`absolute -left-[30px] sm:-left-[39px] top-1.5 flex h-6 w-6 sm:h-7 sm:w-7 items-center justify-center rounded-full border-2 bg-background shadow-sm transition-transform group-hover:scale-110 ${
                  isWarDamage
                    ? "border-amber-500 text-amber-500"
                    : isRestoration
                    ? "border-sky-500 text-sky-500"
                    : "border-primary text-primary"
                }`}
              >
                {isWarDamage ? (
                  <AlertCircle className="h-3.5 w-3.5" />
                ) : isRestoration ? (
                  <ShieldCheck className="h-3.5 w-3.5" />
                ) : (
                  <Clock className="h-3.5 w-3.5" />
                )}
              </div>

              {/* Content Card */}
              <div className="rounded-xl border border-border/70 bg-card/60 p-4 sm:p-5 transition-shadow hover:shadow-md hover:border-primary/40">
                <div className="flex flex-wrap items-baseline justify-between gap-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-base font-bold text-primary">
                      {item.year || "Thời kỳ"}
                    </span>
                    {item.period_label && (
                      <span className="rounded bg-secondary px-2 py-0.5 text-xs font-semibold text-secondary-foreground">
                        {item.period_label}
                      </span>
                    )}
                  </div>

                  {item.is_verified && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-600 dark:text-emerald-400">
                      <ShieldCheck className="h-3 w-3" />
                      Đã xác thực
                    </span>
                  )}
                </div>

                <h3 className="font-display text-base font-bold text-foreground">
                  {item.event_title}
                </h3>

                <p className="mt-1.5 text-sm text-foreground/85 leading-relaxed">
                  {item.description}
                </p>

                {item.source_ref && (
                  <div className="mt-3 pt-2.5 border-t border-border/40 flex items-center gap-1.5 text-xs text-muted-foreground font-mono">
                    <span className="font-semibold text-foreground/70">Nguồn trích:</span>
                    <span className="truncate">{item.source_ref}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
