/**
 * High-Level Business Logic Engine for STTTNNĐ Royal Seals & Digital Heritage Passport.
 * Spec: STTT-SPEC-AUDIO-PASSPORT-002
 * Scope: STTT_IMPERIAL_CITY (Đại Nội Huế — 16 Historical Monuments across 4 Spatial Zones)
 *
 * Provides:
 * - Deterministic progression tracking across 16 monuments.
 * - Spatial cluster / zone completion calculations.
 * - Four-tier imperial honors title evaluation (4, 8, 12, 16 thresholds).
 * - Idempotency enforcement for seal unlocks and storage integrity.
 */

import {
  PASSPORT_SEALS,
  PASSPORT_ZONE_META,
  PASSPORT_ALL_BADGES,
  PASSPORT_STORAGE_KEY,
  PASSPORT_STUDENT_KEY,
  PASSPORT_ZONE_SEALS_KEY,
  ZONE_ROYAL_SEALS_CATALOG,
  GRAND_ROYAL_SEAL,
  getZoneRoyalSeal,
  getGrandRoyalSeal,
  isZoneSealStamped,
  stampZoneSeal,
  isGrandSealStamped,
  stampGrandSeal,
  getStampedZoneSeals,
  type SpatialZoneSlug,
  type PassportSealDefinition,
  type UnlockedSealRecord,
  type ZoneProgress,
  type PassportBadge,
  type PassportProgress,
  getUnlockedSeals,
  getUnlockedSealsMap,
  isSealUnlocked,
  getSealDefinition,
  getPassportProgress,
  unlockSeal,
  resetPassport,
  unlockAllSealsDemo,
  unlockCertificateDemo,
  playStampSound,
} from "./passport-storage";

import {
  type MonumentSeal,
  type SealMotifType,
  type RoyalSealCategory,
  type SealMaterialType,
  getMonumentSeal,
} from "./passport-types";

import {
  getHonorsTitle,
  getZoneBreakdown,
  generateCertificateId,
  formatImperialDate,
  type HonorsTitleTier,
  type HonorsTitleInfo,
  type ZoneSealBreakdown,
  type CertificateData,
} from "./certificate-utils";

export const ALL_SITE_SEALS = PASSPORT_SEALS;
export const ZONE_NAMES_MAP = PASSPORT_ZONE_META;
export type SiteSeal = PassportSealDefinition;

export {
  // Re-exports from passport-storage
  PASSPORT_SEALS,
  PASSPORT_ZONE_META,
  PASSPORT_ALL_BADGES,
  PASSPORT_STORAGE_KEY,
  PASSPORT_STUDENT_KEY,
  PASSPORT_ZONE_SEALS_KEY,
  ZONE_ROYAL_SEALS_CATALOG,
  GRAND_ROYAL_SEAL,
  getZoneRoyalSeal,
  getGrandRoyalSeal,
  isZoneSealStamped,
  stampZoneSeal,
  isGrandSealStamped,
  stampGrandSeal,
  getStampedZoneSeals,
  getMonumentSeal,
  type MonumentSeal,
  type SealMotifType,
  type RoyalSealCategory,
  type SealMaterialType,
  type SpatialZoneSlug,
  type PassportSealDefinition,
  type UnlockedSealRecord,
  type ZoneProgress,
  type PassportBadge,
  type PassportProgress,
  getUnlockedSeals,
  getUnlockedSealsMap,
  isSealUnlocked,
  getSealDefinition,
  getPassportProgress,
  unlockSeal,
  resetPassport,
  unlockAllSealsDemo,
  unlockCertificateDemo,
  playStampSound,
  // Re-exports from certificate-utils
  getHonorsTitle,
  getZoneBreakdown,
  generateCertificateId,
  formatImperialDate,
  type HonorsTitleTier,
  type HonorsTitleInfo,
  type ZoneSealBreakdown,
  type CertificateData,
};

/** Total number of verified architectural monuments in Đại Nội Huế */
export const TOTAL_MONUMENTS_COUNT = 16;

/** Minimum seals required to unlock the Royal Heritage Certificate of Completion */
export const MIN_CERTIFICATE_SEALS_REQUIRED = 4;

/** Canonical progression thresholds for honors title tiers */
export const TITLE_TIER_THRESHOLDS = {
  NOVICE: 0,
  APPRENTICE: 4,
  EXPLORER: 8,
  SCHOLAR: 12,
  MASTER: 16,
} as const;

/**
 * Evaluates the student's royal title tier based on the number of unlocked seals.
 *
 * Tier progression:
 * - 0 - 3 seals: "novice" -> "Người Khởi Đầu Khám Phá"
 * - 4 - 7 seals: "apprentice" -> "Tập Sự Khảo Cứu Di Sản"
 * - 8 - 11 seals: "explorer" -> "Thám Hiểm Cung Đình Huế"
 * - 12 - 15 seals: "scholar" -> "Học Giả Di Sản Hoàng Thành"
 * - 16 seals: "master" -> "Bậc Thầy Khảo Cứu Cố Đô"
 */
export function evaluateTitleTier(sealCount: number): HonorsTitleInfo {
  return getHonorsTitle(sealCount);
}

/**
 * Calculates cluster / zone completion breakdown and percentage for a given set
 * of unlocked monument slugs or site IDs.
 */
export function calculateClusterCompletion(unlockedSlugsOrIds: string[]): ZoneSealBreakdown[] {
  return getZoneBreakdown(unlockedSlugsOrIds);
}

/**
 * Check whether a specific cluster is 100% completed.
 */
export function isClusterCompleted(
  zoneSlug: SpatialZoneSlug,
  unlockedSlugsOrIds: string[],
): boolean {
  const breakdown = calculateClusterCompletion(unlockedSlugsOrIds);
  const cluster = breakdown.find((z) => z.zoneSlug === zoneSlug);
  return Boolean(cluster?.isCompleted);
}

/**
 * Returns the count of unlocked monuments within a specific cluster.
 */
export function getClusterUnlockedCount(
  zoneSlug: SpatialZoneSlug,
  unlockedSlugsOrIds: string[],
): number {
  const breakdown = calculateClusterCompletion(unlockedSlugsOrIds);
  const cluster = breakdown.find((z) => z.zoneSlug === zoneSlug);
  return cluster?.unlockedCount ?? 0;
}
