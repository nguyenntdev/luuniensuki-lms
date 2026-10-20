"""Accessibility & WCAG 2.2 AA Verification Tests for STTTNNĐ (Lưu Niên — Đại Nội Huế).

Validates:
- Delivery of the 4 requested a11y modules per SPEC V5.1 and 11_WEBSITE_UI_UX_DESIGN_SPEC.md:
  1. frontend/src/components/imperial/a11y/SkipToContent.tsx
  2. frontend/src/lib/imperial/a11y-utils.ts
  3. frontend/src/components/imperial/a11y/ScreenReaderAnnouncer.tsx
  4. frontend/src/lib/imperial/accessibility.test.ts
- Verification of WCAG 2.2 relative luminance and contrast calculations (>= 4.5:1 for AA normal text)
- Verification of Imperial Design Tokens contrast compliance.
"""

import math
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"


def test_accessibility_files_exist():
    """Verify that all four required a11y files exist in the project."""
    skip_to_content = FRONTEND_SRC / "components" / "imperial" / "a11y" / "SkipToContent.tsx"
    a11y_utils = FRONTEND_SRC / "lib" / "imperial" / "a11y-utils.ts"
    sr_announcer = FRONTEND_SRC / "components" / "imperial" / "a11y" / "ScreenReaderAnnouncer.tsx"
    a11y_test = FRONTEND_SRC / "lib" / "imperial" / "accessibility.test.ts"

    assert skip_to_content.is_file(), f"Missing file: {skip_to_content}"
    assert a11y_utils.is_file(), f"Missing file: {a11y_utils}"
    assert sr_announcer.is_file(), f"Missing file: {sr_announcer}"
    assert a11y_test.is_file(), f"Missing file: {a11y_test}"


def test_skip_to_content_implementation():
    """Verify SkipToContent component adheres to WCAG 2.2 Success Criterion 2.4.1 (Bypass Blocks)."""
    skip_file = FRONTEND_SRC / "components" / "imperial" / "a11y" / "SkipToContent.tsx"
    content = skip_file.read_text(encoding="utf-8")

    assert "export default function SkipToContent" in content
    assert "targetId" in content
    assert "label" in content
    assert "sr-only" in content
    assert "focus:not-sr-only" in content
    assert "focus:fixed" in content
    assert "tabindex" in content or "tabIndex" in content
    assert "announceToScreenReader" in content


def test_a11y_utils_contract():
    """Verify a11y-utils.ts exports all required keyboard, focus, announcer, and contrast utilities."""
    utils_file = FRONTEND_SRC / "lib" / "imperial" / "a11y-utils.ts"
    content = utils_file.read_text(encoding="utf-8")

    # Required functions from spec
    assert "export function handleArrowNavigation" in content
    assert "export function trapFocus" in content
    assert "export function announceToScreenReader" in content
    assert "export function getRelativeLuminance" in content
    assert "export function getContrastRatio" in content
    assert "export function checkWCAGCompliance" in content
    assert "export function parseColor" in content
    assert "export const IMPERIAL_DESIGN_TOKENS" in content
    assert "export function auditImperialDesignTokens" in content


def test_screen_reader_announcer_contract():
    """Verify ScreenReaderAnnouncer.tsx implements polite and assertive live regions."""
    announcer_file = FRONTEND_SRC / "components" / "imperial" / "a11y" / "ScreenReaderAnnouncer.tsx"
    content = announcer_file.read_text(encoding="utf-8")

    assert "export default function ScreenReaderAnnouncer" in content
    assert 'aria-live="polite"' in content
    assert 'aria-live="assertive"' in content
    assert 'role="status"' in content
    assert 'role="alert"' in content
    assert 'aria-atomic="true"' in content
    assert "subscribeScreenReaderAnnouncements" in content
    assert "useScreenReaderAnnouncer" in content


def test_layout_integrates_a11y_components():
    """Verify ImperialLayout includes SkipToContent and ScreenReaderAnnouncer."""
    layout_file = FRONTEND_SRC / "app" / "dai-noi" / "layout.tsx"
    content = layout_file.read_text(encoding="utf-8")

    assert "SkipToContent" in content
    assert "ScreenReaderAnnouncer" in content
    assert 'id="imperial-main-content"' in content


# ---------------------------------------------------------------------------
# Mathematical WCAG 2.2 Contrast Ratio Verification
# ---------------------------------------------------------------------------

def srgb_to_linear(channel_255: int) -> float:
    """Converts 8-bit sRGB color channel to linear luminance channel per WCAG 2.2."""
    c = channel_255 / 255.0
    if c <= 0.04045:
        return c / 12.92
    return math.pow((c + 0.055) / 1.055, 2.4)


def relative_luminance(r: int, g: int, b: int) -> float:
    """Calculates relative luminance L = 0.2126 * R + 0.7152 * G + 0.0722 * B."""
    r_lin = srgb_to_linear(r)
    g_lin = srgb_to_linear(g)
    b_lin = srgb_to_linear(b)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def wcag_contrast_ratio(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]) -> float:
    """Calculates WCAG 2.2 contrast ratio (L1 + 0.05) / (L2 + 0.05)."""
    l1 = relative_luminance(*rgb1)
    l2 = relative_luminance(*rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def hsl_to_rgb(h: float, s: float, l: float) -> tuple[int, int, int]:
    """Converts HSL to sRGB tuple (0-255)."""
    h_norm = ((h % 360) + 360) % 360
    c = (1.0 - abs(2.0 * l - 1.0)) * s
    x = c * (1.0 - abs(((h_norm / 60.0) % 2.0) - 1.0))
    m = l - c / 2.0

    if h_norm < 60:
        r_p, g_p, b_p = c, x, 0.0
    elif h_norm < 120:
        r_p, g_p, b_p = x, c, 0.0
    elif h_norm < 180:
        r_p, g_p, b_p = 0.0, c, x
    elif h_norm < 240:
        r_p, g_p, b_p = 0.0, x, c
    elif h_norm < 300:
        r_p, g_p, b_p = x, 0.0, c
    else:
        r_p, g_p, b_p = c, 0.0, x

    return (
        round((r_p + m) * 255),
        round((g_p + m) * 255),
        round((b_p + m) * 255),
    )


def test_wcag_luminance_extremes():
    """Verify luminance calculations for pure white (1.0) and black (0.0)."""
    white_lum = relative_luminance(255, 255, 255)
    black_lum = relative_luminance(0, 0, 0)

    assert pytest.approx(white_lum, abs=0.001) == 1.0
    assert pytest.approx(black_lum, abs=0.001) == 0.0

    ratio = wcag_contrast_ratio((255, 255, 255), (0, 0, 0))
    assert ratio == 21.0


def test_imperial_design_tokens_pass_wcag_aa():
    """Verify all imperial theme tokens exceed WCAG 2.2 AA contrast threshold (>= 4.5:1)."""
    # Tokens defined in globals.css and a11y-utils.ts:
    tokens = {
        # Light theme
        "light_ink_on_paper": {
            "fg": hsl_to_rgb(222, 0.28, 0.13),  # hsl(222 28% 13%)
            "bg": hsl_to_rgb(42, 0.35, 0.96),   # hsl(42 35% 96%)
            "min_expected": 4.5,
        },
        "light_ink_on_card": {
            "fg": hsl_to_rgb(222, 0.28, 0.13),  # hsl(222 28% 13%)
            "bg": hsl_to_rgb(42, 0.42, 0.99),   # hsl(42 42% 99%)
            "min_expected": 4.5,
        },
        "light_muted_on_card": {
            "fg": hsl_to_rgb(220, 0.12, 0.42),  # hsl(220 12% 42%)
            "bg": hsl_to_rgb(42, 0.42, 0.99),   # hsl(42 42% 99%)
            "min_expected": 4.5,
        },
        # Dark theme
        "dark_ivory_on_navy": {
            "fg": hsl_to_rgb(42, 0.26, 0.94),   # hsl(42 26% 94%)
            "bg": hsl_to_rgb(220, 0.24, 0.07),  # hsl(220 24% 7%)
            "min_expected": 4.5,
        },
        "dark_ivory_on_card": {
            "fg": hsl_to_rgb(43, 0.33, 0.94),   # hsl(43 33% 94%)
            "bg": hsl_to_rgb(220, 0.20, 0.10),  # hsl(220 20% 10%)
            "min_expected": 4.5,
        },
        "dark_gold_on_navy": {
            "fg": hsl_to_rgb(42, 0.78, 0.58),   # hsl(42 78% 58%)
            "bg": hsl_to_rgb(220, 0.24, 0.07),  # hsl(220 24% 7%)
            "min_expected": 4.5,
        },
        "dark_navy_on_gold_button": {
            "fg": hsl_to_rgb(220, 0.24, 0.08),  # hsl(220 24% 8%)
            "bg": hsl_to_rgb(42, 0.78, 0.58),   # hsl(42 78% 58%)
            "min_expected": 4.5,
        },
        "dark_muted_on_card": {
            "fg": hsl_to_rgb(218, 0.10, 0.70),  # hsl(218 10% 70%)
            "bg": hsl_to_rgb(220, 0.20, 0.10),  # hsl(220 20% 10%)
            "min_expected": 4.5,
        },
    }

    for name, data in tokens.items():
        ratio = wcag_contrast_ratio(data["fg"], data["bg"])
        assert ratio >= data["min_expected"], (
            f"Token '{name}' contrast ratio {ratio}:1 is below required {data['min_expected']}:1"
        )
