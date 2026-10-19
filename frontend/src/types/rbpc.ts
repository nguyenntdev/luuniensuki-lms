/**
 * LƯU NIÊN — RBPC 2026: Frontend Create, Learn & Commercial Slice Type Contracts
 * Document Scope: Typescript definitions for stories, creators, experiences, inquiries, and partner inbox.
 * Base Specification: Master Execution Goal V2 (§4.2, §4.4, §5.3, §5.4) & CREATE_LEARN_SPEC.md
 *
 * Design Principles:
 * - Epistemic Honesty: Explicit separation between historical fact, living testimony, and commercial request.
 * - Polymorphic Blocks: Discriminator-based polymorphic content blocks including the core `artisan_bridge`.
 * - Zero PII on Public Endpoints: Public status tracking uses high-entropy opaque tokens and reference codes.
 * - Idempotency & Rate-Limiting: Client UUID v4 for double-submit prevention.
 */

// ============================================================================
// 1. Common & Primitive Types
// ============================================================================

export type RbpcLocale = "vi" | "en";

export interface LocalizedField<T = string> {
  vi: T;
  en?: T;
}

export type IsoDateString = string; // Format: YYYY-MM-DD
export type IsoDateTimeString = string; // ISO 8601 UTC timestamp
export type UuidString = string; // UUID v4 format

export type ContentScope = "RBPC_HUE" | "CUU_DINH";

export type EpistemicCertainty =
  | "high"
  | "medium"
  | "contested"
  | "insufficient_sources";

export type SupportType =
  | "direct"
  | "contextual"
  | "interpretation"
  | "unverified";

export type ReviewStatus =
  | "draft"
  | "in_review"
  | "verified"
  | "published_human_approved"
  | "withdrawn";

// ============================================================================
// 2. Creator (Artisan) & Consent Types
// ============================================================================

export type ConsentStatus =
  | "consented"
  | "verified_written_consent"
  | "revoked";

export type VerificationBadgeType =
  | "written_consent"
  | "community_verified"
  | "master_artisan"
  | "heritage_guild";

export interface VerificationBadge {
  type: VerificationBadgeType;
  label: LocalizedField;
  verifiedAt: IsoDateTimeString;
  verifiedBy?: string;
  documentRef?: string;
  tooltip: LocalizedField;
}

export interface OralHistoryRecording {
  audioUrl?: string;
  durationSeconds?: number;
  recordedAt?: IsoDateString;
  interviewer?: string;
  consentGranted: boolean;
  transcriptExcerpt?: LocalizedField;
  fullTranscriptUrl?: string;
  topicsCovered?: string[];
}

export interface RbpcCreator {
  id: UuidString;
  slug: string;
  publicName: string;
  craftTradition: LocalizedField;
  approvedBio: LocalizedField;
  approvedPortraitUrl?: string;
  portraitAlt?: string;
  publicRegion: string;
  consentStatus: ConsentStatus;
  verificationBadge?: VerificationBadge;
  verificationBadges?: VerificationBadge[];
  yearsOfPractice?: number;
  generationLineage?: string;
  oralHistory?: OralHistoryRecording;
  displayConsentId?: string;
  approvedStorySlugs: string[];
  experienceSlugs: string[];
  linkedExperiences?: RbpcExperience[];
  heritagePlaceSlug?: string;
  languagePreferences?: string[];
  createdAt: IsoDateTimeString;
  updatedAt?: IsoDateTimeString;
}

// ============================================================================
// 3. Experience Listing & Pricing Types
// ============================================================================

export type AvailabilityMode = "inquiry_only" | "disabled";

export interface PricingDisplay {
  isFree: boolean;
  amount?: number;
  currency: "VND" | "USD";
  displayFormatted: string; // e.g. "Từ 350.000 VNĐ / khách" or "From $15 / guest"
  pricingUnit: "per_person" | "per_group" | "fixed";
  notes?: LocalizedField;
}

export type SyllabusActivityType =
  | "demonstration"
  | "hands_on"
  | "historical_discussion"
  | "tea_reflection";

export interface WorkshopSyllabusStep {
  stepNumber: number;
  title: LocalizedField;
  durationMinutes?: number;
  description: LocalizedField;
  activityType: SyllabusActivityType;
}

export interface RbpcExperience {
  id: UuidString;
  slug: string;
  creatorSlug: string;
  creatorName: string;
  providerId?: UuidString;
  providerName?: string;
  title: LocalizedField;
  description: LocalizedField;
  syllabus: WorkshopSyllabusStep[];
  areaPublic: string;
  fullAddressPublic?: string;
  durationMinutes: number;
  pricing: PricingDisplay;
  availabilityMode: AvailabilityMode;
  maxPartySize: number;
  minPartySize?: number;
  languagesSupported: string[];
  notice: string; // Transparency notice: "Yêu cầu trải nghiệm chỉ là bước liên hệ xác nhận, không phải giao dịch thanh toán tức thì."
  cancellationPolicyText?: LocalizedField;
  accessibilityNotes?: LocalizedField;
  whatIncluded?: string[];
  whatToBring?: string[];
  lastConfirmedAt?: IsoDateTimeString;
  publicationState: "draft" | "published" | "archived";
  createdAt: IsoDateTimeString;
  updatedAt: IsoDateTimeString;
}

// ============================================================================
// 4. Polymorphic Story Blocks & Chapters
// ============================================================================

export type StoryBlockType =
  | "text"
  | "image"
  | "quote"
  | "source_excerpt"
  | "cultural_context"
  | "model_3d"
  | "artisan_bridge"
  | "comparison"
  | "callout"
  | "reflection_prompt"
  | "audio_recording"
  | "video_clip";

export interface BaseStoryBlock {
  id: string;
  type: StoryBlockType;
  order?: number;
}

export interface TextStoryBlock extends BaseStoryBlock {
  type: "text";
  title?: string;
  body: string;
  format?: "markdown" | "plain";
}

export interface ImageStoryBlock extends BaseStoryBlock {
  type: "image";
  url: string;
  altText: string;
  caption?: string;
  credit?: string;
  rightsRef?: string;
  aspect?: "16:9" | "4:3" | "1:1" | "original";
}

export interface QuoteStoryBlock extends BaseStoryBlock {
  type: "quote";
  quote: string;
  speaker: string;
  roleOrLineage?: string;
  sourceCitation?: string;
}

export interface SourceExcerptStoryBlock extends BaseStoryBlock {
  type: "source_excerpt";
  sourceTitle: string;
  originalText: string;
  modernTranslation?: string;
  locator?: string;
  certainty: EpistemicCertainty;
  claimId?: string;
  sourceUrl?: string;
}

export interface CulturalContextStoryBlock extends BaseStoryBlock {
  type: "cultural_context";
  title: string;
  era?: string;
  significance: string;
  heritagePlaceSlug?: string;
  heritagePlaceName?: string;
}

export interface Model3DStoryBlock extends BaseStoryBlock {
  type: "model_3d";
  modelId: string;
  title: string;
  creatorCredit: string;
  license: string;
  embedUrl?: string;
  stillPhotoFallbackUrl: string;
  accuracyGrade:
    | "survey_grade"
    | "measured_photogrammetry"
    | "historian_reviewed"
    | "illustrative_only"
    | "unreviewed"
    | "rejected_accuracy";
}

/**
 * Polymorphic artisan_bridge block:
 * Connects the historical narrative directly to a living craft master and their experience offering.
 */
export interface ArtisanBridgeStoryBlock extends BaseStoryBlock {
  type: "artisan_bridge";
  creatorSlug: string;
  creatorName: string;
  craftTradition: LocalizedField;
  portraitUrl?: string;
  bridgeNarrative: LocalizedField; // Explains continuity from imperial past to today's living practitioner
  consentStatus: ConsentStatus;
  verificationBadge?: VerificationBadge;
  experienceSlug?: string;
  experienceTitle?: LocalizedField;
  experiencePriceDisplay?: string;
  ctaLabel?: LocalizedField;
}

export interface ComparisonStoryBlock extends BaseStoryBlock {
  type: "comparison";
  historical: {
    title: string;
    description: string;
    imageUrl?: string;
  };
  contemporary: {
    title: string;
    description: string;
    imageUrl?: string;
  };
  synthesisNote?: string;
}

export interface CalloutStoryBlock extends BaseStoryBlock {
  type: "callout";
  tone: "info" | "warning" | "cultural_note" | "epistemic";
  title?: string;
  body: string;
}

export interface ReflectionPromptStoryBlock extends BaseStoryBlock {
  type: "reflection_prompt";
  question: string;
  helperText?: string;
  suggestedFollowups?: string[];
}

export interface AudioRecordingStoryBlock extends BaseStoryBlock {
  type: "audio_recording";
  title: string;
  audioUrl: string;
  durationSeconds: number;
  transcript?: string;
  speakerName: string;
}

export interface VideoClipStoryBlock extends BaseStoryBlock {
  type: "video_clip";
  title: string;
  videoUrl: string;
  posterUrl?: string;
  caption?: string;
}

/**
 * Polymorphic Union of all Story Block Types
 */
export type StoryBlock =
  | TextStoryBlock
  | ImageStoryBlock
  | QuoteStoryBlock
  | SourceExcerptStoryBlock
  | CulturalContextStoryBlock
  | Model3DStoryBlock
  | ArtisanBridgeStoryBlock
  | ComparisonStoryBlock
  | CalloutStoryBlock
  | ReflectionPromptStoryBlock
  | AudioRecordingStoryBlock
  | VideoClipStoryBlock;

export interface StoryChapter {
  id: string;
  chapterNumber: number;
  slug: string;
  title: LocalizedField;
  summary?: LocalizedField;
  readingTimeMinutes?: number;
  blocks: StoryBlock[];
}

export interface RbpcClaimEvidence {
  id: UuidString;
  statement: string;
  locale: RbpcLocale;
  claimCategory:
    | "historical_fact"
    | "maker_technique"
    | "cultural_symbolism"
    | "contemporary_practice";
  sourceTitle: string;
  sourceUrl?: string;
  supportType: SupportType;
  reviewStatus: ReviewStatus;
  citationLabel?: string;
  locator?: string;
}

export interface RbpcStory {
  id: UuidString;
  slug: string;
  title: LocalizedField;
  intro: LocalizedField;
  approvedSummary: LocalizedField;
  heroImageUrl?: string;
  heroImageAlt?: string;
  category?: string;
  status: "draft" | "review" | "approved" | "published" | "archived";
  publishedAt?: IsoDateTimeString;
  readingTimeMinutes: number;
  chapters: StoryChapter[];
  blocks?: StoryBlock[]; // Flat fallback if chapters are omitted
  creatorSlug?: string;
  creator?: RbpcCreator;
  experienceSlug?: string;
  experience?: RbpcExperience;
  heritagePlaceSlug?: string;
  evidenceClaims: RbpcClaimEvidence[];
  contentScope: ContentScope;
  version: number;
  rightsId?: UuidString;
  reviewedBy?: string;
  reviewedAt?: IsoDateTimeString;
  createdAt: IsoDateTimeString;
  updatedAt: IsoDateTimeString;
}

// ============================================================================
// 5. Inquiry State Machine & Form Contracts
// ============================================================================

export type InquiryStatus =
  | "new"
  | "contacted"
  | "confirmed"
  | "declined"
  | "closed";

export type ContactMethod = "email" | "phone" | "zalo";

export interface InquiryContact {
  name: string;
  method: ContactMethod;
  value: string;
}

export interface InquiryFormValues {
  experienceSlug: string;
  name: string;
  contactMethod: ContactMethod;
  contactValue: string;
  preferredDate?: string; // YYYY-MM-DD
  partySize: number;
  message?: string;
  consentAccepted: boolean;
  privacyAccepted: boolean;
  consentVersion: string;
  idempotencyKey: string; // Client UUID v4 generated on form mount
}

export interface RbpcInquiry {
  id: UuidString;
  reference: string; // Non-sequential public ref, e.g. "INQ-7F89-A23C"
  experienceSlug: string;
  experienceTitle: string;
  creatorSlug?: string;
  providerId?: UuidString;
  contact: InquiryContact;
  preferredDate?: IsoDateString | null;
  partySize: number;
  message?: string | null;
  status: InquiryStatus;
  consentVersion: string;
  consentAcceptedAt: IsoDateTimeString;
  idempotencyKey: string;
  createdAt: IsoDateTimeString;
  updatedAt: IsoDateTimeString;
  partnerNotes?: string;
}

export interface InquiryStatusResponse {
  reference: string;
  experienceTitle: string;
  status: InquiryStatus;
  statusMessage: string;
  preferredDate?: IsoDateString | null;
  partySize?: number | null;
  lastUpdatedAt: IsoDateTimeString;
  createdAt?: IsoDateTimeString;
}

export interface InquirySubmissionResult {
  reference: string;
  statusToken: string; // Opaque secret stored on client for status lookups
  status: InquiryStatus;
  message: string;
  createdAt: IsoDateTimeString;
}

// ============================================================================
// 6. Partner Inbox & State Transition Types
// ============================================================================

export interface PartnerInboxItem {
  id: UuidString;
  reference: string;
  experienceSlug: string;
  experienceTitle: string;
  creatorSlug?: string;
  creatorName?: string;
  contactName: string;
  contactMethod: ContactMethod;
  contactValue: string;
  preferredDate?: IsoDateString | null;
  partySize: number;
  message?: string | null;
  status: InquiryStatus;
  partnerNotes?: string | null;
  lastContactedAt?: IsoDateTimeString | null;
  createdAt: IsoDateTimeString;
  updatedAt: IsoDateTimeString;
}

export interface PartnerFilterState {
  status: InquiryStatus | "all";
  experienceSlug?: string;
  searchQuery?: string;
  dateFrom?: IsoDateString;
  dateTo?: IsoDateString;
  sortBy: "createdAt" | "preferredDate" | "status";
  sortOrder: "asc" | "desc";
  page: number;
  pageSize: number;
}

export interface PartnerInquiryUpdatePayload {
  status: InquiryStatus;
  note?: string;
}

// ============================================================================
// 7. Learn Pathway & Educational Bridge Types
// ============================================================================

export type LearnRoadmapPhase =
  | "P1_HERITAGE_BASELINE"
  | "P2_INTERACTIVE_3D"
  | "P3_MAKER_MASTERCLASS"
  | "P4_ACCREDITED_CURRICULUM";

export type LearnModuleStatus =
  | "available_in_repo"
  | "prototype"
  | "roadmap_phase_2";

export interface LearnPathwayModule {
  id: string;
  slug: string;
  title: LocalizedField;
  description: LocalizedField;
  targetAudience: "visitor" | "student" | "educator";
  prerequisiteStorySlugs?: string[];
  linked3DArtefactSlug?: string; // e.g. "cao-dinh", "thuan-dinh"
  linkedCreatorSlug?: string;
  learningObjectives: LocalizedField[];
  roadmapPhase: LearnRoadmapPhase;
  status: LearnModuleStatus;
  historicalPeriod: string;
  sourceCitationsCount: number;
  estimatedMinutes: number;
}

// ============================================================================
// 8. API Envelopes & Utility Responses
// ============================================================================

export interface RbpcApiResponse<T> {
  data: T;
  meta?: {
    total?: number;
    offset?: number;
    limit?: number;
    locale?: RbpcLocale;
    timestamp?: IsoDateTimeString;
  };
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
}
