import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { FunnelDashboardClient } from "./FunnelDashboardClient";
import * as api from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

const mockFunnelData: api.TruthFunnelDashboardData = {
  generated_at: "2026-11-07T10:00:00Z",
  filter_range: {
    start: null,
    end: null,
    cohort: null,
    channel: null,
    experience_id: null,
  },
  observed: {
    truth_tier: "OBSERVED",
    definition: "Số liệu thực tế ghi nhận từ cơ sở dữ liệu qua sự kiện nhật ký và bảng giao dịch rbpc_inquiries.",
    total_funnel_visitors: 450,
    total_completed_experiences: 3,
    overall_conversion_pct: 0.67,
    stages: [
      {
        stage: "visitor",
        display_name: "1. Khách truy cập (Visitor)",
        description: "Khách tiếp cận",
        count: 450,
        conversion_from_previous_pct: 100.0,
        conversion_from_top_pct: 100.0,
        truth_tier: "OBSERVED",
        measurement_method: "AnalyticsEvent",
      },
      {
        stage: "source_read",
        display_name: "2. Đọc nguồn sử liệu (Source Read)",
        description: "Đọc sử liệu >60s",
        count: 90,
        conversion_from_previous_pct: 20.0,
        conversion_from_top_pct: 20.0,
        truth_tier: "OBSERVED",
        measurement_method: "AnalyticsEvent",
      },
      {
        stage: "inquiry",
        display_name: "3. Yêu cầu đặt chỗ (Inquiry)",
        description: "Gửi phiếu yêu cầu",
        count: 15,
        conversion_from_previous_pct: 16.67,
        conversion_from_top_pct: 3.33,
        truth_tier: "OBSERVED",
        measurement_method: "rbpc_inquiries",
      },
      {
        stage: "confirm",
        display_name: "4. Xác nhận đặt chỗ (Confirm)",
        description: "Nghệ nhân xác nhận",
        count: 5,
        conversion_from_previous_pct: 33.33,
        conversion_from_top_pct: 1.11,
        truth_tier: "OBSERVED",
        measurement_method: "rbpc_inquiries confirmed",
      },
      {
        stage: "completed",
        display_name: "5. Trải nghiệm hoàn thành (Completed)",
        description: "Hoàn tất trải nghiệm",
        count: 3,
        conversion_from_previous_pct: 60.0,
        conversion_from_top_pct: 0.67,
        truth_tier: "OBSERVED",
        measurement_method: "rbpc_inquiries closed",
      },
    ],
    quality_cohorts: [
      {
        cohort_id: "channel_email",
        cohort_name: "Kênh liên hệ: EMAIL",
        cohort_type: "channel",
        visitor_count: 50,
        source_read_count: 20,
        inquiry_count: 10,
        confirm_count: 4,
        completed_count: 2,
        visitor_to_source_pct: 40.0,
        source_to_inquiry_pct: 50.0,
        inquiry_to_confirm_pct: 40.0,
        confirm_to_completed_pct: 50.0,
        overall_conversion_pct: 4.0,
        avg_dwell_seconds: 78.5,
        source_grounding_score_pct: 100.0,
      },
    ],
  },
  hypothesis: {
    truth_tier: "HYPOTHESIS",
    definition: "Giả thuyết mô hình chuyển đổi chuẩn hóa",
    epistemic_disclaimer: "Các tỷ lệ chuyển đổi giả định chuẩn hóa từ DOC-RBPC-FIN-001.",
    benchmark_assumptions: {
      story_engagement_rate_pct: 20.0,
      inquiry_conversion_rate_pct: 15.0,
      partner_acceptance_rate_pct: 75.0,
      experience_completion_rate_pct: 88.89,
      benchmark_monthly_eligible_visitors: 1500,
    },
    modeled_monthly_funnel: {
      visitors: 1500,
      engaged_story_readers: 300,
      qualified_inquiries: 45,
      confirmed_bookings: 34,
      completed_experiences: 30,
    },
  },
  forecast: {
    truth_tier: "FORECAST",
    definition: "Mục tiêu kinh doanh SOM Year 1",
    epistemic_disclaimer: "Mục tiêu kinh doanh và dự phóng thị trường SOM 2026-2027.",
    target_period: "SOM Năm 1 (10 tháng hoạt động, 2026-2027)",
    projected_annual_bookings: 1100,
    projected_annual_gmv_vnd: 570000000.0,
    target_partner_workshops: 5,
    projected_platform_net_revenue_vnd: 57000000.0,
    projected_artisan_retained_vnd: 513000000.0,
    negative_abuse_guardrail: "Con số 1,100 lượt trải nghiệm là mục tiêu dự phóng SOM năm 1, được cách ly tuyệt đối khỏi tầng dữ liệu thực tế (OBSERVED).",
  },
  anti_abuse_validation: {
    status: "PASSED_STRICT",
    forecast_1100_in_completed_bookings: false,
    observed_completed_matches_closed_inquiries: true,
    synthetic_counts_in_observed: false,
    empty_db_baseline_zero: true,
    enforcement_policy: "Strict isolation between OBSERVED actuals and FORECAST projections.",
  },
};

let mockAuthState = {
  status: "authed",
  user: { id: "admin-1", role: "admin", email: "admin@example.com" } as any,
  logout: vi.fn(),
};

vi.mock("@/stores/authStore", () => ({
  useAuthStore: (selector: (state: unknown) => unknown) => selector(mockAuthState),
}));

describe("Truth-Level Conversion Funnel Dashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders login requirement when unauthenticated", () => {
    mockAuthState = {
      status: "unauth",
      user: null,
      logout: vi.fn(),
    };
    const html = renderToStaticMarkup(<FunnelDashboardClient />);
    expect(html).toContain("Vui lòng đăng nhập");
  });

  it("renders forbidden message when user is not staff/admin", () => {
    mockAuthState = {
      status: "authed",
      user: { id: "1", role: "learner", email: "learner@example.com" } as any,
      logout: vi.fn(),
    };
    const html = renderToStaticMarkup(<FunnelDashboardClient />);
    expect(html).toContain("Bạn không có quyền truy cập");
  });

  it("renders truth funnel dashboard elements for authenticated admin", () => {
    mockAuthState = {
      status: "authed",
      user: { id: "admin-1", role: "admin", email: "admin@example.com" } as any,
      logout: vi.fn(),
    };

    const html = renderToStaticMarkup(<FunnelDashboardClient initialData={mockFunnelData} />);

    // Header & Titles
    expect(html).toContain("Truth-Level Conversion Funnel");
    expect(html).toContain("OBSERVED");
    expect(html).toContain("HYPOTHESIS");
    expect(html).toContain("FORECAST");

    // Anti-Abuse Invariant Banner
    expect(html).toContain("data-testid=\"anti-abuse-status\"");
    expect(html).toContain("Mục tiêu dự phóng 1,100 lượt không bao giờ được tính vào số lượt hoàn thành thực tế");

    // KPIs and stages
    expect(html).toContain("data-testid=\"observed-completed-count\"");
    expect(html).toContain("data-testid=\"observed-inquiries-count\"");
    expect(html).toContain("data-testid=\"observed-confirmed-count\"");
    expect(html).toContain("data-testid=\"observed-source-reads-count\"");
    expect(html).toContain("data-testid=\"observed-visitors-count\"");
    expect(html).toContain("data-testid=\"observed-overall-conversion\"");

    // Quality cohorts
    expect(html).toContain("data-testid=\"quality-cohorts-table\"");

    // Navigation back to admin
    expect(html).toContain("Admin Studio");
  });
});
