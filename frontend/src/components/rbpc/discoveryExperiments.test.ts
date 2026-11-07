import { describe, it, expect, vi } from "vitest";
import * as React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  CANONICAL_DISCOVERY_EXPERIMENTS,
  CANONICAL_USABILITY_TASKS,
  MANDATORY_METHODOLOGY_DISCLAIMER_EN,
  MANDATORY_METHODOLOGY_DISCLAIMER_VI,
  scrubPii,
  validateMethodologyDisclaimer,
} from "@/lib/rbpc/discoveryExperiments";
import { DiscoveryFeedbackModal } from "./DiscoveryFeedbackModal";

describe("Customer Discovery Experiments & Usability Tasks Contract (V5-T114)", () => {
  it("defines 5 canonical pre-registered experiments with falsification triggers", () => {
    expect(CANONICAL_DISCOVERY_EXPERIMENTS).toHaveLength(5);
    const expIds = CANONICAL_DISCOVERY_EXPERIMENTS.map((e) => e.experiment_id);
    expect(expIds).toEqual(["EXP-01", "EXP-02", "EXP-03", "EXP-04", "EXP-05"]);

    for (const exp of CANONICAL_DISCOVERY_EXPERIMENTS) {
      expect(exp.hypothesis).toBeTruthy();
      expect(exp.metric_name).toBeTruthy();
      expect(exp.formula).toBeTruthy();
      expect(exp.target_threshold).toBeGreaterThan(0);
      expect(exp.falsification_trigger).toBeGreaterThan(0);
      expect(exp.status).toBe("PRE_REGISTERED");
      expect(exp.sample_size_target).toBeGreaterThan(0);
    }
  });

  it("defines 4 standardized usability tasks with zero upfront check", () => {
    expect(CANONICAL_USABILITY_TASKS).toHaveLength(4);
    const taskIds = CANONICAL_USABILITY_TASKS.map((t) => t.task_id);
    expect(taskIds).toEqual(["TASK-01", "TASK-02", "TASK-03", "TASK-04"]);

    const task01 = CANONICAL_USABILITY_TASKS.find((t) => t.task_id === "TASK-01");
    expect(task01?.zero_upfront_check).toBe(true);
    expect(task01?.max_dwell_seconds).toBe(180);
    expect(task01?.steps.length).toBeGreaterThanOrEqual(5);
  });

  it("scrubs PII such as emails, phone numbers, IPs, and full names", () => {
    const raw = "My email is visitor@example.com, phone 0912345678, IP 192.168.1.100. Contact Nguyễn Văn A.";
    const { cleanedText, piiDetected } = scrubPii(raw);

    expect(piiDetected).toBe(true);
    expect(cleanedText).not.toContain("visitor@example.com");
    expect(cleanedText).not.toContain("0912345678");
    expect(cleanedText).not.toContain("192.168.1.100");
    expect(cleanedText).not.toContain("Nguyễn Văn A");
    expect(cleanedText).toContain("[EMAIL_REDACTED]");
    expect(cleanedText).toContain("[PHONE_REDACTED]");
    expect(cleanedText).toContain("[IP_REDACTED]");
  });

  describe("Negative Abuse Guardrail: Non-Representativeness Disclaimer", () => {
    it("allows convenience sample when NOT claimed representative", () => {
      const valid = validateMethodologyDisclaimer("CONVENIENCE", false, null);
      expect(valid).toBe(true);
    });

    it("allows convenience sample when claimed representative IF full methodology disclaimer is present", () => {
      const valid = validateMethodologyDisclaimer("VOLUNTARY_OPT_IN", true, MANDATORY_METHODOLOGY_DISCLAIMER_EN);
      expect(valid).toBe(true);
    });

    it("throws error when claimed representative WITHOUT disclaimer", () => {
      expect(() => {
        validateMethodologyDisclaimer("CONVENIENCE", true, "");
      }).toThrowError(/Self-selected respondents cannot be labeled representative/);
    });

    it("throws error when disclaimer lacks sampling disclosure", () => {
      const defective = "Selection bias exists and cannot be extrapolated to the general population.";
      expect(() => {
        validateMethodologyDisclaimer("PURPOSIVE_SELF_SELECTED", true, defective);
      }).toThrowError(/missing sampling methodology disclosure/);
    });

    it("throws error when disclaimer lacks selection bias disclosure", () => {
      const defective = "Convenience sample cannot be extrapolated to the general population without randomized stratified sampling.";
      expect(() => {
        validateMethodologyDisclaimer("VOLUNTARY_OPT_IN", true, defective);
      }).toThrowError(/missing selection bias disclosure/);
    });

    it("throws error when disclaimer lacks extrapolation prohibition", () => {
      const defective = "Convenience sample with early adopter selection bias.";
      expect(() => {
        validateMethodologyDisclaimer("CONVENIENCE", true, defective);
      }).toThrowError(/missing population extrapolation limitation/);
    });
  });

  describe("DiscoveryFeedbackModal Component", () => {
    it("renders modal with mandatory disclaimer and anonymous inputs", () => {
      const html = renderToStaticMarkup(
        React.createElement(DiscoveryFeedbackModal, {
          isOpen: true,
          onClose: () => {},
          onSubmit: () => {},
          taskIdOrScriptId: "TASK-01",
          targetCohort: "cultural_traveler",
          locale: "vi",
        })
      );

      expect(html).toContain("Tuyên bố Phương pháp luận (Bắt buộc)");
      expect(html).toContain("Mã Định Danh Ẩn Danh (Token)");
      expect(html).toContain("Đánh giá mức độ hài lòng / độ tin cậy");
      expect(html).toContain("Gửi Ý Kiến Ẩn Danh");
      expect(html).toContain("rbpc-discovery-v1");
    });

    it("renders English version correctly", () => {
      const html = renderToStaticMarkup(
        React.createElement(DiscoveryFeedbackModal, {
          isOpen: true,
          onClose: () => {},
          onSubmit: () => {},
          taskIdOrScriptId: "TASK-01",
          targetCohort: "cultural_traveler",
          locale: "en",
        })
      );

      expect(html).toContain("Methodology Disclaimer (Mandatory):");
      expect(html).toContain("Customer Discovery Usability Feedback");
      expect(html).toContain("Anonymous Subject Token:");
      expect(html).toContain("Submit Anonymous Feedback");
    });

    it("returns null when isOpen is false", () => {
      const html = renderToStaticMarkup(
        React.createElement(DiscoveryFeedbackModal, {
          isOpen: false,
          onClose: () => {},
          onSubmit: () => {},
          taskIdOrScriptId: "TASK-01",
          targetCohort: "cultural_traveler",
        })
      );
      expect(html).toBe("");
    });
  });
});
