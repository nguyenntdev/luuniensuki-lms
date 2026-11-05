import React from "react";
import { describe, it, expect, vi } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { CurriculumCompetencyCatalog } from "./CurriculumCompetencyCatalog";
import type {
  CurriculumCompetency,
  CurriculumCompetencyRelicMapping,
} from "@/types/curriculum";

describe("CurriculumCompetencyCatalog Component", () => {
  const mockCompetencies: CurriculumCompetency[] = [
    {
      id: "comp-1",
      code: "COMP_HIST_LITERACY",
      standard_framework: "VN_GDPT_2018",
      domain: "historical_literacy",
      name_vi: "Năng lực Tìm hiểu Lịch sử",
      name_en: "Historical Literacy",
      description_vi: "Năng lực nhận diện sự kiện, hiện vật Cửu Đỉnh.",
      description_en: "Ability to recognize historical events and relics.",
      grade_band_descriptors: {},
      is_active: true,
      created_at: "2026-11-05T00:00:00Z",
    },
    {
      id: "comp-2",
      code: "COMP_SOURCE_CRITICISM",
      standard_framework: "VN_GDPT_2018",
      domain: "source_criticism",
      name_vi: "Năng lực Khảo chứng Sử liệu",
      name_en: "Source Criticism",
      description_vi: "Khảo chứng thư tịch và bản dập 2D.",
      description_en: "Epistemic source critique.",
      grade_band_descriptors: {},
      is_active: true,
      created_at: "2026-11-05T00:00:00Z",
    },
  ];

  const mockMappings: CurriculumCompetencyRelicMapping[] = [
    {
      id: "map-1",
      competency_id: "comp-1",
      competency_code: "COMP_HIST_LITERACY",
      competency_name_vi: "Năng lực Tìm hiểu Lịch sử",
      competency_domain: "historical_literacy",
      relic_urn_slug: "cao-dinh",
      relic_motif_id: "urn_cao_dinh_01",
      grade_band: "GRADE_6_7",
      min_grade: 6,
      max_grade: 7,
      learning_activity_vi: "Quan sát họa tiết Rồng trên Cao Đỉnh",
      evidence_requirement_vi: "Đối chiếu bản dập 2D",
      status: "verified",
      is_reviewed: true,
      review_warning: null,
      flag_count: 0,
      created_at: "2026-11-05T00:00:00Z",
      updated_at: "2026-11-05T00:00:00Z",
    },
    {
      id: "map-2",
      competency_id: "comp-2",
      competency_code: "COMP_SOURCE_CRITICISM",
      competency_name_vi: "Năng lực Khảo chứng Sử liệu",
      competency_domain: "source_criticism",
      relic_urn_slug: "tuyen-dinh",
      grade_band: "GRADE_10_12",
      min_grade: 10,
      max_grade: 12,
      learning_activity_vi: "Thẩm định văn khắc Hán Nôm trên Tuyên Đỉnh",
      evidence_requirement_vi: "Trích dẫn châu bản triều Nguyễn",
      status: "unreviewed",
      is_reviewed: false,
      review_warning: "Cảnh báo: Ánh xạ năng lực chưa được thẩm định chuyên môn bởi giáo viên cốt cán",
      flag_count: 0,
      created_at: "2026-11-05T00:00:00Z",
      updated_at: "2026-11-05T00:00:00Z",
    },
    {
      id: "map-3",
      competency_id: "comp-2",
      competency_code: "COMP_SOURCE_CRITICISM",
      competency_name_vi: "Năng lực Khảo chứng Sử liệu",
      competency_domain: "source_criticism",
      relic_urn_slug: "nhan-dinh",
      grade_band: "GRADE_10_12",
      min_grade: 10,
      max_grade: 12,
      learning_activity_vi: "Phân tích văn tự cổ Nhân Đỉnh",
      evidence_requirement_vi: "Đối chiếu tài liệu làng nghề",
      status: "flagged",
      is_reviewed: false,
      review_warning: "Cảnh báo: Ánh xạ bị giáo viên gắn cờ cảnh báo: inaccurate_grade_level",
      flag_count: 1,
      created_at: "2026-11-05T00:00:00Z",
      updated_at: "2026-11-05T00:00:00Z",
    },
  ];

  it("renders catalog title, GDPT 2018 framework, and standard competency cards", () => {
    const html = renderToStaticMarkup(
      <CurriculumCompetencyCatalog
        competencies={mockCompetencies}
        initialMappings={mockMappings}
        userRole="learner"
      />
    );

    expect(html).toContain("Danh mục Năng lực Lịch sử &amp; Ánh xạ Di sản Cửu Đỉnh");
    expect(html).toContain("Chương trình Giáo dục Phổ thông 2018 (Môn Lịch sử)");
    expect(html).toContain("COMP_HIST_LITERACY");
    expect(html).toContain("COMP_SOURCE_CRITICISM");
    expect(html).toContain("Năng lực Tìm hiểu Lịch sử");
    expect(html).toContain("Năng lực Khảo chứng Sử liệu");
  });

  it("displays review warnings on unreviewed mappings (Negative Abuse Invariant)", () => {
    const html = renderToStaticMarkup(
      <CurriculumCompetencyCatalog
        competencies={mockCompetencies}
        initialMappings={mockMappings}
        userRole="guest"
      />
    );

    // Unreviewed mapping warning
    expect(html).toContain("Cảnh báo thẩm định năng lực:");
    expect(html).toContain("Cảnh báo: Ánh xạ năng lực chưa được thẩm định chuyên môn bởi giáo viên cốt cán");
    expect(html).toContain("Chưa duyệt");
  });

  it("displays flagged warning banner when mapping has been flagged by teacher", () => {
    const html = renderToStaticMarkup(
      <CurriculumCompetencyCatalog
        competencies={mockCompetencies}
        initialMappings={mockMappings}
        userRole="guest"
      />
    );

    expect(html).toContain("Cảnh báo: Ánh xạ bị giáo viên gắn cờ cảnh báo: inaccurate_grade_level");
    expect(html).toContain("Bị gắn cờ sai lệch (1)");
  });

  it("renders verified badge when mapping is approved and verified without warnings", () => {
    const html = renderToStaticMarkup(
      <CurriculumCompetencyCatalog
        competencies={mockCompetencies}
        initialMappings={mockMappings}
        userRole="teacher"
      />
    );

    expect(html).toContain("Đã thẩm định");
  });

  it("renders Teacher Edit and Flag buttons only when user is teacher or staff", () => {
    const htmlTeacher = renderToStaticMarkup(
      <CurriculumCompetencyCatalog
        competencies={mockCompetencies}
        initialMappings={mockMappings}
        userRole="teacher"
      />
    );
    expect(htmlTeacher).toContain("Chế độ Giáo viên / Biên tập viên");
    expect(htmlTeacher).toContain("Chỉnh sửa");
    expect(htmlTeacher).toContain("Gắn cờ sai lệch");

    const htmlGuest = renderToStaticMarkup(
      <CurriculumCompetencyCatalog
        competencies={mockCompetencies}
        initialMappings={mockMappings}
        userRole="guest"
      />
    );
    expect(htmlGuest).toContain("Chế độ Khách xem");
    // Should NOT have teacher action buttons
    expect(htmlGuest).not.toContain("Gắn cờ sai lệch");
  });
});
