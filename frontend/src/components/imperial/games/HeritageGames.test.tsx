import React from "react";
import { describe, it, expect } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { HeritageGames } from "./HeritageGames";
import { TimelineSequenceGame } from "./TimelineSequenceGame";
import { ImperialCipherGame } from "./ImperialCipherGame";
import { HeritageDetectiveWidget } from "@/components/imperial/detective/HeritageDetectiveWidget";
import { FALLBACK_CLUES, FALLBACK_GAME_QUESTIONS } from "@/lib/imperial/games-data";

describe("Heritage Games Component Suite (HeritageGames.test.tsx)", () => {
  it("renders HeritageGames with all 4 standardized mini-game mode tabs", () => {
    const html = renderToStaticMarkup(
      <HeritageGames initialQuestions={FALLBACK_GAME_QUESTIONS} defaultGameCategory="quiz" />,
    );

    // 4 Primary Game Mode Buttons
    expect(html).toContain("Trắc nghiệm di sản");
    expect(html).toContain("Thám tử cổ vật");
    expect(html).toContain("Sắp xếp niên biểu");
    expect(html).toContain("Giải mã mật mã");

    // Live score counter badge
    expect(html).toContain("Điểm tích lũy:");
  });

  it("renders TimelineSequenceGame with touch-friendly up/down reordering controls and hints", () => {
    const html = renderToStaticMarkup(<TimelineSequenceGame />);

    expect(html).toContain("Năng Lực S2 — Sắp Xếp Niên Biểu Di Sản");
    expect(html).toContain("Dùng các nút ▲ ▼ để sắp xếp các sự kiện theo đúng thứ tự thời gian");
    expect(html).toContain("Kiểm tra thứ tự");
    expect(html).toContain("Mở manh mối");

    // Accessible ARIA labels for touch reordering
    expect(html).toContain("Di chuyển lên trước");
    expect(html).toContain("Di chuyển xuống sau");
  });

  it("renders ImperialCipherGame with historical story, prompt, and word bank tokens", () => {
    const html = renderToStaticMarkup(<ImperialCipherGame />);

    expect(html).toContain("Năng Lực S3 &amp; S4 — Giải Mã Mật Mã Cung Đình");
    expect(html).toContain("Bối cảnh di sản &amp; Sử ký triều Nguyễn:");
    expect(html).toContain("Khu vực giải mã mật thư:");
    expect(html).toContain("Kho từ khóa ngự chế &amp; Mảnh ghép mật mã");
    expect(html).toContain("Giải mã mật thư");
    expect(html).toContain("Gợi ý văn tự");
  });

  it("renders HeritageDetectiveWidget with candidate target buttons for high school students", () => {
    const clue = FALLBACK_CLUES[0];
    const html = renderToStaticMarkup(<HeritageDetectiveWidget clue={clue} />);

    expect(html).toContain("Thám tử di sản Đại Nội");
    expect(html).toContain(clue.title);
    expect(html).toContain("Gửi dự đoán công trình:");
    expect(html).toContain("Điện Thái Hòa");
    expect(html).toContain("Ngọ Môn");
    expect(html).toContain("Hiển Lâm Các");
  });
});
