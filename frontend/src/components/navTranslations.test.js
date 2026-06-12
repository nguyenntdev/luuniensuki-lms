import { describe, it, expect } from "vitest";
import { translations, translate } from "./navTranslations";

// Property 10 (Roundtrip i18n) — security-hardening design.md:
//   For every nav key k that differs by language, `t_en(k) != t_vi(k)`,
//   and `t(lang)(missing) === missing`.
//
// Validates: Requirements 22.1, 27.1
//
// The nav translation domain is a small, fixed set of keys, so these tests
// enumerate the entire key space exhaustively rather than sampling it — the
// strongest possible check of the property over its real domain.

// Keys legitimately identical across languages (e.g. brand names) would be
// allowlisted here. Today every nav string differs between vi and en, so the
// allowlist is empty and the per-key inequality assertion is exact.
const IDENTICAL_ACROSS_LANGUAGES = new Set();

const viKeys = Object.keys(translations.vi);
const enKeys = Object.keys(translations.en);
const sharedKeys = viKeys.filter((k) => k in translations.en);

describe("nav i18n tables (Req 22.1, 22.3)", () => {
  it("defines both vi and en tables", () => {
    expect(translations.vi).toBeTypeOf("object");
    expect(translations.en).toBeTypeOf("object");
    expect(viKeys.length).toBeGreaterThan(0);
    expect(enKeys.length).toBeGreaterThan(0);
  });

  it("every shared key maps to a non-empty string in both languages", () => {
    for (const key of sharedKeys) {
      expect(translations.vi[key], `vi[${key}]`).toBeTypeOf("string");
      expect(translations.en[key], `en[${key}]`).toBeTypeOf("string");
      expect(translations.vi[key].trim().length, `vi[${key}] non-empty`).toBeGreaterThan(0);
      expect(translations.en[key].trim().length, `en[${key}] non-empty`).toBeGreaterThan(0);
    }
  });

  it("the en table is NOT identical to the vi table (the original bug had en === vi)", () => {
    // The pre-fix bug duplicated the Vietnamese strings into the English table.
    // At least one shared key must differ; in practice all of them do.
    const anyDiffer = sharedKeys.some((k) => translations.en[k] !== translations.vi[k]);
    expect(anyDiffer).toBe(true);
    expect(translations.en).not.toEqual(translations.vi);
  });

  it("EN differs from VI for every shared key (Property 10: t_en(k) != t_vi(k))", () => {
    for (const key of sharedKeys) {
      if (IDENTICAL_ACROSS_LANGUAGES.has(key)) continue;
      expect(
        translate("en", key),
        `en and vi must differ for ${key}`,
      ).not.toBe(translate("vi", key));
    }
  });
});

describe("nav i18n key coverage (Req 22.3)", () => {
  it("every vi key also exists in en", () => {
    const missingInEn = viKeys.filter((k) => !(k in translations.en));
    expect(missingInEn).toEqual([]);
  });

  it("every en key also exists in vi", () => {
    const missingInVi = enKeys.filter((k) => !(k in translations.vi));
    expect(missingInVi).toEqual([]);
  });
});

describe("translate() safe missing-key fallback (Property 10: t(lang)(missing) === missing, Req 22.2)", () => {
  it("returns the key unchanged for a missing key in en", () => {
    expect(translate("en", "__nonexistent_key__")).toBe("__nonexistent_key__");
  });

  it("returns the key unchanged for a missing key in vi", () => {
    expect(translate("vi", "__nonexistent_key__")).toBe("__nonexistent_key__");
  });

  it("returns the key unchanged for an unknown language", () => {
    // translations["xx"] is undefined; optional chaining + `?? key` must hold.
    expect(translate("xx", "nav.dashboard")).toBe("nav.dashboard");
  });

  it("does not throw for any combination of unknown lang/key", () => {
    expect(() => translate(undefined, undefined)).not.toThrow();
    expect(translate(undefined, "nav.profile")).toBe("nav.profile");
  });

  it("resolves real keys to their translated value", () => {
    expect(translate("en", "nav.dashboard")).toBe("Learn");
    expect(translate("vi", "nav.dashboard")).toBe("Học tập");
  });
});
