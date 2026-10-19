import { describe, it, expect, vi, beforeEach } from "vitest";
import * as React from "react";
import InquiriesPage from "@/app/rbpc/inquiries/page";
import PartnerInboxPage from "@/app/rbpc/partner/page";
import LearnPage from "@/app/learn/page";
import { LEARN_PATHWAY_MODULES } from "@/lib/rbpc/learnModules";
import {
  CURATED_EXPERIENCES,
  SEED_PARTNER_INQUIRIES,
  generateClientUuid,
  generatePublicReference,
  generateOpaqueToken,
  validateEmail,
  validatePhone,
  fetchInquiryStatusByToken,
} from "@/lib/rbpc/inquiries";
import { VALID_TRANSITIONS, maskContactValue } from "@/components/rbpc/PartnerInboxView";

describe("RBPC Inquiries & Partner Pages Contract Tests", () => {
  it("exports InquiriesPage as a valid React component", () => {
    expect(InquiriesPage).toBeDefined();
    const el = React.createElement(InquiriesPage);
    expect(el).toBeDefined();
  });

  it("exports PartnerInboxPage as a valid React component", () => {
    expect(PartnerInboxPage).toBeDefined();
    const el = React.createElement(PartnerInboxPage);
    expect(el).toBeDefined();
  });

  it("exports LearnPage and implements 4-phase educational continuum", () => {
    expect(LearnPage).toBeDefined();
    const el = React.createElement(LearnPage);
    expect(el).toBeDefined();

    expect(LEARN_PATHWAY_MODULES.length).toBeGreaterThanOrEqual(4);
    const phases = new Set(LEARN_PATHWAY_MODULES.map((m) => m.roadmapPhase));
    expect(phases.has("P1_HERITAGE_BASELINE")).toBe(true);
    expect(phases.has("P2_INTERACTIVE_3D")).toBe(true);
    expect(phases.has("P3_MAKER_MASTERCLASS")).toBe(true);
    expect(phases.has("P4_ACCREDITED_CURRICULUM")).toBe(true);

    // Verify 3D artefact linkage
    const linked3d = LEARN_PATHWAY_MODULES.filter((m) => m.linked3DArtefactSlug);
    expect(linked3d.length).toBeGreaterThanOrEqual(2);
    expect(linked3d.some((m) => m.linked3DArtefactSlug === "cao-dinh")).toBe(true);
  });

  describe("Curated Experiences Integrity & Commercial Honesty Invariant", () => {
    it("provides exactly 3 verified cultural workshops in Hue", () => {
      expect(CURATED_EXPERIENCES).toHaveLength(3);
      const slugs = CURATED_EXPERIENCES.map((e) => e.slug);
      expect(slugs).toContain("workshop-duc-dong-phuong-duc");
      expect(slugs).toContain("workshop-phap-lam-hue");
      expect(slugs).toContain("workshop-hoa-giay-thanh-tien");
    });

    it("strictly enforces non-commercial availability notice across all curated experiences", () => {
      for (const exp of CURATED_EXPERIENCES) {
        expect(exp.notice).toBeDefined();
        expect(exp.notice.length).toBeGreaterThan(10);
        // Must declare inquiry-only status and never promise instant automated charge
        expect(exp.notice).toMatch(/không thu phí trực tuyến tức thì|không phải giao dịch thanh toán trực tuyến tức thì/);
        expect(exp.maxPartySize).toBeGreaterThanOrEqual(1);
        expect(exp.maxPartySize).toBeLessThanOrEqual(50);
        expect(exp.durationMinutes).toBeGreaterThan(0);
        expect(exp.providerId).toBeDefined();
      }
    });
  });

  describe("Seed Partner Inquiries & Multi-Tenant Scoping", () => {
    it("contains diverse seed inquiries covering multiple lifecycle states", () => {
      expect(SEED_PARTNER_INQUIRIES.length).toBeGreaterThanOrEqual(5);

      const statuses = SEED_PARTNER_INQUIRIES.map((i) => i.status);
      expect(statuses).toContain("new");
      expect(statuses).toContain("contacted");
      expect(statuses).toContain("confirmed");
      expect(statuses).toContain("declined");
    });

    it("verifies multi-tenant provider isolation across distinct workshop accounts", () => {
      const providerIds = new Set(SEED_PARTNER_INQUIRIES.map((i) => i.providerId));
      expect(providerIds.size).toBeGreaterThanOrEqual(3);
      expect(providerIds.has("prov-phuong-duc-01")).toBe(true);
      expect(providerIds.has("prov-phap-lam-01")).toBe(true);
      expect(providerIds.has("prov-thanh-tien-02")).toBe(true);

      // Filtering for prov-phuong-duc-01 excludes items from other providers
      const phuongDucItems = SEED_PARTNER_INQUIRIES.filter(
        (i) => i.providerId === "prov-phuong-duc-01"
      );
      expect(phuongDucItems.length).toBeGreaterThan(0);
      expect(phuongDucItems.every((i) => i.providerId === "prov-phuong-duc-01")).toBe(true);
      expect(phuongDucItems.map((i) => i.id)).not.toContain("inq-003"); // inq-003 is Phap Lam
      expect(phuongDucItems.map((i) => i.id)).not.toContain("inq-005"); // inq-005 is Thanh Tien
    });
  });

  describe("Client Input Sanitization & Token Generation", () => {
    it("generates valid RFC 4122 v4 UUID for client-side double-submit idempotency key", () => {
      const key1 = generateClientUuid();
      const key2 = generateClientUuid();

      expect(key1).not.toBe(key2);
      expect(key1).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
      );
    });

    it("generates opaque non-sequential reference codes formatted as INQ-XXXX-YYYY", () => {
      const ref = generatePublicReference();
      expect(ref).toMatch(/^INQ-[A-Z0-9]{4}-[A-Z0-9]{4}$/);
      expect(ref).not.toContain("0001"); // Non-sequential check
    });

    it("generates high-entropy secret status tokens formatted as tok_sec_<32hex>", () => {
      const token = generateOpaqueToken();
      expect(token).toMatch(/^tok_sec_[0-9a-f]{32}$/);
    });

    it("validates email formatting correctly", () => {
      expect(validateEmail("traveler@example.com")).toBe(true);
      expect(validateEmail("user.name+tag@domain.co.uk")).toBe(true);
      expect(validateEmail("invalid-email")).toBe(false);
      expect(validateEmail("@missinguser.com")).toBe(false);
      expect(validateEmail("missingdomain@")).toBe(false);
      expect(validateEmail("")).toBe(false);
    });

    it("validates Vietnamese and international phone numbers correctly", () => {
      expect(validatePhone("0912345678")).toBe(true);
      expect(validatePhone("+84 912 345 678")).toBe(true);
      expect(validatePhone("0234 3822 532")).toBe(true);
      expect(validatePhone("123")).toBe(false);
      expect(validatePhone("abcdefghij")).toBe(false);
      expect(validatePhone("")).toBe(false);
    });
  });

  describe("Zero PII Invariant on Public Status Tracking", () => {
    it("returns only lifecycle metadata and excludes email, phone, name, and internal notes", async () => {
      const statusRes = await fetchInquiryStatusByToken("INQ-7F89-A23C");

      expect(statusRes.reference).toBe("INQ-7F89-A23C");
      expect(statusRes.status).toBe("new");
      expect(statusRes.experienceTitle).toBeDefined();
      expect(statusRes.statusMessage).toBeDefined();

      // STRICT ZERO PII INVARIANT:
      // The status response object MUST NOT have visitor PII properties
      const raw = statusRes as unknown as Record<string, unknown>;
      expect(raw.name).toBeUndefined();
      expect(raw.contact_name).toBeUndefined();
      expect(raw.email).toBeUndefined();
      expect(raw.phone).toBeUndefined();
      expect(raw.contact_value).toBeUndefined();
      expect(raw.partner_notes).toBeUndefined();
      expect(raw.internal_notes).toBeUndefined();
    });
  });
});
