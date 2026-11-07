"use client";

import React, { useState } from "react";
import {
  MANDATORY_METHODOLOGY_DISCLAIMER_EN,
  MANDATORY_METHODOLOGY_DISCLAIMER_VI,
  scrubPii,
  validateMethodologyDisclaimer,
  type AnonymizedFeedbackSubmission,
  type CohortType,
} from "@/lib/rbpc/discoveryExperiments";

export interface DiscoveryFeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (feedback: AnonymizedFeedbackSubmission) => void;
  taskIdOrScriptId: string;
  targetCohort: CohortType;
  locale?: "vi" | "en";
  initialDwellSeconds?: number;
}

export function DiscoveryFeedbackModal({
  isOpen,
  onClose,
  onSubmit,
  taskIdOrScriptId,
  targetCohort,
  locale = "vi",
  initialDwellSeconds = 0,
}: DiscoveryFeedbackModalProps) {
  const [participantToken, setParticipantToken] = useState<string>(() => {
    // Generate valid default anonymous token e.g. FIT-A1B2
    const prefix = targetCohort === "artisan_partner" ? "ART" : targetCohort === "heritage_educator" ? "EDU" : "FIT";
    const randHex = Math.random().toString(36).substring(2, 6).toUpperCase();
    return `${prefix}-${randHex}`;
  });

  const [ratingLikert, setRatingLikert] = useState<number>(5);
  const [qualitativeText, setQualitativeText] = useState<string>("");
  const [taskCompleted, setTaskCompleted] = useState<boolean>(true);
  const [consentAccepted, setConsentAccepted] = useState<boolean>(true);
  const [claimRepresentative, setClaimRepresentative] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  if (!isOpen) return null;

  const disclaimerText =
    locale === "vi" ? MANDATORY_METHODOLOGY_DISCLAIMER_VI : MANDATORY_METHODOLOGY_DISCLAIMER_EN;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (!consentAccepted) {
      setErrorMsg(
        locale === "vi"
          ? "Bạn cần đồng ý với điều khoản nghiên cứu ẩn danh để tiếp tục."
          : "You must accept anonymous research consent to proceed."
      );
      return;
    }

    // Negative abuse check: If claimed representative, enforce disclaimer
    try {
      if (claimRepresentative) {
        validateMethodologyDisclaimer("VOLUNTARY_OPT_IN", true, disclaimerText);
      }
    } catch (err: any) {
      setErrorMsg(err.message);
      return;
    }

    // Scrub qualitative feedback
    const { cleanedText } = scrubPii(qualitativeText);

    const submission: AnonymizedFeedbackSubmission = {
      record_id: `rec_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      participant_token: participantToken.trim().toUpperCase(),
      cohort: targetCohort,
      task_or_script_id: taskIdOrScriptId,
      task_completed: taskCompleted,
      dwell_seconds: initialDwellSeconds,
      rating_likert: ratingLikert,
      qualitative_feedback: cleanedText,
      consent_accepted: true,
      consent_version: "rbpc-discovery-v1",
      timestamp: new Date().toISOString(),
      is_self_selected: true,
    };

    onSubmit(submission);
    onClose();
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="discovery-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      data-testid="discovery-feedback-modal"
    >
      <div className="w-full max-w-xl rounded-xl border border-amber-900/30 bg-[#FAF7F2] p-6 text-stone-900 shadow-2xl">
        <div className="flex items-center justify-between border-b border-amber-900/10 pb-3">
          <h2 id="discovery-modal-title" className="font-serif text-xl font-bold text-amber-950">
            {locale === "vi" ? "Đóng Góp Ý Kiến Thử Nghiệm Khám Phá" : "Customer Discovery Usability Feedback"}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="text-stone-500 hover:text-stone-800"
            aria-label="Close"
          >
            ✕
          </button>
        </div>

        {/* Mandatory Methodology Disclaimer Notice */}
        <div
          className="my-4 rounded-lg border border-amber-800/20 bg-amber-50/80 p-3 text-xs text-amber-900"
          data-testid="methodology-disclaimer-box"
        >
          <p className="font-semibold uppercase tracking-wider text-amber-950">
            {locale === "vi" ? "Tuyên bố Phương pháp luận (Bắt buộc):" : "Methodology Disclaimer (Mandatory):"}
          </p>
          <p className="mt-1 leading-relaxed">{disclaimerText}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-stone-700">
              {locale === "vi" ? "Mã Định Danh Ẩn Danh (Token):" : "Anonymous Subject Token:"}
            </label>
            <input
              type="text"
              value={participantToken}
              onChange={(e) => setParticipantToken(e.target.value)}
              className="mt-1 w-full rounded border border-stone-300 bg-white px-3 py-1.5 font-mono text-sm uppercase"
              data-testid="participant-token-input"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700">
              {locale === "vi" ? "Đánh giá mức độ hài lòng / độ tin cậy (1 - 5):" : "Trust / Satisfaction Rating (1 - 5 Likert):"}
            </label>
            <div className="mt-1 flex gap-4" data-testid="likert-rating-group">
              {[1, 2, 3, 4, 5].map((val) => (
                <label key={val} className="flex cursor-pointer items-center gap-1 text-sm font-medium">
                  <input
                    type="radio"
                    name="likert"
                    value={val}
                    checked={ratingLikert === val}
                    onChange={() => setRatingLikert(val)}
                  />
                  <span>{val}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700">
              {locale === "vi" ? "Nhiệm vụ hoàn tất thành công?" : "Task Completed Successfully?"}
            </label>
            <label className="mt-1 flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={taskCompleted}
                onChange={(e) => setTaskCompleted(e.target.checked)}
                data-testid="task-completed-checkbox"
              />
              <span>{locale === "vi" ? "Đã hoàn tất theo đúng tiêu chí" : "Completed according to success criteria"}</span>
            </label>
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700">
              {locale === "vi" ? "Nhận xét chi tiết (Hệ thống tự động xóa PII):" : "Qualitative Feedback (Auto-PII scrubbed):"}
            </label>
            <textarea
              rows={3}
              value={qualitativeText}
              onChange={(e) => setQualitativeText(e.target.value)}
              placeholder={
                locale === "vi"
                  ? "Ví dụ: Giao diện dễ hiểu, nút gửi yêu cầu ghi rõ 0 đồng nên rất an tâm..."
                  : "e.g., Clear source drawer, zero upfront notice removed payment anxiety..."
              }
              className="mt-1 w-full rounded border border-stone-300 bg-white p-2 text-sm"
              data-testid="qualitative-feedback-input"
            />
          </div>

          {/* Negative Abuse Checkbox */}
          <div className="rounded border border-stone-200 bg-stone-50 p-2.5">
            <label className="flex items-start gap-2 text-xs text-stone-700">
              <input
                type="checkbox"
                checked={claimRepresentative}
                onChange={(e) => setClaimRepresentative(e.target.checked)}
                data-testid="claim-representative-checkbox"
              />
              <span>
                {locale === "vi"
                  ? "Đính kèm xác nhận phương pháp luận (Ngăn chặn việc ngộ nhận mẫu tự nguyện là đại diện toàn thể dân tộc/du khách)."
                  : "Attach methodology compliance confirmation (Prohibits treating self-selected cohort as general population)."}
              </span>
            </label>
          </div>

          {/* Consent Checkbox */}
          <div>
            <label className="flex items-center gap-2 text-xs font-medium text-stone-700">
              <input
                type="checkbox"
                checked={consentAccepted}
                onChange={(e) => setConsentAccepted(e.target.checked)}
                data-testid="consent-checkbox"
              />
              <span>
                {locale === "vi"
                  ? "Tôi đồng ý lưu trữ phản hồi nghiên cứu ẩn danh theo điều khoản rbpc-discovery-v1."
                  : "I agree to store anonymous discovery feedback under policy rbpc-discovery-v1."}
              </span>
            </label>
          </div>

          {errorMsg && (
            <p className="text-xs font-semibold text-red-600" data-testid="error-message">
              {errorMsg}
            </p>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded px-4 py-2 text-xs font-semibold text-stone-600 hover:bg-stone-200"
            >
              {locale === "vi" ? "Hủy" : "Cancel"}
            </button>
            <button
              type="submit"
              className="rounded bg-amber-800 px-4 py-2 text-xs font-semibold text-white shadow hover:bg-amber-900"
              data-testid="submit-feedback-btn"
            >
              {locale === "vi" ? "Gửi Ý Kiến Ẩn Danh" : "Submit Anonymous Feedback"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

DiscoveryFeedbackModal.displayName = "DiscoveryFeedbackModal";
