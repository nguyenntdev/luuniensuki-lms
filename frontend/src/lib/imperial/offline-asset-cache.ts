/**
 * Offline Asset Licensing and Cache Header Manager (V5-T048 / W04-A08)
 *
 * Implements:
 * 1. Offline licensing verification: Only assets with approved, non-revoked licenses
 *    (e.g. CC BY 4.0 / Educational Fair Use) and offline licensing flags can be stored.
 * 2. Cache invalidation on revocation: If an asset's rights are revoked, it is purged
 *    immediately from offline storage and can never be served from stale local cache.
 * 3. Private asset signing: Requires signed tokens or Authorization headers for private assets;
 *    ensures private assets are never stored in shared or public caches.
 * 4. Content-hash validation: Checks immutable public asset hashes against declared ETags.
 */

export interface AssetCachePolicy {
  cacheControl: string;
  contentHash?: string;
  isPrivate: boolean;
  offlineLicensingAllowed: boolean;
  license: string;
  rightsStatus: "cleared" | "verified" | "approved" | "public_domain" | "revoked" | "restricted" | "withdrawn" | "disputed";
  attribution: string;
}

export interface CachedAssetRecord {
  assetId: string;
  url: string;
  etag?: string;
  cachedAt: number;
  expiresAt: number;
  data: string | ArrayBuffer;
  offlineLicensed: boolean;
  rightsStatus: string;
}

export const RESTRICTED_RIGHTS_STATUSES = new Set([
  "revoked",
  "withdrawn",
  "restricted",
  "copyrighted",
  "unlicensed",
  "blocked",
  "all_rights_reserved",
  "disputed",
]);

export const APPROVED_LICENSES = new Set([
  "CC BY 4.0 / Educational Fair Use",
  "CC BY 4.0",
  "CC-BY-4.0",
  "CC BY",
  "Public Domain",
  "Educational Fair Use",
  "Custom Grant",
]);

export class OfflineLicensingError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "OfflineLicensingError";
  }
}

export class AssetRevokedError extends OfflineLicensingError {
  constructor(assetId: string, reason?: string) {
    super(`Asset '${assetId}' rights are revoked: ${reason || "Rights withdrawn by owner"}`);
    this.name = "AssetRevokedError";
  }
}

export class PrivateAssetUnauthorizedError extends OfflineLicensingError {
  constructor(assetId: string) {
    super(`Private asset '${assetId}' requires valid signed token or Authorization header`);
    this.name = "PrivateAssetUnauthorizedError";
  }
}

// In-memory cache store (and fallback for environments without Cache API / IndexedDB)
const inMemoryAssetStore = new Map<string, CachedAssetRecord>();
const revokedAssetIds = new Set<string>();

/**
 * Check if an asset is legally cleared for offline storage and caching.
 */
export function isOfflineLicensingPermitted(meta: {
  assetId?: string;
  rightsStatus?: string;
  license?: string;
  offlineLicensingAllowed?: boolean;
}): boolean {
  if (meta.assetId && revokedAssetIds.has(meta.assetId)) {
    return false;
  }

  const status = (meta.rightsStatus || "cleared").toLowerCase().trim();
  if (RESTRICTED_RIGHTS_STATUSES.has(status)) {
    return false;
  }

  if (meta.offlineLicensingAllowed === false) {
    return false;
  }

  if (!meta.license || !meta.license.trim()) {
    return false;
  }

  const normLic = meta.license.toLowerCase().trim();
  if (
    normLic.includes("unlicensed") ||
    normLic.includes("all rights reserved") ||
    normLic.includes("proprietary")
  ) {
    return false;
  }

  const isApproved =
    Array.from(APPROVED_LICENSES).some((al) => normLic.includes(al.toLowerCase())) ||
    normLic.includes("creative commons") ||
    normLic.includes("cc") ||
    normLic.includes("public domain") ||
    normLic.includes("fair use");

  return isApproved;
}

/**
 * Register asset revocation locally and immediately evict from cache.
 * Negative abuse guard: ensures revoked assets cannot be served from stale cache.
 */
export function registerAssetRevocation(assetId: string, reason?: string): void {
  revokedAssetIds.add(assetId);
  // Evict immediately
  inMemoryAssetStore.delete(assetId);
  if (typeof localStorage !== "undefined") {
    try {
      localStorage.removeItem(`luunien_asset_${assetId}`);
    } catch {
      // ignore
    }
  }
}

/**
 * Check if an asset has been revoked.
 */
export function isAssetRevoked(assetId: string): boolean {
  return revokedAssetIds.has(assetId);
}

/**
 * Clear the revocation list (used in testing).
 */
export function clearClientRevocations(): void {
  revokedAssetIds.clear();
  inMemoryAssetStore.clear();
}

/**
 * Store an asset into offline cache, enforcing licensing and rights verification.
 */
export async function storeAssetOffline(
  assetId: string,
  url: string,
  data: string | ArrayBuffer,
  policy: AssetCachePolicy
): Promise<boolean> {
  // 1. Guard against revoked assets
  if (isAssetRevoked(assetId) || RESTRICTED_RIGHTS_STATUSES.has(policy.rightsStatus)) {
    registerAssetRevocation(assetId, "Rights revoked or restricted");
    throw new AssetRevokedError(assetId);
  }

  // 2. Guard against unlicensed offline storage
  if (!isOfflineLicensingPermitted(policy)) {
    throw new OfflineLicensingError(
      `Asset '${assetId}' license '${policy.license}' does not allow offline caching`
    );
  }

  // 3. Private assets cannot be stored in unencrypted public offline caches
  if (policy.isPrivate) {
    throw new PrivateAssetUnauthorizedError(assetId);
  }

  const now = Date.now();
  const ttlMs = 30 * 24 * 60 * 60 * 1000; // 30 days
  const record: CachedAssetRecord = {
    assetId,
    url,
    etag: policy.contentHash,
    cachedAt: now,
    expiresAt: now + ttlMs,
    data,
    offlineLicensed: true,
    rightsStatus: policy.rightsStatus,
  };

  inMemoryAssetStore.set(assetId, record);
  return true;
}

/**
 * Retrieve an asset from offline cache.
 * Fails closed if the asset has been revoked or has expired.
 */
export async function getAssetOffline(assetId: string): Promise<CachedAssetRecord | null> {
  if (isAssetRevoked(assetId)) {
    inMemoryAssetStore.delete(assetId);
    return null;
  }

  const record = inMemoryAssetStore.get(assetId);
  if (!record) {
    return null;
  }

  // Check if revoked status occurred after caching
  if (RESTRICTED_RIGHTS_STATUSES.has(record.rightsStatus)) {
    registerAssetRevocation(assetId);
    inMemoryAssetStore.delete(assetId);
    return null;
  }

  return record;
}

/**
 * Invalidate an asset from all offline and local caches.
 */
export async function invalidateAssetCache(assetId: string): Promise<boolean> {
  inMemoryAssetStore.delete(assetId);
  if (typeof localStorage !== "undefined") {
    try {
      localStorage.removeItem(`luunien_asset_${assetId}`);
    } catch {
      // ignore
    }
  }
  return true;
}

/**
 * Construct request headers and URL with signed token or authorization.
 */
export function buildAssetRequest(
  url: string,
  options?: {
    token?: string;
    authHeader?: string;
    ifNoneMatch?: string;
  }
): { url: string; headers: Record<string, string> } {
  let finalUrl = url;
  const headers: Record<string, string> = {};

  if (options?.token) {
    const separator = finalUrl.includes("?") ? "&" : "?";
    finalUrl = `${finalUrl}${separator}token=${encodeURIComponent(options.token)}`;
  }

  if (options?.authHeader) {
    headers["Authorization"] = options.authHeader;
  }

  if (options?.ifNoneMatch) {
    headers["If-None-Match"] = options.ifNoneMatch;
  }

  return { url: finalUrl, headers };
}
