import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
  handleArrowNavigation,
  trapFocus,
  getFocusableElements,
  subscribeScreenReaderAnnouncements,
  announceToScreenReader,
  announceMapNavigation,
  announceMarkerSelection,
  announceGameFeedback,
  parseColor,
  hslToRgb,
  getRelativeLuminance,
  getContrastRatio,
  checkWCAGCompliance,
  IMPERIAL_DESIGN_TOKENS,
  auditImperialDesignTokens,
  type ScreenReaderAnnouncement,
} from "./a11y-utils";

describe("STTTNNĐ Imperial Accessibility (a11y) & WCAG 2.2 AA", () => {
  // -------------------------------------------------------------------------
  // 1. Keyboard Navigation Logic
  // -------------------------------------------------------------------------
  describe("Keyboard Navigation (handleArrowNavigation)", () => {
    const monuments = [
      "Ngọ Môn",
      "Điện Thái Hòa",
      "Hiển Lâm Các",
      "Thế Miếu",
      "Cung Diên Thọ",
    ];

    it("navigates forward with ArrowRight and backward with ArrowLeft", () => {
      const onSelect = vi.fn();
      const preventDefault = vi.fn();

      // Forward: index 0 -> 1
      const nextIndex = handleArrowNavigation(
        { key: "ArrowRight", preventDefault } as unknown as KeyboardEvent,
        monuments,
        0,
        onSelect,
      );

      expect(nextIndex).toBe(1);
      expect(onSelect).toHaveBeenCalledWith("Điện Thái Hòa", 1);
      expect(preventDefault).toHaveBeenCalled();

      // Backward: index 2 -> 1
      const prevIndex = handleArrowNavigation(
        { key: "ArrowLeft", preventDefault } as unknown as KeyboardEvent,
        monuments,
        2,
        onSelect,
      );

      expect(prevIndex).toBe(1);
      expect(onSelect).toHaveBeenCalledWith("Điện Thái Hòa", 1);
    });

    it("performs circular wrap-around by default", () => {
      const onSelect = vi.fn();

      // Wrap forward from last element to first (index 4 -> 0)
      const wrappedStart = handleArrowNavigation(
        { key: "ArrowRight", preventDefault: vi.fn() } as unknown as KeyboardEvent,
        monuments,
        4,
        onSelect,
      );
      expect(wrappedStart).toBe(0);
      expect(onSelect).toHaveBeenCalledWith("Ngọ Môn", 0);

      // Wrap backward from first element to last (index 0 -> 4)
      const wrappedEnd = handleArrowNavigation(
        { key: "ArrowLeft", preventDefault: vi.fn() } as unknown as KeyboardEvent,
        monuments,
        0,
        onSelect,
      );
      expect(wrappedEnd).toBe(4);
      expect(onSelect).toHaveBeenCalledWith("Cung Diên Thọ", 4);
    });

    it("clamps boundaries without wrap when wrap: false", () => {
      const onSelect = vi.fn();

      // Clamped at end
      const clampedEnd = handleArrowNavigation({
        event: { key: "ArrowRight", preventDefault: vi.fn() } as unknown as KeyboardEvent,
        items: monuments,
        currentIndex: 4,
        onSelect,
        wrap: false,
      });
      expect(clampedEnd).toBe(4);

      // Clamped at start
      const clampedStart = handleArrowNavigation({
        event: { key: "ArrowLeft", preventDefault: vi.fn() } as unknown as KeyboardEvent,
        items: monuments,
        currentIndex: 0,
        onSelect,
        wrap: false,
      });
      expect(clampedStart).toBe(0);
    });

    it("handles Home and End keys for instant boundary jumping", () => {
      const onSelect = vi.fn();

      // Jump to Home (index 0)
      const homeIndex = handleArrowNavigation(
        { key: "Home", preventDefault: vi.fn() } as unknown as KeyboardEvent,
        monuments,
        3,
        onSelect,
      );
      expect(homeIndex).toBe(0);
      expect(onSelect).toHaveBeenCalledWith("Ngọ Môn", 0);

      // Jump to End (index length - 1)
      const endIndex = handleArrowNavigation(
        { key: "End", preventDefault: vi.fn() } as unknown as KeyboardEvent,
        monuments,
        1,
        onSelect,
      );
      expect(endIndex).toBe(4);
      expect(onSelect).toHaveBeenCalledWith("Cung Diên Thọ", 4);
    });

    it("respects orientation restrictions (horizontal vs vertical vs grid)", () => {
      const onSelect = vi.fn();

      // Horizontal orientation ignores ArrowUp / ArrowDown
      const horizontalDown = handleArrowNavigation({
        event: { key: "ArrowDown", preventDefault: vi.fn() } as unknown as KeyboardEvent,
        items: monuments,
        currentIndex: 1,
        onSelect,
        orientation: "horizontal",
      });
      expect(horizontalDown).toBe(1);
      expect(onSelect).not.toHaveBeenCalled();

      // Vertical orientation ignores ArrowLeft / ArrowRight
      const verticalRight = handleArrowNavigation({
        event: { key: "ArrowRight", preventDefault: vi.fn() } as unknown as KeyboardEvent,
        items: monuments,
        currentIndex: 1,
        onSelect,
        orientation: "vertical",
      });
      expect(verticalRight).toBe(1);
      expect(onSelect).not.toHaveBeenCalled();
    });

    it("supports 2D Grid navigation with gridColumns offset", () => {
      const gridItems = ["A", "B", "C", "D", "E", "F"]; // 2 rows x 3 columns
      const onSelect = vi.fn();

      // Moving Down in a 3-column grid steps +3 (from index 1 'B' to index 4 'E')
      const downIndex = handleArrowNavigation({
        event: { key: "ArrowDown", preventDefault: vi.fn() } as unknown as KeyboardEvent,
        items: gridItems,
        currentIndex: 1,
        onSelect,
        orientation: "grid",
        gridColumns: 3,
      });
      expect(downIndex).toBe(4);
      expect(onSelect).toHaveBeenCalledWith("E", 4);

      // Moving Up steps -3 (from index 4 'E' to index 1 'B')
      const upIndex = handleArrowNavigation({
        event: { key: "ArrowUp", preventDefault: vi.fn() } as unknown as KeyboardEvent,
        items: gridItems,
        currentIndex: 4,
        onSelect,
        orientation: "grid",
        gridColumns: 3,
      });
      expect(upIndex).toBe(1);
      expect(onSelect).toHaveBeenCalledWith("B", 1);
    });

    it("ignores non-navigation keys and empty arrays gracefully", () => {
      const onSelect = vi.fn();
      const preventDefault = vi.fn();

      const ignored = handleArrowNavigation(
        { key: "Enter", preventDefault } as unknown as KeyboardEvent,
        monuments,
        2,
        onSelect,
      );
      expect(ignored).toBe(2);
      expect(onSelect).not.toHaveBeenCalled();
      expect(preventDefault).not.toHaveBeenCalled();

      // Empty items
      const emptyResult = handleArrowNavigation(
        { key: "ArrowRight", preventDefault } as unknown as KeyboardEvent,
        [],
        0,
        onSelect,
      );
      expect(emptyResult).toBe(0);
    });
  });

  // -------------------------------------------------------------------------
  // 2. Focus Trap Helper
  // -------------------------------------------------------------------------
  describe.skipIf(typeof document === "undefined")("Focus Trap (trapFocus)", () => {
    let container: HTMLElement;
    let btn1: HTMLButtonElement;
    let input1: HTMLInputElement;
    let link1: HTMLAnchorElement;

    beforeEach(() => {
      container = document.createElement("div");
      btn1 = document.createElement("button");
      btn1.textContent = "Button 1";
      input1 = document.createElement("input");
      input1.type = "text";
      link1 = document.createElement("a");
      link1.href = "#";
      link1.textContent = "Link 1";

      container.appendChild(btn1);
      container.appendChild(input1);
      container.appendChild(link1);
      document.body.appendChild(container);
    });

    afterEach(() => {
      if (document.body.contains(container)) {
        document.body.removeChild(container);
      }
    });

    it("finds all valid focusable elements inside container", () => {
      const disabledBtn = document.createElement("button");
      disabledBtn.disabled = true;
      container.appendChild(disabledBtn);

      const hiddenEl = document.createElement("div");
      hiddenEl.setAttribute("aria-hidden", "true");
      const innerBtn = document.createElement("button");
      hiddenEl.appendChild(innerBtn);
      container.appendChild(hiddenEl);

      const focusables = getFocusableElements(container);
      expect(focusables).toContain(btn1);
      expect(focusables).toContain(input1);
      expect(focusables).toContain(link1);
      expect(focusables).not.toContain(disabledBtn);
      expect(focusables).not.toContain(innerBtn);
    });

    it("focuses initial element upon activation", () => {
      const initialFocus = vi.spyOn(btn1, "focus");
      const cleanup = trapFocus(container, { initialFocus: true });
      expect(initialFocus).toHaveBeenCalled();
      cleanup();
    });

    it("loops focus from last element to first element on Tab", () => {
      const cleanup = trapFocus(container);
      const firstFocus = vi.spyOn(btn1, "focus");

      // Simulate currently on last element (link1)
      vi.spyOn(document, "activeElement", "get").mockReturnValue(link1);

      const tabEvent = new KeyboardEvent("keydown", {
        key: "Tab",
        shiftKey: false,
        bubbles: true,
        cancelable: true,
      });

      const preventDefault = vi.spyOn(tabEvent, "preventDefault");
      container.dispatchEvent(tabEvent);

      expect(preventDefault).toHaveBeenCalled();
      expect(firstFocus).toHaveBeenCalled();
      cleanup();
    });

    it("loops focus from first element to last element on Shift + Tab", () => {
      const cleanup = trapFocus(container);
      const lastFocus = vi.spyOn(link1, "focus");

      // Simulate currently on first element (btn1)
      vi.spyOn(document, "activeElement", "get").mockReturnValue(btn1);

      const shiftTabEvent = new KeyboardEvent("keydown", {
        key: "Tab",
        shiftKey: true,
        bubbles: true,
        cancelable: true,
      });

      const preventDefault = vi.spyOn(shiftTabEvent, "preventDefault");
      container.dispatchEvent(shiftTabEvent);

      expect(preventDefault).toHaveBeenCalled();
      expect(lastFocus).toHaveBeenCalled();
      cleanup();
    });

    it("triggers onEscape callback when Escape key is pressed", () => {
      const onEscape = vi.fn();
      const cleanup = trapFocus(container, { onEscape });

      const escapeEvent = new KeyboardEvent("keydown", {
        key: "Escape",
        bubbles: true,
        cancelable: true,
      });

      container.dispatchEvent(escapeEvent);
      expect(onEscape).toHaveBeenCalledTimes(1);
      cleanup();
    });

    it("restores previously focused element upon cleanup", () => {
      const previousElement = document.createElement("button");
      document.body.appendChild(previousElement);
      const restoreFocusSpy = vi.spyOn(previousElement, "focus");

      vi.spyOn(document, "activeElement", "get").mockReturnValue(previousElement);

      const cleanup = trapFocus(container, { restoreFocus: true });
      cleanup();

      expect(restoreFocusSpy).toHaveBeenCalled();
      document.body.removeChild(previousElement);
    });
  });

  // -------------------------------------------------------------------------
  // 3. Screen Reader Live Region Announcements
  // -------------------------------------------------------------------------
  describe("Screen Reader Announcer Bus", () => {
    it("notifies subscribers of polite and assertive announcements", () => {
      const received: ScreenReaderAnnouncement[] = [];
      const unsubscribe = subscribeScreenReaderAnnouncements((announcement) => {
        received.push(announcement);
      });

      announceToScreenReader("Chào mừng đến với Đại Nội Huế", "polite");
      announceToScreenReader("Chú ý: Cảnh báo thời gian làm bài!", "assertive");

      expect(received.length).toBe(2);
      expect(received[0].message).toBe("Chào mừng đến với Đại Nội Huế");
      expect(received[0].politeness).toBe("polite");
      expect(received[1].message).toBe("Chú ý: Cảnh báo thời gian làm bài!");
      expect(received[1].politeness).toBe("assertive");
      expect(received[1].id).toBeGreaterThan(received[0].id);

      unsubscribe();
      announceToScreenReader("Sau khi hủy đăng ký", "polite");
      expect(received.length).toBe(2);
    });

    it("formats aerial map navigation announcements correctly", () => {
      const received: ScreenReaderAnnouncement[] = [];
      const unsubscribe = subscribeScreenReaderAnnouncements((a) => received.push(a));

      announceMapNavigation("zoom_in", { scale: 1.5 });
      expect(received[received.length - 1].message).toBe("Đã phóng to bản đồ đến 150%");

      announceMapNavigation("zoom_out", { scale: 0.8 });
      expect(received[received.length - 1].message).toBe("Đã thu nhỏ bản đồ còn 80%");

      announceMapNavigation("fit");
      expect(received[received.length - 1].message).toBe(
        "Đã thu phóng toàn bộ Đại Nội vừa vặn khung nhìn",
      );

      announceMapNavigation("zone_filter", {
        zoneName: "Hoàng Thành",
        totalSites: 6,
      });
      expect(received[received.length - 1].message).toBe(
        "Đang lọc hiển thị 6 di tích thuộc phân khu Hoàng Thành",
      );

      unsubscribe();
    });

    it("formats monument marker selection details with Vietnamese metadata", () => {
      const received: ScreenReaderAnnouncement[] = [];
      const unsubscribe = subscribeScreenReaderAnnouncements((a) => received.push(a));

      announceMarkerSelection({
        name_vi: "Ngọ Môn",
        name_han_nom: "午門",
        zone_name: "Trục chính dũng đạo",
        condition: "Nguyên vẹn",
      });

      const last = received[received.length - 1].message;
      expect(last).toContain("Đã chọn di tích: Ngọ Môn");
      expect(last).toContain("chữ Hán Nôm: 午門");
      expect(last).toContain("thuộc Trục chính dũng đạo");
      expect(last).toContain("tình trạng: Nguyên vẹn");

      unsubscribe();
    });

    it("formats gamified learning feedback announcements", () => {
      const received: ScreenReaderAnnouncement[] = [];
      const unsubscribe = subscribeScreenReaderAnnouncements((a) => received.push(a));

      // Correct answer
      announceGameFeedback({ type: "correct", points: 50 });
      expect(received[received.length - 1].message).toBe(
        "Chính xác! Bạn nhận được 50 điểm kinh nghiệm.",
      );
      expect(received[received.length - 1].politeness).toBe("polite");

      // Incorrect answer (assertive)
      announceGameFeedback({
        type: "incorrect",
        message: "Chưa chính xác, hãy tra cứu lại ĐNTL để tìm niên đại.",
      });
      expect(received[received.length - 1].message).toContain("Chưa chính xác");
      expect(received[received.length - 1].politeness).toBe("assertive");

      // Streak celebration
      announceGameFeedback({ type: "streak", streakCount: 5 });
      expect(received[received.length - 1].message).toBe(
        "Tuyệt vời! Bạn đã đạt chuỗi học tập 5 ngày liên tiếp!",
      );

      unsubscribe();
    });
  });

  // -------------------------------------------------------------------------
  // 4. Color Parsing & Contrast Ratio (WCAG 2.2 AA / AAA)
  // -------------------------------------------------------------------------
  describe("Color Parsing & Relative Luminance", () => {
    it("parses hex colors accurately (3, 4, 6, 8 digits)", () => {
      expect(parseColor("#fff")).toEqual({ r: 255, g: 255, b: 255, a: 1 });
      expect(parseColor("#000000")).toEqual({ r: 0, g: 0, b: 0, a: 1 });
      expect(parseColor("#181e2b")).toEqual({ r: 24, g: 30, b: 43, a: 1 });
      expect(parseColor("#ffffff80")?.a).toBeCloseTo(0.5, 1);
    });

    it("parses RGB and RGBA formats", () => {
      expect(parseColor("rgb(255, 255, 255)")).toEqual({
        r: 255,
        g: 255,
        b: 255,
        a: 1,
      });
      expect(parseColor("rgba(24, 30, 43, 0.8)")).toEqual({
        r: 24,
        g: 30,
        b: 43,
        a: 0.8,
      });
    });

    it("parses HSL and raw Tailwind/CSS variable triplets", () => {
      const parsedHsl = parseColor("hsl(42 35% 96%)");
      expect(parsedHsl).toBeDefined();
      expect(parsedHsl?.r).toBeGreaterThan(230);

      // Raw CSS variable: "222 28% 13%"
      const rawTriplet = parseColor("222 28% 13%");
      expect(rawTriplet).toBeDefined();
      expect(rawTriplet?.r).toBeLessThan(50);
      expect(rawTriplet?.b).toBeGreaterThan(rawTriplet?.r ?? 0);
    });

    it("calculates relative luminance according to WCAG 2.2", () => {
      // Pure White: L = 1.0
      expect(getRelativeLuminance({ r: 255, g: 255, b: 255 })).toBe(1.0);

      // Pure Black: L = 0.0
      expect(getRelativeLuminance({ r: 0, g: 0, b: 0 })).toBe(0.0);
    });

    it("calculates contrast ratio conforming to W3C standards", () => {
      // Black vs White = 21:1
      const maxContrast = getContrastRatio("#000000", "#ffffff");
      expect(maxContrast).toBe(21.0);

      // Identical colors = 1:1
      const identicalContrast = getContrastRatio("#181e2b", "#181e2b");
      expect(identicalContrast).toBe(1.0);

      // Commutative property: (A on B) === (B on A)
      const ratioAB = getContrastRatio("#FAF8F5", "#181E2B");
      const ratioBA = getContrastRatio("#181E2B", "#FAF8F5");
      expect(ratioAB).toBe(ratioBA);
    });

    it("verifies compliance thresholds for WCAG 2.2 AA and AAA", () => {
      // High contrast (White on Black) passes both AA and AAA
      const passResult = checkWCAGCompliance("#ffffff", "#000000", {
        level: "AA",
        size: "normal",
      });
      expect(passResult.passes).toBe(true);
      expect(passResult.ratio).toBe(21);
      expect(passResult.requiredRatio).toBe(4.5);

      // Low contrast fails
      const failResult = checkWCAGCompliance("#777777", "#888888", {
        level: "AA",
        size: "normal",
      });
      expect(failResult.passes).toBe(false);
      expect(failResult.ratio).toBeLessThan(4.5);
    });
  });

  // -------------------------------------------------------------------------
  // 5. Imperial Design Tokens Contrast Verification Matrix
  // -------------------------------------------------------------------------
  describe("Imperial Design Tokens WCAG 2.2 AA Audit Matrix", () => {
    it("confirms all Imperial Design Tokens strictly satisfy WCAG 2.2 AA (>= 4.5:1)", () => {
      const auditResults = auditImperialDesignTokens();

      expect(auditResults.length).toBeGreaterThanOrEqual(8);

      auditResults.forEach((token) => {
        expect(
          token.passesAA,
          `Token '${token.name}' contrast ratio ${token.ratio}:1 failed WCAG 2.2 AA (required >= 4.5:1)`,
        ).toBe(true);

        expect(token.ratio).toBeGreaterThanOrEqual(4.5);
      });
    });

    it("verifies Light Theme Paper and Ink achieves > 15:1 contrast", () => {
      const inkOnPaper = getContrastRatio("hsl(222 28% 13%)", "hsl(42 35% 96%)");
      expect(inkOnPaper).toBeGreaterThanOrEqual(15.0);
    });

    it("verifies Dark Theme Ivory on Deep Navy achieves > 15:1 contrast", () => {
      const ivoryOnNavy = getContrastRatio("hsl(42 26% 94%)", "hsl(220 24% 7%)");
      expect(ivoryOnNavy).toBeGreaterThanOrEqual(15.0);
    });

    it("verifies Dark Theme Imperial Gold on Deep Navy achieves > 9:1 contrast", () => {
      const goldOnNavy = getContrastRatio("hsl(42 78% 58%)", "hsl(220 24% 7%)");
      expect(goldOnNavy).toBeGreaterThanOrEqual(9.0);
    });

    it("verifies Dark Theme Button label on Imperial Gold achieves > 9:1 contrast", () => {
      const navyOnGoldBtn = getContrastRatio("hsl(220 24% 8%)", "hsl(42 78% 58%)");
      expect(navyOnGoldBtn).toBeGreaterThanOrEqual(9.0);
    });
  });
});
