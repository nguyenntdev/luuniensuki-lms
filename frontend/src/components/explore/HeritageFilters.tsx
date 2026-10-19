"use client";

import React, { useCallback, useId } from "react";
import {
  Search,
  X,
  LayoutGrid,
  MapPin,
  Compass,
  Landmark,
  Crown,
  Hammer,
  Music,
  Box,
  Award,
  RotateCcw,
  SlidersHorizontal,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import type { HeritageCategory } from "@/types/heritage";
import type { RbpcLocale } from "@/lib/rbpc/copy";
import { cn } from "@/lib/utils";

export type HeritageViewMode = "grid" | "map";

export interface HeritageFilterValues {
  q: string;
  category: HeritageCategory | "all";
  unescoOnly?: boolean;
  has3dOnly?: boolean;
  accessStatus?: "open" | "all";
}

export interface HeritageFiltersProps {
  values: HeritageFilterValues;
  onChange: (nextValues: HeritageFilterValues) => void;
  viewMode: HeritageViewMode;
  onViewModeChange: (nextMode: HeritageViewMode) => void;
  totalCount?: number;
  isLoading?: boolean;
  locale?: RbpcLocale;
  className?: string;
  onReset?: () => void;
}

export interface CategoryTabItem {
  id: HeritageCategory | "all";
  labelVi: string;
  labelEn: string;
  icon: LucideIcon;
}

export const FILTER_CATEGORY_TABS: CategoryTabItem[] = [
  {
    id: "all",
    labelVi: "Tất cả di sản",
    labelEn: "All Heritage",
    icon: Compass,
  },
  {
    id: "imperial_architecture",
    labelVi: "Kiến trúc Cung đình",
    labelEn: "Imperial Monuments",
    icon: Landmark,
  },
  {
    id: "royal_tomb",
    labelVi: "Lăng tẩm Hoàng gia",
    labelEn: "Royal Tombs",
    icon: Crown,
  },
  {
    id: "craft_living_culture",
    labelVi: "Làng nghề thủ công",
    labelEn: "Living Crafts",
    icon: Hammer,
  },
  {
    id: "music_performance",
    labelVi: "Di sản phi vật thể",
    labelEn: "Intangible Traditions",
    icon: Music,
  },
];

/**
 * HeritageFilters Component
 * Provides:
 * 1. Category tabs (Imperial Monuments, Royal Tombs, Living Crafts, Intangible Traditions, All)
 * 2. Search input with live clear action and accent-tolerant placeholder
 * 3. View toggle (Grid vs Map)
 * 4. Filter chips (UNESCO 14 components, 3D model)
 * 5. Results count & reset action
 */
export default function HeritageFilters({
  values,
  onChange,
  viewMode,
  onViewModeChange,
  totalCount,
  isLoading = false,
  locale = "vi",
  className,
  onReset,
}: HeritageFiltersProps) {
  const searchInputId = useId();

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({
      ...values,
      q: e.target.value,
    });
  };

  const handleClearSearch = () => {
    onChange({
      ...values,
      q: "",
    });
  };

  const handleSelectCategory = (catId: HeritageCategory | "all") => {
    onChange({
      ...values,
      category: catId,
    });
  };

  const handleToggleUnesco = () => {
    onChange({
      ...values,
      unescoOnly: !values.unescoOnly,
    });
  };

  const handleToggle3d = () => {
    onChange({
      ...values,
      has3dOnly: !values.has3dOnly,
    });
  };

  const handleResetFilters = useCallback(() => {
    if (onReset) {
      onReset();
    } else {
      onChange({
        q: "",
        category: "all",
        unescoOnly: false,
        has3dOnly: false,
        accessStatus: "all",
      });
    }
  }, [onChange, onReset]);

  const hasActiveFilters = Boolean(
    values.q.trim() ||
      values.category !== "all" ||
      values.unescoOnly ||
      values.has3dOnly
  );

  return (
    <div
      className={cn(
        "flex flex-col gap-4 rounded-2xl border border-border/80 bg-card p-4 sm:p-5 shadow-xs transition-colors",
        className
      )}
      role="search"
      aria-label={locale === "vi" ? "Bộ lọc tìm kiếm di sản Huế" : "Huế heritage search filters"}
    >
      {/* Row 1: Search Input & View Toggle */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        {/* Search Input Container */}
        <div className="relative flex-1">
          <label htmlFor={searchInputId} className="sr-only">
            {locale === "vi"
              ? "Tìm kiếm di tích, lăng tẩm, làng nghề"
              : "Search monuments, tombs, craft villages"}
          </label>
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-muted-foreground">
            <Search className="h-4 w-4" aria-hidden="true" />
          </div>

          <input
            id={searchInputId}
            type="search"
            value={values.q}
            onChange={handleSearchChange}
            placeholder={
              locale === "vi"
                ? "Tìm kiếm di tích, lăng tẩm, làng nghề... (VD: Ngọ Môn, Tự Đức, Phường Đúc)"
                : "Search monuments, tombs, craft villages... (e.g. Ngo Mon, Tu Duc, Phuong Duc)"
            }
            className="block w-full min-h-[44px] rounded-xl border border-border/80 bg-background py-2.5 pr-10 pl-10 text-sm text-foreground placeholder:text-muted-foreground/70 transition-colors focus:border-primary focus:bg-background focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
          />

          {values.q && (
            <button
              type="button"
              onClick={handleClearSearch}
              aria-label={locale === "vi" ? "Xóa từ khóa tìm kiếm" : "Clear search query"}
              className="absolute inset-y-0 right-0 flex min-h-[44px] min-w-[44px] items-center justify-center text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          )}
        </div>

        {/* View Mode Toggle: Grid vs Map (Min 44px Touch Targets) */}
        <div
          role="group"
          aria-label={locale === "vi" ? "Chế độ hiển thị" : "Display view mode"}
          className="flex shrink-0 items-center rounded-xl border border-border/80 bg-muted/40 p-1"
        >
          <button
            type="button"
            onClick={() => onViewModeChange("grid")}
            aria-pressed={viewMode === "grid"}
            className={cn(
              "flex min-h-[44px] items-center gap-1.5 rounded-lg px-3.5 py-2 text-xs font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2",
              viewMode === "grid"
                ? "bg-background text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <LayoutGrid className="h-4 w-4" aria-hidden="true" />
            <span>{locale === "vi" ? "Dạng lưới" : "Grid"}</span>
          </button>

          <button
            type="button"
            onClick={() => onViewModeChange("map")}
            aria-pressed={viewMode === "map"}
            className={cn(
              "flex min-h-[44px] items-center gap-1.5 rounded-lg px-3.5 py-2 text-xs font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2",
              viewMode === "map"
                ? "bg-background text-foreground shadow-xs"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <MapPin className="h-4 w-4" aria-hidden="true" />
            <span>{locale === "vi" ? "Bản đồ" : "Map"}</span>
          </button>
        </div>
      </div>

      {/* Row 2: Category Tabs (Horizontal Scrollable Pills, Min 44px Touch Targets) */}
      <div className="relative">
        <div
          role="tablist"
          aria-label={locale === "vi" ? "Danh mục di sản" : "Heritage categories"}
          className="no-scrollbar flex items-center gap-2 overflow-x-auto py-1"
        >
          {FILTER_CATEGORY_TABS.map((tab) => {
            const isSelected = values.category === tab.id;
            const label = locale === "vi" ? tab.labelVi : tab.labelEn;
            const Icon = tab.icon;

            return (
              <button
                key={tab.id}
                role="tab"
                type="button"
                aria-selected={isSelected}
                onClick={() => handleSelectCategory(tab.id)}
                className={cn(
                  "flex min-h-[44px] shrink-0 items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2",
                  isSelected
                    ? "bg-primary text-primary-foreground shadow-xs"
                    : "border border-border/70 bg-background/80 text-muted-foreground hover:border-border hover:bg-secondary/70 hover:text-foreground"
                )}
              >
                <Icon
                  className={cn(
                    "h-3.5 w-3.5",
                    isSelected ? "text-primary-foreground" : "text-muted-foreground"
                  )}
                  aria-hidden="true"
                />
                <span>{label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Row 3: Facet Pills (UNESCO & 3D, Min 44px Touch Targets) + Result Count + Reset */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border/60 pt-3 text-xs">
        {/* Toggle Chips */}
        <div className="flex flex-wrap items-center gap-2">
          {/* UNESCO Toggle Chip */}
          <button
            type="button"
            onClick={handleToggleUnesco}
            aria-pressed={Boolean(values.unescoOnly)}
            className={cn(
              "inline-flex min-h-[44px] items-center gap-1.5 rounded-full border px-3.5 py-1.5 font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2",
              values.unescoOnly
                ? "border-emerald-600 bg-emerald-50 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300 font-semibold shadow-xs"
                : "border-border/80 bg-background/80 text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
            )}
          >
            <Award className="h-3.5 w-3.5" aria-hidden="true" />
            <span>
              {locale === "vi" ? "Chỉ hiện UNESCO (14 Cấu phần)" : "UNESCO Inscribed Only"}
            </span>
          </button>

          {/* 3D Model Toggle Chip */}
          <button
            type="button"
            onClick={handleToggle3d}
            aria-pressed={Boolean(values.has3dOnly)}
            className={cn(
              "inline-flex min-h-[44px] items-center gap-1.5 rounded-full border px-3.5 py-1.5 font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2",
              values.has3dOnly
                ? "border-primary bg-primary/10 text-primary font-semibold shadow-xs"
                : "border-border/80 bg-background/80 text-muted-foreground hover:bg-secondary/60 hover:text-foreground"
            )}
          >
            <Box className="h-3.5 w-3.5" aria-hidden="true" />
            <span>{locale === "vi" ? "Có mô hình 3D" : "Has 3D Model"}</span>
          </button>
        </div>

        {/* Results Count & Reset Button */}
        <div className="flex items-center gap-3">
          {totalCount !== undefined && (
            <span className="text-muted-foreground">
              {isLoading ? (
                <span>{locale === "vi" ? "Đang tải dữ liệu..." : "Loading records..."}</span>
              ) : (
                <span>
                  {locale === "vi" ? (
                    <>
                      Đang hiển thị{" "}
                      <strong className="font-semibold text-foreground">{totalCount}</strong>{" "}
                      địa điểm
                    </>
                  ) : (
                    <>
                      Showing{" "}
                      <strong className="font-semibold text-foreground">{totalCount}</strong>{" "}
                      places
                    </>
                  )}
                </span>
              )}
            </span>
          )}

          {hasActiveFilters && (
            <button
              type="button"
              onClick={handleResetFilters}
              className="inline-flex min-h-[44px] items-center gap-1 rounded-lg px-3 py-1 font-semibold text-primary transition-colors hover:bg-primary/10 hover:text-primary-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--rbpc-focus,#1E675A)] focus-visible:ring-offset-2"
            >
              <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
              <span>{locale === "vi" ? "Xóa bộ lọc" : "Reset Filters"}</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
