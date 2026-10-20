/**
 * Accessibility (a11y) & WCAG 2.2 AA Utilities for STTTNNĐ (Lưu Niên — Đại Nội Huế).
 *
 * Implements:
 * - Keyboard navigation helpers (arrow keys, grid navigation, circular wrapping)
 * - Accessible Focus Trap for modals, sheets, and drawers with focus restoration
 * - Live Region Screen Reader Announcement engine with subscription bus
 * - WCAG 2.2 Relative Luminance and Contrast Ratio calculation engine (>= 4.5:1 for AA normal text, >= 3.0:1 for large text / UI)
 * - Verified Imperial Design Tokens contrast audit matrix
 *
 * Reference: 11_WEBSITE_UI_UX_DESIGN_SPEC.md & WCAG 2.2 AA
 */

// ---------------------------------------------------------------------------
// 1. Types & Interfaces
// ---------------------------------------------------------------------------

export type ScreenReaderPoliteness = "polite" | "assertive";

export interface ScreenReaderAnnouncement {
  id: number;
  message: string;
  politeness: ScreenReaderPoliteness;
  timestamp: number;
}

export type AnnouncementSubscriber = (announcement: ScreenReaderAnnouncement) => void;

export type ArrowNavOrientation = "horizontal" | "vertical" | "both" | "grid";

export interface ArrowNavOptions<T = unknown> {
  event: KeyboardEvent | React.KeyboardEvent;
  items: T[];
  currentIndex: number;
  onSelect: (item: T, index: number) => void;
  orientation?: ArrowNavOrientation;
  gridColumns?: number;
  wrap?: boolean;
  preventDefault?: boolean;
}

export interface TrapFocusOptions {
  /** Explicit element to focus initially, or true to focus first focusable child */
  initialFocus?: boolean | HTMLElement;
  /** Whether to restore focus to document.activeElement upon cleanup */
  restoreFocus?: boolean;
  /** Callback fired when the Escape key is pressed */
  onEscape?: () => void;
}

export interface RGBAColor {
  r: number;
  g: number;
  b: number;
  a: number;
}

export type WCAGLevel = "AA" | "AAA";
export type WCAGTextSize = "normal" | "large" | "ui";

export interface WCAGComplianceResult {
  ratio: number;
  passes: boolean;
  requiredRatio: number;
  level: WCAGLevel;
  size: WCAGTextSize;
  message: string;
}

export interface ImperialColorTokenAudit {
  id: string;
  name: string;
  foreground: string;
  background: string;
  purpose: string;
  ratio: number;
  passesAA: boolean;
  passesAAA: boolean;
}

// ---------------------------------------------------------------------------
// 2. Keyboard Navigation Helper: handleArrowNavigation
// ---------------------------------------------------------------------------

/**
 * Handles keyboard arrow navigation across lists, carousels, tabs, or grids.
 * Supports:
 * - ArrowLeft / ArrowRight / ArrowUp / ArrowDown
 * - Home (jump to start) / End (jump to last)
 * - Circular wrap-around or boundary clamping
 * - Grid navigation with configurable column count
 *
 * Supports both options object and positional parameter signatures.
 */
export function handleArrowNavigation<T = unknown>(
  options: ArrowNavOptions<T>,
): number;
export function handleArrowNavigation<T = unknown>(
  event: KeyboardEvent | React.KeyboardEvent,
  items: T[],
  currentIndex: number,
  onSelect: (item: T, index: number) => void,
  options?: Partial<Omit<ArrowNavOptions<T>, "event" | "items" | "currentIndex" | "onSelect">>,
): number;
export function handleArrowNavigation<T = unknown>(
  firstArg: ArrowNavOptions<T> | KeyboardEvent | React.KeyboardEvent,
  itemsArg?: T[],
  currentIndexArg?: number,
  onSelectArg?: (item: T, index: number) => void,
  optionsArg?: Partial<Omit<ArrowNavOptions<T>, "event" | "items" | "currentIndex" | "onSelect">>,
): number {
  let event: KeyboardEvent | React.KeyboardEvent;
  let items: T[];
  let currentIndex: number;
  let onSelect: (item: T, index: number) => void;
  let orientation: ArrowNavOrientation = "both";
  let gridColumns = 1;
  let wrap = true;
  let preventDefault = true;

  if (firstArg && typeof firstArg === "object" && "items" in firstArg) {
    const opts = firstArg as ArrowNavOptions<T>;
    event = opts.event;
    items = opts.items;
    currentIndex = opts.currentIndex;
    onSelect = opts.onSelect;
    if (opts.orientation !== undefined) orientation = opts.orientation;
    if (opts.gridColumns !== undefined) gridColumns = opts.gridColumns;
    if (opts.wrap !== undefined) wrap = opts.wrap;
    if (opts.preventDefault !== undefined) preventDefault = opts.preventDefault;
  } else {
    event = firstArg as KeyboardEvent | React.KeyboardEvent;
    items = itemsArg ?? [];
    currentIndex = currentIndexArg ?? 0;
    onSelect = onSelectArg ?? (() => {});
    if (optionsArg) {
      if (optionsArg.orientation !== undefined) orientation = optionsArg.orientation;
      if (optionsArg.gridColumns !== undefined) gridColumns = optionsArg.gridColumns;
      if (optionsArg.wrap !== undefined) wrap = optionsArg.wrap;
      if (optionsArg.preventDefault !== undefined) preventDefault = optionsArg.preventDefault;
    }
  }

  if (!items || items.length === 0) {
    return currentIndex;
  }

  const length = items.length;
  const key = event.key;
  let nextIndex = currentIndex;
  let handled = false;

  switch (key) {
    case "ArrowRight":
      if (orientation !== "vertical") {
        nextIndex = currentIndex + 1;
        handled = true;
      }
      break;

    case "ArrowLeft":
      if (orientation !== "vertical") {
        nextIndex = currentIndex - 1;
        handled = true;
      }
      break;

    case "ArrowDown":
      if (orientation !== "horizontal") {
        nextIndex = orientation === "grid" ? currentIndex + gridColumns : currentIndex + 1;
        handled = true;
      }
      break;

    case "ArrowUp":
      if (orientation !== "horizontal") {
        nextIndex = orientation === "grid" ? currentIndex - gridColumns : currentIndex - 1;
        handled = true;
      }
      break;

    case "Home":
      nextIndex = 0;
      handled = true;
      break;

    case "End":
      nextIndex = length - 1;
      handled = true;
      break;

    default:
      return currentIndex;
  }

  if (!handled) {
    return currentIndex;
  }

  // Handle bounds
  if (wrap) {
    nextIndex = ((nextIndex % length) + length) % length;
  } else {
    nextIndex = Math.max(0, Math.min(length - 1, nextIndex));
  }

  if (preventDefault && typeof event.preventDefault === "function") {
    event.preventDefault();
  }

  onSelect(items[nextIndex], nextIndex);
  return nextIndex;
}

// ---------------------------------------------------------------------------
// 3. Focus Trap Helper: trapFocus
// ---------------------------------------------------------------------------

const FOCUSABLE_SELECTOR = [
  "a[href]",
  "area[href]",
  "input:not([disabled]):not([type='hidden'])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "button:not([disabled])",
  "iframe",
  "object",
  "embed",
  "[tabindex]:not([tabindex='-1'])",
  "[contenteditable='true']",
].join(", ");

/**
 * Returns an array of visible, non-disabled focusable DOM elements inside container.
 */
export function getFocusableElements(container: HTMLElement): HTMLElement[] {
  if (!container) return [];
  const rawElements = Array.from(
    container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR),
  );

  return rawElements.filter((el) => {
    // Check disabled property
    if ("disabled" in el && (el as HTMLButtonElement).disabled) return false;
    // Check if element is hidden
    if (el.getAttribute("aria-hidden") === "true") return false;
    // Basic visibility check
    if (typeof window !== "undefined" && window.getComputedStyle) {
      const style = window.getComputedStyle(el);
      if (style.display === "none" || style.visibility === "hidden") return false;
    }
    return true;
  });
}

/**
 * Traps keyboard focus within an HTML element (modal, drawer, or dialog).
 * Ensures WCAG 2.2 keyboard navigation compliance (Tab / Shift+Tab cycling).
 * Returns a cleanup function that restores focus to previously active element.
 */
export function trapFocus(
  element: HTMLElement,
  options?: TrapFocusOptions,
): () => void {
  if (!element || typeof document === "undefined") {
    return () => {};
  }

  const previouslyFocused = document.activeElement as HTMLElement | null;

  // Initial focus
  if (options?.initialFocus !== false) {
    if (options?.initialFocus instanceof HTMLElement) {
      options.initialFocus.focus();
    } else {
      const focusables = getFocusableElements(element);
      if (focusables.length > 0) {
        focusables[0].focus();
      } else if (element.tabIndex >= 0) {
        element.focus();
      }
    }
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "Escape" && options?.onEscape) {
      e.preventDefault();
      options.onEscape();
      return;
    }

    if (e.key !== "Tab") return;

    const focusables = getFocusableElements(element);
    if (focusables.length === 0) {
      e.preventDefault();
      return;
    }

    const firstElement = focusables[0];
    const lastElement = focusables[focusables.length - 1];
    const currentActive = document.activeElement;

    if (e.shiftKey) {
      // Shift + Tab: going backwards
      if (currentActive === firstElement || !element.contains(currentActive)) {
        e.preventDefault();
        lastElement.focus();
      }
    } else {
      // Tab: going forwards
      if (currentActive === lastElement || !element.contains(currentActive)) {
        e.preventDefault();
        firstElement.focus();
      }
    }
  };

  element.addEventListener("keydown", handleKeyDown);

  return () => {
    element.removeEventListener("keydown", handleKeyDown);
    if (
      options?.restoreFocus !== false &&
      previouslyFocused &&
      typeof previouslyFocused.focus === "function" &&
      document.body.contains(previouslyFocused)
    ) {
      try {
        previouslyFocused.focus();
      } catch {
        // Silently ignore if focus fails
      }
    }
  };
}

// ---------------------------------------------------------------------------
// 4. Live Region Screen Reader Announcement Engine
// ---------------------------------------------------------------------------

let announcementCounter = 0;
const subscribers = new Set<AnnouncementSubscriber>();

/**
 * Subscribes a listener to receive screen reader announcements.
 * Returns an unsubscribe callback.
 */
export function subscribeScreenReaderAnnouncements(
  subscriber: AnnouncementSubscriber,
): () => void {
  subscribers.add(subscriber);
  return () => {
    subscribers.delete(subscriber);
  };
}

/**
 * Dispatches an accessible announcement to screen readers via ARIA live regions.
 * Works both with React components (via subscriber bus) and standalone fallback DOM containers.
 */
export function announceToScreenReader(
  message: string,
  politeness: ScreenReaderPoliteness = "polite",
  options?: { clearDelay?: number },
): void {
  if (!message || typeof message !== "string" || message.trim() === "") {
    return;
  }

  const cleanMessage = message.trim();
  announcementCounter += 1;
  const payload: ScreenReaderAnnouncement = {
    id: announcementCounter,
    message: cleanMessage,
    politeness,
    timestamp: Date.now(),
  };

  // 1. Notify in-memory subscribers (e.g., ScreenReaderAnnouncer component)
  subscribers.forEach((sub) => {
    try {
      sub(payload);
    } catch (err) {
      console.warn("ScreenReaderAnnouncer subscriber error:", err);
    }
  });

  // 2. Fallback direct DOM injection if in browser and no React listener
  if (typeof document !== "undefined") {
    const regionId =
      politeness === "assertive"
        ? "sr-global-announcer-assertive"
        : "sr-global-announcer-polite";

    let liveRegion = document.getElementById(regionId);
    if (!liveRegion) {
      liveRegion = document.createElement("div");
      liveRegion.id = regionId;
      liveRegion.className = "sr-only";
      liveRegion.setAttribute("aria-live", politeness);
      liveRegion.setAttribute("aria-atomic", "true");
      liveRegion.setAttribute("role", politeness === "assertive" ? "alert" : "status");
      document.body.appendChild(liveRegion);
    }

    // Toggle text with a micro-clear to force ATs to re-read identical messages
    liveRegion.textContent = "";
    requestAnimationFrame(() => {
      if (liveRegion) {
        liveRegion.textContent = cleanMessage;
      }
    });

    const clearDelay = options?.clearDelay ?? 5000;
    if (clearDelay > 0) {
      setTimeout(() => {
        if (liveRegion && liveRegion.textContent === cleanMessage) {
          liveRegion.textContent = "";
        }
      }, clearDelay);
    }
  }
}

// ---------------------------------------------------------------------------
// 5. Specialized Imperial Domain Announcements
// ---------------------------------------------------------------------------

export interface MapNavigationAnnouncementDetails {
  scale?: number;
  zoneName?: string;
  siteName?: string;
  totalSites?: number;
}

/**
 * Announces aerial map pan, zoom, fit, and layer actions in clear Vietnamese.
 */
export function announceMapNavigation(
  action: "pan" | "zoom_in" | "zoom_out" | "fit" | "scale_1to1" | "zone_filter" | "toggle_labels",
  details?: MapNavigationAnnouncementDetails,
): void {
  let message = "";
  switch (action) {
    case "zoom_in":
      message = details?.scale
        ? `Đã phóng to bản đồ đến ${Math.round(details.scale * 100)}%`
        : "Đã phóng to bản đồ";
      break;
    case "zoom_out":
      message = details?.scale
        ? `Đã thu nhỏ bản đồ còn ${Math.round(details.scale * 100)}%`
        : "Đã thu nhỏ bản đồ";
      break;
    case "fit":
      message = "Đã thu phóng toàn bộ Đại Nội vừa vặn khung nhìn";
      break;
    case "scale_1to1":
      message = "Đã đặt tỷ lệ bản đồ về 100% kích thước gốc";
      break;
    case "pan":
      message = details?.zoneName
        ? `Đang chuyển hướng xem khu vực ${details.zoneName}`
        : "Đã di chuyển vị trí bản đồ";
      break;
    case "zone_filter":
      message = details?.zoneName
        ? `Đang lọc hiển thị ${details.totalSites ?? 0} di tích thuộc phân khu ${details.zoneName}`
        : "Đã xoá bộ lọc phân khu, hiển thị tất cả di tích";
      break;
    case "toggle_labels":
      message = "Đã chuyển đổi trạng thái hiển thị nhãn tên công trình";
      break;
  }

  announceToScreenReader(message, "polite");
}

export interface MarkerSelectionDetails {
  name_vi: string;
  name_han_nom?: string;
  zone_name?: string;
  condition?: string;
  learning_level?: string;
}

/**
 * Announces monument pin selection with Vietnamese historical metadata.
 */
export function announceMarkerSelection(details: MarkerSelectionDetails): void {
  const parts = [`Đã chọn di tích: ${details.name_vi}`];
  if (details.name_han_nom) parts.push(`chữ Hán Nôm: ${details.name_han_nom}`);
  if (details.zone_name) parts.push(`thuộc ${details.zone_name}`);
  if (details.condition) parts.push(`tình trạng: ${details.condition}`);
  if (details.learning_level) parts.push(details.learning_level);

  announceToScreenReader(parts.join(", "), "polite");
}

export interface GameFeedbackDetails {
  type: "correct" | "incorrect" | "hint" | "streak" | "level_up" | "complete";
  message?: string;
  points?: number;
  streakCount?: number;
}

/**
 * Announces gamified learning feedback (correct/incorrect answers, XP, streaks).
 */
export function announceGameFeedback(feedback: GameFeedbackDetails): void {
  let message = "";
  let politeness: ScreenReaderPoliteness = "polite";

  switch (feedback.type) {
    case "correct":
      message = feedback.points
        ? `Chính xác! Bạn nhận được ${feedback.points} điểm kinh nghiệm.`
        : "Câu trả lời hoàn toàn chính xác!";
      break;
    case "incorrect":
      message = feedback.message || "Chưa chính xác. Hãy đối chiếu sử liệu và thử lại.";
      politeness = "assertive";
      break;
    case "streak":
      message = feedback.streakCount
        ? `Tuyệt vời! Bạn đã đạt chuỗi học tập ${feedback.streakCount} ngày liên tiếp!`
        : "Chuỗi học tập được duy trì thành công!";
      break;
    case "level_up":
      message = feedback.message || "Chúc mừng! Bạn đã mở khóa cấp độ nghiên cứu mới!";
      politeness = "assertive";
      break;
    case "hint":
      message = feedback.message || "Gợi ý sử liệu đã được mở khóa.";
      break;
    case "complete":
      message = feedback.message || "Chúc mừng bạn đã hoàn thành nhiệm vụ nghiên cứu!";
      break;
  }

  announceToScreenReader(message, politeness);
}

// ---------------------------------------------------------------------------
// 6. WCAG 2.2 Color Parsing & Relative Luminance
// ---------------------------------------------------------------------------

/**
 * Converts HSL color values to sRGB in 0-255 range.
 */
export function hslToRgb(h: number, s: number, l: number): { r: number; g: number; b: number } {
  const normalizedH = ((h % 360) + 360) % 360;
  const clampedS = Math.max(0, Math.min(1, s));
  const clampedL = Math.max(0, Math.min(1, l));

  const c = (1 - Math.abs(2 * clampedL - 1)) * clampedS;
  const x = c * (1 - Math.abs(((normalizedH / 60) % 2) - 1));
  const m = clampedL - c / 2;

  let rPrime = 0;
  let gPrime = 0;
  let bPrime = 0;

  if (normalizedH < 60) {
    rPrime = c;
    gPrime = x;
  } else if (normalizedH < 120) {
    rPrime = x;
    gPrime = c;
  } else if (normalizedH < 180) {
    gPrime = c;
    bPrime = x;
  } else if (normalizedH < 240) {
    gPrime = x;
    bPrime = c;
  } else if (normalizedH < 300) {
    rPrime = x;
    bPrime = c;
  } else {
    rPrime = c;
    bPrime = x;
  }

  return {
    r: Math.round((rPrime + m) * 255),
    g: Math.round((gPrime + m) * 255),
    b: Math.round((bPrime + m) * 255),
  };
}

/**
 * Universal color parser supporting:
 * - Hex: `#fff`, `#ffffff`, `#ffffff80`
 * - RGB / RGBA: `rgb(255, 255, 255)`, `rgba(0,0,0,0.8)`
 * - HSL / HSLA: `hsl(42, 35%, 96%)`, `hsl(42 35% 96%)`, `hsl(42 35% 96% / 0.8)`
 * - CSS Variable HSL triplets: `"42 35% 96%"`, `"222 28% 13%"`
 * - Named colors: `white`, `black`, `transparent`
 */
export function parseColor(color: string): RGBAColor | null {
  if (!color || typeof color !== "string") return null;
  const str = color.trim().toLowerCase();

  // Named colors
  if (str === "white") return { r: 255, g: 255, b: 255, a: 1 };
  if (str === "black") return { r: 0, g: 0, b: 0, a: 1 };
  if (str === "transparent") return { r: 0, g: 0, b: 0, a: 0 };

  // Hex format
  if (str.startsWith("#")) {
    const hex = str.slice(1);
    if (hex.length === 3 || hex.length === 4) {
      const r = parseInt(hex[0] + hex[0], 16);
      const g = parseInt(hex[1] + hex[1], 16);
      const b = parseInt(hex[2] + hex[2], 16);
      const a = hex.length === 4 ? parseInt(hex[3] + hex[3], 16) / 255 : 1;
      return { r, g, b, a };
    }
    if (hex.length === 6 || hex.length === 8) {
      const r = parseInt(hex.slice(0, 2), 16);
      const g = parseInt(hex.slice(2, 4), 16);
      const b = parseInt(hex.slice(4, 6), 16);
      const a = hex.length === 8 ? parseInt(hex.slice(6, 8), 16) / 255 : 1;
      return { r, g, b, a };
    }
  }

  // RGB / RGBA format
  const rgbMatch = str.match(
    /^rgba?\(\s*(\d+)[,\s]+(\d+)[,\s]+(\d+)(?:[,\s/]+([\d.%]+))?\s*\)$/,
  );
  if (rgbMatch) {
    const r = Math.min(255, parseInt(rgbMatch[1], 10));
    const g = Math.min(255, parseInt(rgbMatch[2], 10));
    const b = Math.min(255, parseInt(rgbMatch[3], 10));
    let a = 1;
    if (rgbMatch[4]) {
      a = rgbMatch[4].endsWith("%")
        ? parseFloat(rgbMatch[4]) / 100
        : parseFloat(rgbMatch[4]);
    }
    return { r, g, b, a };
  }

  // HSL / HSLA standard format
  if (str.startsWith("hsl")) {
    const hslMatch = str.match(
      /^hsla?\(\s*([\d.]+)[,\s]+([\d.]+)%[,\s]+([\d.]+)%(?:[,\s/]+([\d.%]+))?\s*\)$/,
    );
    if (hslMatch) {
      const h = parseFloat(hslMatch[1]);
      const s = parseFloat(hslMatch[2]) / 100;
      const l = parseFloat(hslMatch[3]) / 100;
      let a = 1;
      if (hslMatch[4]) {
        a = hslMatch[4].endsWith("%")
          ? parseFloat(hslMatch[4]) / 100
          : parseFloat(hslMatch[4]);
      }
      return { ...hslToRgb(h, s, l), a };
    }
  }

  // Raw Tailwind / shadcn CSS variable triplet format: "42 35% 96%"
  const rawHslMatch = str.match(/^([\d.]+)\s+([\d.]+)%\s+([\d.]+)%$/);
  if (rawHslMatch) {
    const h = parseFloat(rawHslMatch[1]);
    const s = parseFloat(rawHslMatch[2]) / 100;
    const l = parseFloat(rawHslMatch[3]) / 100;
    return { ...hslToRgb(h, s, l), a: 1 };
  }

  return null;
}

/**
 * Calculates relative luminance according to W3C WCAG 2.2 standard:
 * L = 0.2126 * R + 0.7152 * G + 0.0722 * B
 */
export function getRelativeLuminance(rgb: { r: number; g: number; b: number }): number {
  const rs = rgb.r / 255;
  const gs = rgb.g / 255;
  const bs = rgb.b / 255;

  const rLin = rs <= 0.04045 ? rs / 12.92 : Math.pow((rs + 0.055) / 1.055, 2.4);
  const gLin = gs <= 0.04045 ? gs / 12.92 : Math.pow((gs + 0.055) / 1.055, 2.4);
  const bLin = bs <= 0.04045 ? bs / 12.92 : Math.pow((bs + 0.055) / 1.055, 2.4);

  return 0.2126 * rLin + 0.7152 * gLin + 0.0722 * bLin;
}

/**
 * Calculates the WCAG 2.2 contrast ratio between two colors.
 * Formula: (L1 + 0.05) / (L2 + 0.05) where L1 is the lighter color.
 * Returns ratio rounded to 2 decimal places (e.g., 15.58).
 */
export function getContrastRatio(foreground: string, background: string): number {
  const fg = parseColor(foreground);
  const bg = parseColor(background);

  if (!fg || !bg) {
    throw new Error(
      `Không thể tính độ tương phản do định dạng màu không hợp lệ: fg="${foreground}", bg="${background}"`,
    );
  }

  const l1 = getRelativeLuminance(fg);
  const l2 = getRelativeLuminance(bg);

  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);

  const ratio = (lighter + 0.05) / (darker + 0.05);
  return Number(ratio.toFixed(2));
}

/**
 * Verifies whether a color pair complies with WCAG 2.2 AA (or AAA) standards.
 * Thresholds:
 * - AA Normal Text: >= 4.5:1
 * - AA Large Text / UI Components: >= 3.0:1
 * - AAA Normal Text: >= 7.0:1
 * - AAA Large Text: >= 4.5:1
 */
export function checkWCAGCompliance(
  foreground: string,
  background: string,
  options?: {
    level?: WCAGLevel;
    size?: WCAGTextSize;
  },
): WCAGComplianceResult {
  const level = options?.level || "AA";
  const size = options?.size || "normal";
  const ratio = getContrastRatio(foreground, background);

  let requiredRatio = 4.5;
  if (level === "AAA") {
    requiredRatio = size === "large" ? 4.5 : 7.0;
  } else {
    // AA
    requiredRatio = size === "large" || size === "ui" ? 3.0 : 4.5;
  }

  const passes = ratio >= requiredRatio;
  return {
    ratio,
    passes,
    requiredRatio,
    level,
    size,
    message: passes
      ? `Đạt chuẩn WCAG 2.2 ${level} (${ratio}:1 >= ${requiredRatio}:1)`
      : `Không đạt chuẩn WCAG 2.2 ${level} (${ratio}:1 < ${requiredRatio}:1)`,
  };
}

// ---------------------------------------------------------------------------
// 7. Imperial Design Tokens Contrast Matrix
// ---------------------------------------------------------------------------

export interface ImperialColorTokenDefinition {
  id: string;
  name: string;
  foreground: string;
  background: string;
  purpose: string;
}

export const IMPERIAL_DESIGN_TOKENS: ImperialColorTokenDefinition[] = [
  // Light Theme
  {
    id: "light-ink-on-paper",
    name: "Light Theme: Ink on Paper (Body Editorial Text)",
    foreground: "hsl(222 28% 13%)", // #181E2B
    background: "hsl(42 35% 96%)",  // #FAF8F5
    purpose: "Main historical dossiers, archival descriptions, and body reading text",
  },
  {
    id: "light-ink-on-card",
    name: "Light Theme: Ink on Card / Surface",
    foreground: "hsl(222 28% 13%)",
    background: "hsl(42 42% 99%)",
    purpose: "Inspector drawers, floating cards, search dialogs",
  },
  {
    id: "light-deep-navy-on-paper",
    name: "Light Theme: Deep Navy on Paper (Headings)",
    foreground: "hsl(220 24% 12%)", // #171C26
    background: "hsl(42 35% 97%)",
    purpose: "Primary monument titles and section headers",
  },
  {
    id: "light-muted-on-card",
    name: "Light Theme: Muted Ink on Card (Captions & Metadata)",
    foreground: "hsl(220 12% 42%)", // #5E6778
    background: "hsl(42 42% 99%)",
    purpose: "Metadata, source archival units, and auxiliary captions",
  },

  // Dark Theme
  {
    id: "dark-ivory-on-navy",
    name: "Dark Theme: Ivory Text on Deep Navy Background",
    foreground: "hsl(42 26% 94%)", // #F3F1EC
    background: "hsl(220 24% 7%)", // #0E1217
    purpose: "Dark mode body copy and reading text",
  },
  {
    id: "dark-ivory-on-card",
    name: "Dark Theme: Ivory on Dark Card Surface",
    foreground: "hsl(43 33% 94%)",
    background: "hsl(220 20% 10%)",
    purpose: "Dark mode monument drawer and modal content",
  },
  {
    id: "dark-gold-on-navy",
    name: "Dark Theme: Imperial Gold on Deep Navy",
    foreground: "hsl(42 78% 58%)", // #ECC040
    background: "hsl(220 24% 7%)",
    purpose: "Imperial highlights, tags, and prominent titles",
  },
  {
    id: "dark-navy-on-gold-button",
    name: "Dark Theme: Navy text on Imperial Gold Button",
    foreground: "hsl(220 24% 8%)",
    background: "hsl(42 78% 58%)",
    purpose: "High-contrast action button labels",
  },
  {
    id: "dark-muted-on-card",
    name: "Dark Theme: Muted text on Dark Card",
    foreground: "hsl(218 10% 70%)",
    background: "hsl(220 20% 10%)",
    purpose: "Secondary metadata and subtitle text in dark mode",
  },
];

/**
 * Runs an automated accessibility audit against all Imperial Design Tokens.
 * Verifies that each token satisfies WCAG 2.2 AA (>= 4.5:1).
 */
export function auditImperialDesignTokens(): ImperialColorTokenAudit[] {
  return IMPERIAL_DESIGN_TOKENS.map((token) => {
    const ratio = getContrastRatio(token.foreground, token.background);
    return {
      id: token.id,
      name: token.name,
      foreground: token.foreground,
      background: token.background,
      purpose: token.purpose,
      ratio,
      passesAA: ratio >= 4.5,
      passesAAA: ratio >= 7.0,
    };
  });
}
