import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import PilotOnboardingPortal from "./page";

describe("Pilot Onboarding Portal Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the pilot token redemption gateway for unactivated users", () => {
    const html = renderToStaticMarkup(<PilotOnboardingPortal />);

    expect(html).toContain("Cổng Thử Nghiệm Thí Điểm");
    expect(html).toContain("Kích Hoạt &amp; Đồng Hành Pilot Dự Án Lưu Niên");
    expect(html).toContain("Xác Thực Mã Mời Thử Nghiệm");
    expect(html).toContain("Mã Token Thư Mời (Invitation Secret Token)");
    expect(html).toContain("Kiểm tra mã");
  });

  it("emphasizes ethical research compliance and invitation requirement", () => {
    const html = renderToStaticMarkup(<PilotOnboardingPortal />);

    expect(html).toContain("Chương trình thử nghiệm thí điểm có kiểm soát chất lượng");
    expect(html).toContain("Dành riêng cho đối tác giáo dục THPT/THCS và các cơ sở làng nghề");
  });
});
