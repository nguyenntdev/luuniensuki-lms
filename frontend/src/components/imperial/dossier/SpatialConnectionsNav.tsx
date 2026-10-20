"use client";

import Link from "next/link";
import { ArrowLeft, ArrowRight, Compass, MapPin, Navigation } from "lucide-react";
import type { SpatialConnection } from "@/lib/imperial/map-types";

interface SpatialConnectionsNavProps {
  connections: SpatialConnection[];
  currentSiteName: string;
}

export default function SpatialConnectionsNav({
  connections,
  currentSiteName,
}: SpatialConnectionsNavProps) {
  if (!connections || connections.length === 0) {
    return null;
  }

  const prev = connections.find((c) => c.direction === "prev");
  const next = connections.find((c) => c.direction === "next");
  const related = connections.filter((c) => c.direction === "related");

  return (
    <section aria-labelledby="connections-heading" className="space-y-6 pt-4 border-t border-border/80">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <Navigation className="h-5 w-5 text-primary" />
          <h2 id="connections-heading" className="font-display text-xl font-bold tracking-tight text-foreground md:text-2xl">
            Liên hệ không gian & Trục kiến trúc tiếp nối
          </h2>
        </div>
      </div>

      <p className="text-sm text-muted-foreground leading-relaxed">
        Khám phá các công trình tiếp theo dọc theo trục Thần Đạo trung tâm hoặc các cụm không gian liên hoàn trong Đại Nội Huế.
      </p>

      {/* Prev / Next Axis Walk Navigation */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {prev ? (
          <Link
            href={`/dai-noi/cong-trinh/${prev.target_slug}`}
            className="group flex flex-col justify-between rounded-xl border border-border/80 bg-card p-4 transition-all hover:border-primary/50 hover:shadow-md"
          >
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground font-semibold uppercase tracking-wider mb-1">
              <ArrowLeft className="h-3.5 w-3.5 text-primary group-hover:-translate-x-1 transition-transform" />
              <span>Công trình phía trước trên trục</span>
            </div>
            <h3 className="font-display text-base font-bold text-foreground group-hover:text-primary transition-colors">
              {prev.target_name_vi}
            </h3>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              {prev.axis_description}
            </p>
          </Link>
        ) : (
          <div className="rounded-xl border border-dashed border-border/60 p-4 text-xs text-muted-foreground flex items-center justify-center">
            Điểm khởi đầu của trục không gian
          </div>
        )}

        {next ? (
          <Link
            href={`/dai-noi/cong-trinh/${next.target_slug}`}
            className="group flex flex-col justify-between rounded-xl border border-border/80 bg-card p-4 transition-all hover:border-primary/50 hover:shadow-md text-right sm:text-right"
          >
            <div className="flex items-center justify-end gap-1.5 text-xs text-muted-foreground font-semibold uppercase tracking-wider mb-1">
              <span>Công trình tiếp theo trên trục</span>
              <ArrowRight className="h-3.5 w-3.5 text-primary group-hover:translate-x-1 transition-transform" />
            </div>
            <h3 className="font-display text-base font-bold text-foreground group-hover:text-primary transition-colors">
              {next.target_name_vi}
            </h3>
            <p className="mt-1 text-xs text-muted-foreground leading-relaxed">
              {next.axis_description}
            </p>
          </Link>
        ) : (
          <div className="rounded-xl border border-dashed border-border/60 p-4 text-xs text-muted-foreground flex items-center justify-center">
            Điểm kết thúc của trục chính đạo
          </div>
        )}
      </div>

      {/* Related Monuments in same functional space */}
      {related.length > 0 && (
        <div className="rounded-xl bg-secondary/30 p-4 space-y-2 border border-border/60">
          <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            <Compass className="h-3.5 w-3.5 text-primary" />
            <span>Các công trình liên quan cùng cụm không gian:</span>
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            {related.map((rel) => (
              <Link
                key={rel.target_slug}
                href={`/dai-noi/cong-trinh/${rel.target_slug}`}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-medium text-foreground hover:border-primary hover:text-primary transition-colors shadow-sm"
              >
                <MapPin className="h-3 w-3 text-primary" />
                <span>{rel.target_name_vi}</span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
