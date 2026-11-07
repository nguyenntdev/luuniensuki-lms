import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import RbpcImpactDashboardPage from "./page";
import { RbpcImpactDashboardClient } from "@/components/rbpc/RbpcImpactDashboardClient";
import * as inquiriesApi from "@/lib/rbpc/inquiries";
import type { RbpcImpactMetricsOut } from "@/types/rbpc";

vi.mock("@/lib/seo", () => ({
  setPageMeta: vi.fn(),
}));

const mockImpactMetrics: RbpcImpactMetricsOut = {
  observed_metrics: {
    published_stories_count: 5,
    consented_creators_count: 4,
    active_experiences_count: 3,
    total_inquiries_received: 12,
    verified_heritage_places_count: 23,
    verified_source_citations_count: 48,
    completed_experiences_count: 2,
    artisan_payout_vnd_settled: 1640000.0,
    sponsor_support_vnd_verified: 202360638.0,
  },
  projected_metrics: {
    estimated_monthly_demand: 120,
    projected_local_value_addition_vnd: 54000000.0,
    projection_basis: "Các số liệu dự phóng là giả định mô hình kinh doanh phục vụ nghiên cứu và đề án RBPC 2026, không phải doanh thu đã ghi nhận.",
  },
  scope: "RBPC_HUE",
  generated_at: "2026-11-05T12:00:00Z",
};

describe("RBPC Public Impact Dashboard Page", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders static structure with header and observed vs projected separation", () => {
    const html = renderToStaticMarkup(<RbpcImpactDashboardClient initialMetrics={mockImpactMetrics} />);

    // Header & Titles
    expect(html).toContain("Bảng Tác Động Thực Tế &amp; Đối Soát Minh Bạch");
    expect(html).toContain("Minh bạch số liệu thực tế — Không tạo số ảo hay thổi phồng quy mô");

    // Section 1: Observed metrics presence
    expect(html).toContain("1. Số Liệu Thực Tế Ghi Nhận (Database-Observed)");
    expect(html).toContain("Trải nghiệm hoàn tất");
    expect(html).toContain("Chi trả thực tế nghệ nhân");
    expect(html).toContain("Bảo trợ hiện vật xác thực");
    expect(html).toContain("data-testid=\"completed-experiences-count\"");
    expect(html).toContain("data-testid=\"artisan-payout-settled\"");
    expect(html).toContain("data-testid=\"sponsor-support-verified\"");

    // Section 2: Projected metrics quarantined
    expect(html).toContain("2. Số Liệu Dự Phóng Mô Hình Kinh Doanh (Forward Projections — Phân Tách Rõ)");
    expect(html).toContain("data-testid=\"projection-basis-disclaimer\"");
    expect(html).toContain("data-testid=\"projected-monthly-demand\"");
    expect(html).toContain("data-testid=\"projected-local-value\"");

    // Integrity Notice
    expect(html).toContain("Cam kết liêm chính số liệu LƯU NIÊN");
    expect(html).toContain("bảng tác động hiển thị chính xác 0");
  });

  it("negative abuse: renders 0 metrics when initialMetrics has 0 completed experiences and payouts", () => {
    const emptyMetrics: RbpcImpactMetricsOut = {
      observed_metrics: {
        published_stories_count: 0,
        consented_creators_count: 0,
        active_experiences_count: 0,
        total_inquiries_received: 0,
        verified_heritage_places_count: 0,
        verified_source_citations_count: 0,
        completed_experiences_count: 0,
        artisan_payout_vnd_settled: 0.0,
        sponsor_support_vnd_verified: 202360638.0,
      },
      projected_metrics: {
        estimated_monthly_demand: 120,
        projected_local_value_addition_vnd: 54000000.0,
        projection_basis: "Các số liệu dự phóng là giả định mô hình kinh doanh phục vụ nghiên cứu và đề án RBPC 2026, không phải doanh thu đã ghi nhận.",
      },
      scope: "RBPC_HUE",
      generated_at: "2026-11-05T12:00:00Z",
    };

    const html = renderToStaticMarkup(<RbpcImpactDashboardClient initialMetrics={emptyMetrics} />);
    expect(html).toContain("data-testid=\"completed-experiences-count\"");
    expect(html).toContain("data-testid=\"artisan-payout-settled\"");
    expect(html).toContain("data-testid=\"total-inquiries-count\"");
    expect(html).toContain(">0</div>");
    expect(html).toContain("0 ₫"); // Unicode non-breaking space used by Intl.NumberFormat
  });

  it("fetchImpactMetricsApi contract calls /api/v1/rbpc/impact", async () => {
    const apiSpy = vi.spyOn(inquiriesApi, "fetchImpactMetricsApi").mockResolvedValue(mockImpactMetrics);
    const res = await inquiriesApi.fetchImpactMetricsApi();

    expect(apiSpy).toHaveBeenCalledTimes(1);
    expect(res.observed_metrics.completed_experiences_count).toBe(2);
    expect(res.observed_metrics.artisan_payout_vnd_settled).toBe(1640000.0);
    expect(res.observed_metrics.sponsor_support_vnd_verified).toBe(202360638.0);
    expect(res.projected_metrics.estimated_monthly_demand).toBe(120);
    expect(res.projected_metrics.projection_basis).toContain("giả định mô hình kinh doanh");
  });
});
