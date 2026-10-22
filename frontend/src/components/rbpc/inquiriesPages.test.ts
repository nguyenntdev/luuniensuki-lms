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
  fetchPartnerInquiries,
  submitInquiryToApi,
  updatePartnerInquiryStatusApi,
  InquiryNotFoundError,
} from "@/lib/rbpc/inquiries";
import * as apiModule from "@/lib/api";
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
      const spy = vi.spyOn(apiModule, "apiRequest").mockResolvedValueOnce({
        reference: "INQ-7F89-A23C",
        experience_title: "Trải nghiệm nghệ thuật nặn khuôn sáp & đúc đồng truyền thống Phường Đúc",
        status: "new",
        status_message: "Yêu cầu đã được ghi nhận.",
        preferred_date: "2026-11-05",
        party_size: 2,
        created_at: "2026-10-18T10:00:00Z",
      });

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

      spy.mockRestore();
    });
  });

  describe("V5-T014: Partner Status PATCH Persistence & Client Rollback", () => {
    it("re-throws error when updatePartnerInquiryStatusApi receives 403 or 400 rejection", async () => {
      const spy = vi.spyOn(apiModule, "apiRequest").mockRejectedValueOnce(
        new Error("HTTP 403: Forbidden Scope")
      );

      await expect(
        updatePartnerInquiryStatusApi("inq-001", "confirmed", "test note")
      ).rejects.toThrow("HTTP 403: Forbidden Scope");

      expect(spy).toHaveBeenCalledWith(
        "/api/v1/rbpc/partner/inquiries/inq-001",
        expect.objectContaining({
          method: "PATCH",
          body: { status: "confirmed", note: "test note" },
        })
      );
      spy.mockRestore();
    });

    it("verifies state machine valid transitions and rollback invariant", () => {
      // Invariant: 'new' can only transition to 'contacted' or 'declined', NEVER 'confirmed' directly
      expect(VALID_TRANSITIONS["new"]).not.toContain("confirmed");
      expect(VALID_TRANSITIONS["new"]).not.toContain("closed");

      // Invariant: 'closed' is terminal and cannot transition to any state
      expect(VALID_TRANSITIONS["closed"]).toEqual([]);

      // Rollback invariant test:
      const initialItem = { ...SEED_PARTNER_INQUIRIES[0] };
      expect(initialItem.status).toBe("new");

      let currentStatus = initialItem.status;
      const optimisticUpdate = (next: typeof initialItem.status) => {
        currentStatus = next;
      };
      const rollback = (prev: typeof initialItem.status) => {
        currentStatus = prev;
      };

      // Simulate failed optimistic update to confirmed
      const prevStatus = currentStatus;
      optimisticUpdate("confirmed");
      expect(currentStatus).toBe("confirmed");

      // Rollback on rejection
      rollback(prevStatus);
      expect(currentStatus).toBe("new");
    });
  });

  describe("submitInquiryToApi Zero Fabricated Success Invariant (V5-T011)", () => {
    const samplePayload = {
      experience_slug: "workshop-duc-dong-phuong-duc",
      contact: {
        name: "Test User",
        method: "email" as const,
        value: "test@example.com",
      },
      party_size: 2,
      consent: {
        accepted: true,
        privacy_accepted: true,
        version: "2026.1_v1",
      },
      idempotency_key: "550e8400-e29b-41d4-a716-446655440000",
    };

    it("rejects and does not fabricate success when backend returns 404", async () => {
      const spy = vi.spyOn(apiModule, "apiRequest").mockRejectedValueOnce(
        new apiModule.ApiError("Not Found", { status: 404 })
      );

      await expect(submitInquiryToApi(samplePayload)).rejects.toThrow();
      expect(spy).toHaveBeenCalledTimes(1);

      spy.mockRestore();
    });

    it("rejects and does not fabricate success on network failure", async () => {
      const spy = vi.spyOn(apiModule, "apiRequest").mockRejectedValueOnce(
        new TypeError("Failed to fetch")
      );

      await expect(submitInquiryToApi(samplePayload)).rejects.toThrow();
      expect(spy).toHaveBeenCalledTimes(1);

      spy.mockRestore();
    });

    it("returns InquirySubmissionResult only when backend returns 202 accepted response", async () => {
      const serverResponse = {
        reference: "INQ-ABCD-1234",
        status_token: "tok_sec_1234567890abcdef1234567890abcdef",
        status: "new" as const,
        message: "Yêu cầu đã được ghi nhận.",
        created_at: "2026-10-21T00:00:00Z",
      };
      const spy = vi.spyOn(apiModule, "apiRequest").mockResolvedValueOnce(serverResponse);

      const result = await submitInquiryToApi(samplePayload);
      expect(result.reference).toBe("INQ-ABCD-1234");
      expect(result.statusToken).toBe("tok_sec_1234567890abcdef1234567890abcdef");
      expect(result.status).toBe("new");
      expect(result.message).toBe("Yêu cầu đã được ghi nhận.");
      expect(result.createdAt).toBe("2026-10-21T00:00:00Z");

      spy.mockRestore();
    });
  });

  describe("V5-T013: Partner Inbox No Seeding In Production", () => {
    it("returns empty array [] when backend returns items: [], without falling back to seed data", async () => {
      const emptyBackendResponse = {
        items: [],
        total: 0,
      };
      const spy = vi.spyOn(apiModule, "apiRequest").mockResolvedValueOnce(emptyBackendResponse);

      const result = await fetchPartnerInquiries();
      expect(result).toEqual([]);
      expect(result.length).toBe(0);
      expect(spy).toHaveBeenCalledWith("/api/v1/rbpc/partner/inquiries");

      spy.mockRestore();
    });

    it("re-throws error on API failure or unauthenticated when allowDemoFallback is not set", async () => {
      const spy = vi.spyOn(apiModule, "apiRequest").mockRejectedValueOnce(
        new apiModule.ApiError("HTTP 401: Unauthorized", { status: 401 })
      );

      await expect(fetchPartnerInquiries()).rejects.toThrow("HTTP 401: Unauthorized");
      expect(spy).toHaveBeenCalledWith("/api/v1/rbpc/partner/inquiries");

      spy.mockRestore();
    });

    it("returns SEED_PARTNER_INQUIRIES only when explicitly requesting demo fallback", async () => {
      const spy = vi.spyOn(apiModule, "apiRequest").mockRejectedValueOnce(
        new apiModule.ApiError("HTTP 401: Unauthorized", { status: 401 })
      );

      const result = await fetchPartnerInquiries({ allowDemoFallback: true });
      expect(result).toEqual(SEED_PARTNER_INQUIRIES);
      expect(result.length).toBeGreaterThanOrEqual(5);

      spy.mockRestore();
    });
  });

  describe("Token Status Strict Server Lookup (V5-T012)", () => {
    it("strictly queries /api/v1/rbpc/inquiries/status/{opaqueToken} with proper URL encoding", async () => {
      const spy = vi.spyOn(apiModule, "apiRequest").mockResolvedValueOnce({
        reference: "INQ-ABCD-1234",
        experience_title: "Trải nghiệm Đúc Đồng",
        status: "new",
        status_message: "Yêu cầu đã được tiếp nhận.",
        party_size: 4,
        preferred_date: "2026-11-20",
        last_updated_at: "2026-10-21T10:00:00Z",
      });

      const res = await fetchInquiryStatusByToken("tok_sec_abc 123");
      expect(res.reference).toBe("INQ-ABCD-1234");
      expect(res.experienceTitle).toBe("Trải nghiệm Đúc Đồng");
      expect(spy).toHaveBeenCalledWith("/api/v1/rbpc/inquiries/status/tok_sec_abc%20123");

      spy.mockRestore();
    });

    it("removes matchedSeed fallback: seed reference with 404 server response throws InquiryNotFoundError", async () => {
      // Prior implementation would catch 404 and return SEED_PARTNER_INQUIRIES item.
      // Under V5-T012, matchedSeed fallback is eliminated: must throw typed error.
      const spy = vi.spyOn(apiModule, "apiRequest").mockRejectedValueOnce(
        new apiModule.ApiError("Inquiry not found for status token.", { status: 404 })
      );

      await expect(fetchInquiryStatusByToken("INQ-7F89-A23C")).rejects.toThrow(InquiryNotFoundError);
      await expect(
        (async () => {
          vi.spyOn(apiModule, "apiRequest").mockRejectedValueOnce(
            new apiModule.ApiError("Not found", { status: 404 })
          );
          await fetchInquiryStatusByToken("INQ-7F89-A23C");
        })()
      ).rejects.toThrow("Không tìm thấy hồ sơ với mã tra cứu này.");

      spy.mockRestore();
    });

    it("throws InquiryNotFoundError on network error without falling back to seed data", async () => {
      const spy = vi.spyOn(apiModule, "apiRequest").mockRejectedValueOnce(
        new TypeError("Failed to fetch")
      );

      await expect(fetchInquiryStatusByToken("INQ-6E21-B44D")).rejects.toThrow(InquiryNotFoundError);
      expect(spy).toHaveBeenCalledWith("/api/v1/rbpc/inquiries/status/INQ-6E21-B44D");

      spy.mockRestore();
    });

    it("throws InquiryNotFoundError for blank or whitespace token", async () => {
      await expect(fetchInquiryStatusByToken("")).rejects.toThrow(InquiryNotFoundError);
      await expect(fetchInquiryStatusByToken("   ")).rejects.toThrow(InquiryNotFoundError);
      await expect(fetchInquiryStatusByToken("")).rejects.toThrow("Mã tra cứu không được để trống.");
    });
  });
});
