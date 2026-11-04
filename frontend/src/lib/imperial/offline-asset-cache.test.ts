import { describe, it, expect, beforeEach } from "vitest";
import {
  isOfflineLicensingPermitted,
  storeAssetOffline,
  getAssetOffline,
  registerAssetRevocation,
  isAssetRevoked,
  clearClientRevocations,
  invalidateAssetCache,
  buildAssetRequest,
  OfflineLicensingError,
  AssetRevokedError,
  PrivateAssetUnauthorizedError,
  type AssetCachePolicy,
} from "./offline-asset-cache";

describe("Offline Asset Licensing and Cache Headers (offline-asset-cache.ts)", () => {
  beforeEach(() => {
    clearClientRevocations();
  });

  const validPolicy: AssetCachePolicy = {
    cacheControl: "public, max-age=31536000, immutable",
    contentHash: "6f7e73424c18c5e6504ee25eda103b56958b1e79348937e152e60731a2bcd16a",
    isPrivate: false,
    offlineLicensingAllowed: true,
    license: "CC BY 4.0 / Educational Fair Use",
    rightsStatus: "cleared",
    attribution: "Trung tâm Bảo tồn Di tích Cố đô Huế (HMCC) & Histolab",
  };

  it("permits offline licensing for verified assets with approved CC BY license", () => {
    const allowed = isOfflineLicensingPermitted(validPolicy);
    expect(allowed).toBe(true);
  });

  it("blocks offline licensing if asset explicitly has offlineLicensingAllowed=false", () => {
    const allowed = isOfflineLicensingPermitted({
      ...validPolicy,
      offlineLicensingAllowed: false,
    });
    expect(allowed).toBe(false);
  });

  it("blocks offline licensing if rights status is revoked or restricted", () => {
    expect(isOfflineLicensingPermitted({ ...validPolicy, rightsStatus: "revoked" })).toBe(false);
    expect(isOfflineLicensingPermitted({ ...validPolicy, rightsStatus: "restricted" })).toBe(false);
    expect(isOfflineLicensingPermitted({ ...validPolicy, rightsStatus: "withdrawn" })).toBe(false);
  });

  it("blocks offline licensing for proprietary or all-rights-reserved assets", () => {
    expect(isOfflineLicensingPermitted({ ...validPolicy, license: "All Rights Reserved" })).toBe(false);
    expect(isOfflineLicensingPermitted({ ...validPolicy, license: "Proprietary Commercial" })).toBe(false);
    expect(isOfflineLicensingPermitted({ ...validPolicy, license: "" })).toBe(false);
  });

  it("stores and retrieves cleared public assets with content hash offline", async () => {
    const stored = await storeAssetOffline(
      "cao-dinh-mesh",
      "/assets/models/CAO-DINH-v1-1k.glb",
      "mesh_data_binary_mock",
      validPolicy
    );
    expect(stored).toBe(true);

    const cached = await getAssetOffline("cao-dinh-mesh");
    expect(cached).not.toBeNull();
    expect(cached?.assetId).toBe("cao-dinh-mesh");
    expect(cached?.etag).toBe(validPolicy.contentHash);
    expect(cached?.offlineLicensed).toBe(true);
  });

  it("rejects caching of private assets in public offline cache", async () => {
    await expect(
      storeAssetOffline(
        "private-archival-scan",
        "/assets/private/scan-01.glb",
        "private_data",
        { ...validPolicy, isPrivate: true }
      )
    ).rejects.toThrow(PrivateAssetUnauthorizedError);
  });

  it("negative abuse test: revoked asset is immediately purged and cannot be served from stale cache", async () => {
    // 1. Initially cache a valid asset
    await storeAssetOffline(
      "relic-image-01",
      "/assets/ban-duc-noi/CAO DINH/rubbing.jpg",
      "image_binary_data",
      validPolicy
    );
    expect(await getAssetOffline("relic-image-01")).not.toBeNull();

    // 2. Revoke asset rights
    registerAssetRevocation("relic-image-01", "Copyright claim received");
    expect(isAssetRevoked("relic-image-01")).toBe(true);

    // 3. Stale cache is purged; read returns null (never stale cache beyond policy)
    const afterRevocation = await getAssetOffline("relic-image-01");
    expect(afterRevocation).toBeNull();

    // 4. Any attempt to re-store the revoked asset fails closed
    await expect(
      storeAssetOffline(
        "relic-image-01",
        "/assets/ban-duc-noi/CAO DINH/rubbing.jpg",
        "image_binary_data",
        validPolicy
      )
    ).rejects.toThrow(AssetRevokedError);
  });

  it("builds asset request with signed token in query parameters", () => {
    const req = buildAssetRequest("/api/v1/imperial/assets/abc-123/image", {
      token: "hmac_signed_token_xyz",
      ifNoneMatch: '"sha256_hash"',
    });
    expect(req.url).toContain("token=hmac_signed_token_xyz");
    expect(req.headers["If-None-Match"]).toBe('"sha256_hash"');
  });

  it("builds asset request with Authorization header", () => {
    const req = buildAssetRequest("/api/v1/imperial/assets/abc-123/image", {
      authHeader: "Bearer jwt_token_staff",
    });
    expect(req.headers["Authorization"]).toBe("Bearer jwt_token_staff");
  });
});
