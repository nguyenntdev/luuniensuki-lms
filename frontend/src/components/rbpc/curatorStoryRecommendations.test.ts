import { describe, it, expect } from "vitest";
import * as React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { CuratorStoryRecommendations } from "./CuratorStoryRecommendations";
import type { CuratorStoryRecommendation } from "@/types/rbpc";

describe("CuratorStoryRecommendations Component Contract (V5-T105)", () => {
  const mockRecs: CuratorStoryRecommendation[] = [
    {
      story_slug: "tieng-chuong-khiem-cung",
      title: "Tiếng Đồng Phường Đúc & Chuông Vọng Khiêm Cung",
      intro: "Hành trình ngược dòng sông Hương từ tiếng chuông đại hồng chung Thiên Mụ đến lò đúc 500 năm tuổi.",
      approved_summary: "Khảo chứng kỹ nghệ rót đồng qua thư tịch triều Nguyễn.",
      category: "craft_living_culture",
      linkage_type: "object_associated_craft",
      historical_justification: "Mối liên kết lịch sử đã thẩm định giữa công trình/hiện vật hoàng cung và xưởng nghề truyền thống.",
      reading_time_minutes: 5,
      verified_historical_relationship: true,
      no_implied_fake_imperial_lineage: true,
      workshop: {
        creator_slug: "nguyen-van-sinh",
        creator_name: "Nghệ nhân Nhân dân Nguyễn Văn Sinh",
        craft_tradition: "Đúc đồng Phường Đúc",
        experience_slug: "workshop-duc-dong-phuong-duc",
        experience_title: "Trải nghiệm Đúc Đồng Thủ Công Cùng Nghệ Nhân Phường Đúc",
        area_public: "Phường Đúc, TP. Huế",
        availability_mode: "inquiry_only",
        is_verified_artisan: true,
        consent_status: "consented",
        artisan_dignity_note: "Nghệ nhân đương đại gìn giữ kỹ nghệ truyền thống; hoàn toàn tách biệt với cổ vật hoàng gia năm 1835.",
      },
    },
  ];

  it("exports a valid React component with correct displayName", () => {
    expect(CuratorStoryRecommendations).toBeDefined();
    expect(CuratorStoryRecommendations.displayName).toBe("CuratorStoryRecommendations");
  });

  it("renders recommendations with verified historical linkage badge and artisan dignity note", () => {
    const html = renderToStaticMarkup(
      React.createElement(CuratorStoryRecommendations, {
        storySlug: "the-mieu",
        locale: "vi",
        initialRecommendations: mockRecs,
      })
    );

    // Title & badge
    expect(html).toContain("Gợi ý Hành trình Giám tuyển");
    expect(html).toContain("Liên kết thẩm định");
    expect(html).toContain("Tiếng Đồng Phường Đúc &amp; Chuông Vọng Khiêm Cung");

    // Workshop and Artisan dignity note
    expect(html).toContain("Nghệ nhân Nhân dân Nguyễn Văn Sinh");
    expect(html).toContain("Đúc đồng Phường Đúc");
    expect(html).toContain("hoàn toàn tách biệt với cổ vật hoàng gia năm 1835");
  });

  it("renders in English with appropriate translated labels", () => {
    const html = renderToStaticMarkup(
      React.createElement(CuratorStoryRecommendations, {
        storySlug: "the-mieu",
        locale: "en",
        initialRecommendations: [
          {
            ...mockRecs[0],
            title: "Foundry Fires of Phuong Duc",
            historical_justification: "Verified historical association connecting royal architecture to traditional craft quarters.",
            workshop: {
              ...mockRecs[0].workshop!,
              artisan_dignity_note: "Living craft practitioner preserving traditional technique; distinct from 1835 royal antiquities.",
            },
          },
        ],
      })
    );

    expect(html).toContain("Curator-Controlled Story Recommendations");
    expect(html).toContain("Verified Heritage Link");
    expect(html).toContain("Foundry Fires of Phuong Duc");
    expect(html).toContain("distinct from 1835 royal antiquities");
  });

  it("fails closed and renders nothing when recommendations list is empty", () => {
    const html = renderToStaticMarkup(
      React.createElement(CuratorStoryRecommendations, {
        storySlug: "unknown-story",
        locale: "vi",
        initialRecommendations: [],
      })
    );
    expect(html).toBe("");
  });
});
