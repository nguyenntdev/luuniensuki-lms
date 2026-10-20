import React from "react";
import { describe, it, expect } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import PrintableFieldworkWorksheet from "./PrintableFieldworkWorksheet";
import {
  ALL_16_PRINTABLE_STATIONS,
  STANDARD_4_STATIONS_SLUGS,
  STATION_CLUSTERS,
  RUBRIC_DIMENSIONS,
  EXIT_TICKET_QUESTIONS,
} from "./worksheetData";
import { WorksheetPrintConfig } from "./types";

describe("PrintableFieldworkWorksheet Component (STTT-SPEC-PWA-PRINT-001)", () => {
  const baseConfig: WorksheetPrintConfig = {
    school_name: "TRƯỜNG THPT CHUYÊN QUỐC HỌC HUẾ",
    department_name: "Tổ Lịch sử - Địa lý",
    lesson_code: "KHTN-LS10-DN01",
    grade_level: "Lớp 10 THPT",
    class_name: "10 Sử",
    student_name: "Nguyễn Văn An",
    teacher_name: "Thầy Lê Văn B",
    date_vi: "16/10/2026",
    orientation: "landscape",
    teacher_key_mode: false,
    include_qr: true,
    include_rubric: true,
    include_exit_ticket: true,
    selected_monument_slugs: STANDARD_4_STATIONS_SLUGS,
  };

  const standardStations = ALL_16_PRINTABLE_STATIONS.filter((s) =>
    STANDARD_4_STATIONS_SLUGS.includes(s.monument_slug),
  );

  it("renders standard 4-station student worksheet with official 5512/BGDĐT administrative header", () => {
    const html = renderToStaticMarkup(
      <PrintableFieldworkWorksheet
        stations={standardStations}
        config={baseConfig}
      />,
    );

    // Administrative Header
    expect(html).toContain("SỞ GIÁO DỤC VÀ ĐÀO TẠO THỪA THIÊN HUẾ");
    expect(html).toContain("TRƯỜNG THPT CHUYÊN QUỐC HỌC HUẾ");
    expect(html).toContain("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM");
    expect(html).toContain("Độc lập – Tự do – Hạnh phúc");
    expect(html).toContain("KHTN-LS10-DN01");
    expect(html).toContain("Công văn 5512/BGDĐT");

    // Mode title
    expect(html).toContain("PHIẾU HỌC TẬP THỰC ĐỊA — BẢN LÀM BÀI CỦA HỌC SINH");

    // Student Metadata
    expect(html).toContain("Nguyễn Văn An");
    expect(html).toContain("10 Sử");
    expect(html).toContain("Thầy Lê Văn B");

    // 4 Columns
    expect(html).toContain("CỘT 1");
    expect(html).toContain("TRẠM QUAN SÁT &amp; VỊ TRÍ TRÊN BẢN ĐỒ");
    expect(html).toContain("CỘT 2");
    expect(html).toContain("HIỆN TRẠNG MẮT THẤY TẠI THỰC ĐỊA");
    expect(html).toContain("CỘT 3");
    expect(html).toContain("TƯ LIỆU CHÍNH SỬ ĐỐI CHIẾU");
    expect(html).toContain("CỘT 4");
    expect(html).toContain("EM KẾT LUẬN GÌ (MÔ HÌNH M - E - E)");

    // Standard stations
    expect(html).toContain("Ngọ Môn");
    expect(html).toContain("Điện Thái Hòa");
    expect(html).toContain("Hiển Lâm Các");
    expect(html).toContain("Cung Diên Thọ");

    // Student writing lines in blank mode
    expect(html).toContain("border-dotted");
    expect(html).toContain("Ghi chép hiện trạng tại thực địa");

    // Exit ticket & Rubric
    expect(html).toContain("EXIT TICKET");
    expect(html).toContain("KHUNG ĐÁNH GIÁ NĂNG LỰC LỊCH SỬ (RUBRIC S1 – S4)");
  });

  it("renders teacher key mode with suggested answers, source analysis and full score rubric", () => {
    const teacherConfig: WorksheetPrintConfig = {
      ...baseConfig,
      teacher_key_mode: true,
    };

    const html = renderToStaticMarkup(
      <PrintableFieldworkWorksheet
        stations={standardStations}
        config={teacherConfig}
      />,
    );

    // Teacher header badge
    expect(html).toContain("HỒ SƠ GIÁO VIÊN — HƯỚNG DẪN CHẤM &amp; ĐÁP ÁN CHUẨN (TEACHER KEY)");
    expect(html).toContain("12 / 12 (Đáp án)");

    // Teacher suggested answers
    expect(html).toContain("[Gợi ý hiện trạng mắt thấy - Giáo viên]");
    expect(html).toContain("Phân tích sử liệu:");
    expect(html).toContain("Mệnh đề lịch sử (Claim - 1đ)");
    expect(html).toContain("Bằng chứng đối chiếu (Evidence - 1đ)");
    expect(html).toContain("Giới hạn kiểm chứng thêm (Epistemic Boundary - 1đ)");
  });

  it("renders QR codes when include_qr is enabled and hides them when disabled", () => {
    const withQrHtml = renderToStaticMarkup(
      <PrintableFieldworkWorksheet
        stations={standardStations}
        config={baseConfig}
      />,
    );
    expect(withQrHtml).toContain("<svg");
    expect(withQrHtml).toContain("Bản đồ số Đại Nội");

    const noQrHtml = renderToStaticMarkup(
      <PrintableFieldworkWorksheet
        stations={standardStations}
        config={{ ...baseConfig, include_qr: false }}
      />,
    );
    expect(noQrHtml).not.toContain("Bản đồ số Đại Nội");
  });

  it("supports all 16 monuments across the 4 royal zones without crashing", () => {
    expect(ALL_16_PRINTABLE_STATIONS.length).toBe(16);

    const html = renderToStaticMarkup(
      <PrintableFieldworkWorksheet
        stations={ALL_16_PRINTABLE_STATIONS}
        config={{
          ...baseConfig,
          selected_monument_slugs: ALL_16_PRINTABLE_STATIONS.map((s) => s.monument_slug),
        }}
      />,
    );

    ALL_16_PRINTABLE_STATIONS.forEach((st) => {
      expect(html).toContain(st.monument_name_vi);
      expect(html).toContain(st.primary_source.source_title);
    });
  });

  it("verifies cluster definitions and rubric dimensions integrity", () => {
    expect(STATION_CLUSTERS.length).toBeGreaterThanOrEqual(4);
    expect(RUBRIC_DIMENSIONS.map((d) => d.id)).toEqual(["S1", "S2", "S3", "S4"]);
    expect(EXIT_TICKET_QUESTIONS.length).toBe(2);
  });
});
