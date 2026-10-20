"use client";

import React, { useCallback, useId, useMemo, useState } from "react";
import {
  Compass,
  Clock,
  BookOpen,
  Scale,
  Award,
  Sparkles,
  HelpCircle,
} from "lucide-react";
import {
  calculateRubricScore,
  RUBRIC_METADATA,
  normalizeScoreKeys,
  type RubricScoresInput,
  type RubricRawScores,
  type RubricCriterionKey,
} from "@/lib/imperial/rubric-engine";
import { cn } from "@/lib/utils";

// =========================================================================== //
// Props Interface
// =========================================================================== //

export interface RubricRadarChartProps {
  /** Student's rubric scores (s1-s4 or s1_spatial-s4_argument) */
  studentScores: RubricScoresInput;
  /** Reference benchmark level (e.g., GDPT 2018 grade-level target). Default: 2.5 or 3.0 */
  benchmarkScores?: RubricScoresInput;
  /** Maximum score per criterion (commonly 3 or 4). Default: 3 */
  maxScore?: number;
  /** Custom label for student polygon in legend. Default: "Bài làm của học sinh" */
  studentLabel?: string;
  /** Custom label for benchmark polygon. Default: "Chuẩn đầu ra GDPT 2018" */
  benchmarkLabel?: string;
  /** Title of the radar visualization */
  title?: string;
  /** Subtitle or explanatory note */
  subtitle?: string;
  /** Show legend badges below chart. Default: true */
  showLegend?: boolean;
  /** Show quantitative score badge summary. Default: true */
  showScoreSummary?: boolean;
  /** Custom additional className for the wrapper */
  className?: string;
}

// Axis layout definitions (Diamond layout: top, right, bottom, left)
const AXES_CONFIG: Array<{
  key: RubricCriterionKey;
  id: "S1" | "S2" | "S3" | "S4";
  icon: typeof Compass;
  dx: number;
  dy: number;
  textAnchor: "middle" | "start" | "end";
  labelPosition: "top" | "right" | "bottom" | "left";
}> = [
  {
    key: "s1",
    id: "S1",
    icon: Compass,
    dx: 0,
    dy: -1,
    textAnchor: "middle",
    labelPosition: "top",
  },
  {
    key: "s2",
    id: "S2",
    icon: Clock,
    dx: 1,
    dy: 0,
    textAnchor: "start",
    labelPosition: "right",
  },
  {
    key: "s3",
    id: "S3",
    icon: BookOpen,
    dx: 0,
    dy: 1,
    textAnchor: "middle",
    labelPosition: "bottom",
  },
  {
    key: "s4",
    id: "S4",
    icon: Scale,
    dx: -1,
    dy: 0,
    textAnchor: "end",
    labelPosition: "left",
  },
];

// Default target benchmark (Good / Proficient level: 2.5 on 0-3 scale, or 3.0 on 0-4 scale)
function getDefaultBenchmark(max: number): RubricRawScores {
  const target = max >= 4 ? 3.0 : 2.5;
  return { s1: target, s2: target, s3: target, s4: target };
}

/**
 * Pure SVG 4-Axis Pedagogical Radar Chart
 *
 * Visualizes student competency profile versus target benchmark level
 * across S1 (Spatial), S2 (Temporal), S3 (Evidence), and S4 (Argument & Epistemic Humility).
 *
 * Fully accessible with ARIA description and screen-reader summary table.
 */
export default function RubricRadarChart({
  studentScores,
  benchmarkScores,
  maxScore = 3,
  studentLabel = "Hồ sơ năng lực học sinh",
  benchmarkLabel = "Chuẩn đầu ra GDPT 2018",
  title = "Biểu đồ Năng lực Khảo sát Lịch sử (Rubric S1–S4)",
  subtitle = "Đối chiếu kết quả đạt được so với chuẩn năng lực lịch sử THPT",
  showLegend = true,
  showScoreSummary = true,
  className,
}: RubricRadarChartProps) {
  const chartId = useId();
  const titleId = `radar-title-${chartId}`;
  const descId = `radar-desc-${chartId}`;

  const [activeCriterion, setActiveCriterion] = useState<RubricCriterionKey | null>(null);

  // Normalize scores
  const student = useMemo(() => normalizeScoreKeys(studentScores), [studentScores]);
  const benchmark = useMemo(() => {
    return benchmarkScores
      ? normalizeScoreKeys(benchmarkScores)
      : getDefaultBenchmark(maxScore);
  }, [benchmarkScores, maxScore]);

  // Overall calculation
  const calc = useMemo(() => {
    return calculateRubricScore(student, undefined, { maxScorePerCriterion: maxScore });
  }, [student, maxScore]);

  // SVG Geometry Dimensions
  const size = 380;
  const cx = size / 2;
  const cy = size / 2;
  const radius = 110; // Max radius for outer boundary

  // Calculate coordinates for a given score on an axis
  const getPoint = useCallback((dx: number, dy: number, score: number) => {
    const clampedScore = Math.max(0, Math.min(score, maxScore));
    const factor = maxScore > 0 ? (clampedScore / maxScore) * radius : 0;
    return {
      x: cx + dx * factor,
      y: cy + dy * factor,
    };
  }, [cx, cy, maxScore, radius]);

  // Build polygon path string from 4 axes
  const getPolygonPoints = useCallback((scores: RubricRawScores): string => {
    return AXES_CONFIG.map(({ key, dx, dy }) => {
      const pt = getPoint(dx, dy, scores[key]);
      return `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`;
    }).join(" ");
  }, [getPoint]);

  const studentPolygon = useMemo(() => getPolygonPoints(student), [student, getPolygonPoints]);
  const benchmarkPolygon = useMemo(() => getPolygonPoints(benchmark), [benchmark, getPolygonPoints]);

  // Concentric Grid Levels (e.g. 1, 2, 3 or 1, 2, 3, 4)
  const gridLevels = useMemo(() => {
    const levels = [];
    const step = maxScore <= 4 ? 1 : Math.ceil(maxScore / 4);
    for (let s = step; s <= maxScore; s += step) {
      const pts = AXES_CONFIG.map(({ dx, dy }) => {
        const pt = getPoint(dx, dy, s);
        return `${pt.x.toFixed(1)},${pt.y.toFixed(1)}`;
      }).join(" ");
      levels.push({ score: s, points: pts });
    }
    return levels;
  }, [maxScore, getPoint]);

  // Color mapping by classification
  const classificationColor = useMemo(() => {
    switch (calc.classification) {
      case "Xuất sắc":
        return "text-amber-500 bg-amber-500/15 border-amber-500/30";
      case "Giỏi":
        return "text-emerald-500 bg-emerald-500/15 border-emerald-500/30";
      case "Khá":
        return "text-blue-500 bg-blue-500/15 border-blue-500/30";
      case "Đạt":
        return "text-yellow-600 bg-yellow-500/15 border-yellow-500/30";
      default:
        return "text-rose-500 bg-rose-500/15 border-rose-500/30";
    }
  }, [calc.classification]);

  return (
    <figure
      className={cn(
        "rounded-2xl border border-border/80 bg-card/90 p-5 shadow-md flex flex-col items-center",
        className,
      )}
      aria-labelledby={titleId}
    >
      {/* Header Info */}
      <div className="w-full text-center space-y-1 mb-2">
        <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-primary/10 text-primary border border-primary/20">
          <Award className="size-3" />
          <span>Hồ Sơ Năng Lực Lịch Sử</span>
        </div>
        <h3 id={titleId} className="font-serif font-bold text-base sm:text-lg text-foreground">
          {title}
        </h3>
        {subtitle && (
          <p id={descId} className="text-xs text-muted-foreground max-w-md mx-auto">
            {subtitle}
          </p>
        )}
      </div>

      {/* Pure SVG 4-Axis Radar Graphic */}
      <div className="relative w-full max-w-[360px] aspect-square flex items-center justify-center my-1">
        <svg
          viewBox={`0 0 ${size} ${size}`}
          className="w-full h-full overflow-visible select-none"
          role="img"
          aria-labelledby={`${titleId} ${descId}`}
        >
          <title>{title}</title>
          <desc>
            {`Biểu đồ radar 4 trục: S1 Không gian: ${student.s1}/${maxScore}, S2 Thời gian: ${student.s2}/${maxScore}, S3 Sử liệu: ${student.s3}/${maxScore}, S4 Lập luận: ${student.s4}/${maxScore}. Xếp loại: ${calc.classification}.`}
          </desc>

          {/* Concentric Grid Polygons */}
          {gridLevels.map((lvl) => (
            <g key={lvl.score}>
              <polygon
                points={lvl.points}
                fill="none"
                stroke="currentColor"
                strokeWidth="1"
                className="text-border/80 stroke-dasharray-[2,2]"
                strokeDasharray="3 3"
              />
              {/* Level Score Label along the top-right quadrant */}
              <text
                x={cx + 6}
                y={cy - (lvl.score / maxScore) * radius + 4}
                className="fill-muted-foreground/70 font-mono text-[10px]"
                textAnchor="start"
              >
                {lvl.score}đ
              </text>
            </g>
          ))}

          {/* Central Axes Lines */}
          {AXES_CONFIG.map(({ key, dx, dy }) => (
            <line
              key={key}
              x1={cx}
              y1={cy}
              x2={cx + dx * radius}
              y2={cy + dy * radius}
              stroke="currentColor"
              strokeWidth="1.2"
              className={cn(
                "transition-colors",
                activeCriterion === key ? "text-primary" : "text-border",
              )}
            />
          ))}

          {/* Benchmark Polygon (Dashed Blue / Slate) */}
          <polygon
            points={benchmarkPolygon}
            fill="rgba(59, 130, 246, 0.08)"
            stroke="#3b82f6"
            strokeWidth="1.75"
            strokeDasharray="4 3"
            className="transition-all duration-300"
          />

          {/* Benchmark Markers */}
          {AXES_CONFIG.map(({ key, dx, dy }) => {
            const pt = getPoint(dx, dy, benchmark[key]);
            return (
              <circle
                key={`bench-${key}`}
                cx={pt.x}
                cy={pt.y}
                r="3"
                fill="#3b82f6"
                className="opacity-75"
              />
            );
          })}

          {/* Student Profile Polygon (Golden Amber / Brand Primary) */}
          <polygon
            points={studentPolygon}
            fill="rgba(245, 158, 11, 0.22)"
            stroke="#d97706"
            strokeWidth="2.5"
            className="transition-all duration-300 filter drop-shadow-sm"
          />

          {/* Student Profile Markers & Interactive Touch Targets */}
          {AXES_CONFIG.map(({ key, id, dx, dy }) => {
            const pt = getPoint(dx, dy, student[key]);
            const isHovered = activeCriterion === key;
            return (
              <g
                key={`stu-${key}`}
                className="cursor-pointer"
                onMouseEnter={() => setActiveCriterion(key)}
                onMouseLeave={() => setActiveCriterion(null)}
                onClick={() => setActiveCriterion(activeCriterion === key ? null : key)}
              >
                {/* Glow ring on hover */}
                {isHovered && (
                  <circle
                    cx={pt.x}
                    cy={pt.y}
                    r="9"
                    fill="none"
                    stroke="#d97706"
                    strokeWidth="2"
                    strokeOpacity="0.5"
                    className="animate-pulse"
                  />
                )}
                {/* Core marker circle */}
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r="5"
                  fill="#ffffff"
                  stroke="#d97706"
                  strokeWidth="2.5"
                  className="transition-transform duration-150 hover:scale-125"
                />
                {/* Score badge next to point */}
                <text
                  x={pt.x + (dx !== 0 ? dx * 12 : 10)}
                  y={pt.y + (dy !== 0 ? dy * 12 : -6)}
                  className="fill-foreground font-mono font-bold text-[11px]"
                  textAnchor={dx > 0 ? "start" : dx < 0 ? "end" : "middle"}
                >
                  {student[key]}đ
                </text>
              </g>
            );
          })}

          {/* Outer Axis Labels */}
          {/* S1: Top */}
          <g
            className="cursor-pointer select-none"
            onClick={() => setActiveCriterion(activeCriterion === "s1" ? null : "s1")}
          >
            <text
              x={cx}
              y={cy - radius - 26}
              textAnchor="middle"
              className={cn(
                "font-serif font-bold text-xs transition-colors",
                activeCriterion === "s1" ? "fill-primary" : "fill-foreground",
              )}
            >
              S1 • Không gian
            </text>
            <text
              x={cx}
              y={cy - radius - 12}
              textAnchor="middle"
              className="fill-muted-foreground text-[10px]"
            >
              (Spatial Reasoning)
            </text>
          </g>

          {/* S2: Right */}
          <g
            className="cursor-pointer select-none"
            onClick={() => setActiveCriterion(activeCriterion === "s2" ? null : "s2")}
          >
            <text
              x={cx + radius + 14}
              y={cy - 4}
              textAnchor="start"
              className={cn(
                "font-serif font-bold text-xs transition-colors",
                activeCriterion === "s2" ? "fill-primary" : "fill-foreground",
              )}
            >
              S2 • Thời gian
            </text>
            <text
              x={cx + radius + 14}
              y={cy + 10}
              textAnchor="start"
              className="fill-muted-foreground text-[10px]"
            >
              (Temporal Reasoning)
            </text>
          </g>

          {/* S3: Bottom */}
          <g
            className="cursor-pointer select-none"
            onClick={() => setActiveCriterion(activeCriterion === "s3" ? null : "s3")}
          >
            <text
              x={cx}
              y={cy + radius + 22}
              textAnchor="middle"
              className={cn(
                "font-serif font-bold text-xs transition-colors",
                activeCriterion === "s3" ? "fill-primary" : "fill-foreground",
              )}
            >
              S3 • Sử liệu & Bằng chứng
            </text>
            <text
              x={cx}
              y={cy + radius + 34}
              textAnchor="middle"
              className="fill-muted-foreground text-[10px]"
            >
              (Evidence Analysis)
            </text>
          </g>

          {/* S4: Left */}
          <g
            className="cursor-pointer select-none"
            onClick={() => setActiveCriterion(activeCriterion === "s4" ? null : "s4")}
          >
            <text
              x={cx - radius - 14}
              y={cy - 4}
              textAnchor="end"
              className={cn(
                "font-serif font-bold text-xs transition-colors",
                activeCriterion === "s4" ? "fill-primary" : "fill-foreground",
              )}
            >
              S4 • Lập luận & Giới hạn
            </text>
            <text
              x={cx - radius - 14}
              y={cy + 10}
              textAnchor="end"
              className="fill-muted-foreground text-[10px]"
            >
              (Epistemic Humility)
            </text>
          </g>
        </svg>
      </div>

      {/* Interactive Active Criterion Inspector Card */}
      {activeCriterion && (
        <div className="w-full mt-2 p-3 rounded-xl border border-primary/30 bg-primary/5 text-xs space-y-1 animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center justify-between font-bold text-primary">
            <span>
              {RUBRIC_METADATA[activeCriterion].titleVi} (
              {student[activeCriterion]}/{maxScore}đ)
            </span>
            <span className="font-mono text-[11px]">
              Mục tiêu: {benchmark[activeCriterion]}/{maxScore}đ
            </span>
          </div>
          <p className="text-[11px] text-muted-foreground leading-relaxed">
            {calc.criteriaBreakdown[activeCriterion].descriptor ||
              RUBRIC_METADATA[activeCriterion].description}
          </p>
          <p className="text-[10px] text-primary/80 italic pt-1 border-t border-primary/15">
            Gợi ý: {RUBRIC_METADATA[activeCriterion].recommendationPrompt}
          </p>
        </div>
      )}

      {/* Quantitative Score Summary Pill */}
      {showScoreSummary && (
        <div className="w-full mt-3 pt-3 border-t border-border/60 flex items-center justify-between text-xs">
          <div className="space-y-0.5">
            <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">
              Xếp loại Năng lực
            </span>
            <span
              className={cn(
                "px-2.5 py-0.5 rounded-full text-xs font-bold border inline-block",
                classificationColor,
              )}
            >
              {calc.classification}
            </span>
          </div>

          <div className="text-right space-y-0.5">
            <span className="text-[10px] uppercase font-bold text-muted-foreground tracking-wider block">
              Điểm chuẩn hóa hệ 10
            </span>
            <div className="flex items-baseline justify-end gap-1 font-mono">
              <span className="text-lg font-extrabold text-primary">
                {calc.normalized10.toFixed(1)}
              </span>
              <span className="text-muted-foreground text-[11px]">
                / 10.0 ({calc.rawScore}/{calc.maxPossibleScore}đ)
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Legend */}
      {showLegend && (
        <div className="flex flex-wrap items-center justify-center gap-4 mt-3 pt-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-3.5 h-3.5 rounded-sm bg-amber-500/30 border-2 border-amber-500" />
            <span className="text-[11px] font-medium text-foreground">{studentLabel}</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-4 h-0 border-t-2 border-dashed border-blue-500" />
            <span className="text-[11px] font-medium text-foreground">{benchmarkLabel}</span>
          </div>
        </div>
      )}

      {/* Accessible Screen-Reader Summary Table (Hidden Visually) */}
      <div className="sr-only">
        <table>
          <caption>Bảng tổng hợp điểm Rubric S1-S4 chi tiết</caption>
          <thead>
            <tr>
              <th scope="col">Tiêu chuẩn năng lực</th>
              <th scope="col">Điểm đạt được</th>
              <th scope="col">Mục tiêu chuẩn</th>
              <th scope="col">Điểm tối đa</th>
              <th scope="col">Mức độ thể hiện</th>
            </tr>
          </thead>
          <tbody>
            {AXES_CONFIG.map(({ key, id }) => {
              const meta = RUBRIC_METADATA[key];
              const score = student[key];
              const bench = benchmark[key];
              const breakdown = calc.criteriaBreakdown[key];
              return (
                <tr key={key}>
                  <th scope="row">{`${id}: ${meta.dimensionVi}`}</th>
                  <td>{score}</td>
                  <td>{bench}</td>
                  <td>{maxScore}</td>
                  <td>{breakdown.levelLabel}</td>
                </tr>
              );
            })}
            <tr>
              <th scope="row">Tổng điểm thô</th>
              <td>{calc.rawScore}</td>
              <td>-</td>
              <td>{calc.maxPossibleScore}</td>
              <td>{calc.classification}</td>
            </tr>
            <tr>
              <th scope="row">Điểm quy đổi hệ 10</th>
              <td>{calc.normalized10}</td>
              <td>-</td>
              <td>10.0</td>
              <td>{calc.classification}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </figure>
  );
}
