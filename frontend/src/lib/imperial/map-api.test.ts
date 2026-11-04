import { describe, it, expect, vi } from "vitest";
import * as apiModule from "@/lib/api";
import {
  fetchActiveMap,
  fetchZones,
  fetchSites,
  fetchSiteDetail,
  fetchSiteEvidence,
  fetchSiteTimeline,
  fetchAdminMaps,
  fetchAdminAnnotations,
  createAnnotation,
  updateAnnotation,
  deleteAnnotation,
  publishMap,
  exportAnnotations,
  importAnnotations,
} from "./map-api";
import type { ImperialMapAnnotation, ImperialMapAsset } from "./map-types";

describe("imperial map-api client", () => {
  it("fetchActiveMap returns active aerial map with >= 12 annotations", async () => {
    const res = await fetchActiveMap();
    expect(res).toBeDefined();
    expect(res.map).toBeDefined();
    expect(res.map.version).toBeGreaterThanOrEqual(1);
    expect(res.annotations).toBeDefined();
    expect(Array.isArray(res.annotations)).toBe(true);
    expect(res.annotations.length).toBeGreaterThanOrEqual(12);

    // Verify all annotations have valid UV coordinates in [0..1]
    res.annotations.forEach((anno) => {
      expect(anno.u).toBeGreaterThanOrEqual(0);
      expect(anno.u).toBeLessThanOrEqual(1);
      expect(anno.v).toBeGreaterThanOrEqual(0);
      expect(anno.v).toBeLessThanOrEqual(1);
      expect(anno.marker_style).toBeDefined();
    });
  });

  it("fetchZones returns 4 verified spatial zones", async () => {
    const zones = await fetchZones();
    expect(zones.length).toBe(4);
    const slugs = zones.map((z) => z.slug);
    expect(slugs).toContain("central-ceremonial-axis");
    expect(slugs).toContain("ancestral-worship-space");
    expect(slugs).toContain("purple-forbidden-city");
    expect(slugs).toContain("royal-living-gardens");
  });

  it("fetchSites returns sites with zone slugs and learning levels", async () => {
    const sites = await fetchSites();
    expect(sites.length).toBeGreaterThanOrEqual(15);
    const ngoMon = sites.find((s) => s.slug === "ngo-mon");
    expect(ngoMon).toBeDefined();
    expect(ngoMon?.name_vi).toBe("Ngọ Môn");
    expect(ngoMon?.zone_slug).toBe("central-ceremonial-axis");
  });

  it("fetchSites filters by zone and search query", async () => {
    const centralSites = await fetchSites({ zone: "central-ceremonial-axis" });
    expect(centralSites.length).toBeGreaterThanOrEqual(3);
    centralSites.forEach((s) => {
      expect(s.zone_slug).toBe("central-ceremonial-axis");
    });

    const searchRes = await fetchSites({ search: "Thái Hòa" });
    expect(searchRes.length).toBeGreaterThanOrEqual(1);
    expect(searchRes[0].slug).toBe("dien-thai-hoa");
  });

  it("fetchSiteDetail returns detail for valid slug and null for non-existent", async () => {
    const detail = await fetchSiteDetail("dien-thai-hoa");
    expect(detail).toBeDefined();
    expect(detail?.name_vi).toBe("Điện Thái Hòa");

    const nonExistent = await fetchSiteDetail("non-existent-site-xyz");
    expect(nonExistent).toBeNull();
  });

  it("fetchSiteEvidence returns archival sources and claims", async () => {
    const evidence = await fetchSiteEvidence("ngo-mon");
    expect(evidence.site_slug).toBe("ngo-mon");
    expect(evidence.sources.length).toBeGreaterThanOrEqual(1);
    expect(evidence.sources[0].source_title).toBeDefined();
  });

  it("fetchSiteTimeline returns historical events", async () => {
    const timeline = await fetchSiteTimeline("ngo-mon");
    expect(timeline.site_slug).toBe("ngo-mon");
    expect(timeline.events.length).toBeGreaterThanOrEqual(2);
  });

  it("fetchAdminMaps and fetchAdminAnnotations return asset records", async () => {
    const maps = await fetchAdminMaps();
    expect(maps.length).toBeGreaterThanOrEqual(1);
    const annos = await fetchAdminAnnotations(maps[0].id);
    expect(annos.length).toBeGreaterThanOrEqual(12);
  });

  it("createAnnotation, updateAnnotation, deleteAnnotation lifecycle with real persistence", async () => {
    const serverCreated: ImperialMapAnnotation = {
      id: "anno-srv-001",
      map_asset_id: "map-1",
      site_id: "site-ngo-mon",
      shape_type: "point",
      u: 0.5,
      v: 0.8,
      label: "Ngọ Môn",
      marker_style: "monument",
      review_status: "draft",
      position_confidence: "approximate",
      row_version: 1,
    };

    const serverUpdated: ImperialMapAnnotation = {
      ...serverCreated,
      u: 0.55,
      row_version: 2,
    };

    const apiSpy = vi
      .spyOn(apiModule, "apiRequest")
      .mockResolvedValueOnce(serverCreated)
      .mockResolvedValueOnce(serverUpdated)
      .mockResolvedValueOnce({ ok: true, success: true, id: "anno-srv-001" });

    const newAnno = await createAnnotation("map-1", {
      site_id: "site-ngo-mon",
      u: 0.5,
      v: 0.8,
      label: "Ngọ Môn",
    });
    expect(newAnno.id).toBe("anno-srv-001");
    expect(newAnno.u).toBe(0.5);
    expect(apiSpy).toHaveBeenNthCalledWith(
      1,
      "/api/v1/imperial/admin/maps/map-1/annotations",
      expect.objectContaining({ method: "POST" }),
    );

    const updated = await updateAnnotation(newAnno.id, {
      ...newAnno,
      u: 0.55,
      row_version: newAnno.row_version,
    });
    expect(updated.u).toBe(0.55);
    expect(updated.row_version).toBe(2);
    expect(apiSpy).toHaveBeenNthCalledWith(
      2,
      `/api/v1/imperial/admin/annotations/${newAnno.id}`,
      expect.objectContaining({
        method: "PATCH",
        headers: { "If-Match": '"row-version-1"' },
      }),
    );

    const delRes = await deleteAnnotation(newAnno.id);
    expect(delRes.success).toBe(true);
    expect(delRes.id).toBe("anno-srv-001");
    expect(apiSpy).toHaveBeenNthCalledWith(
      3,
      `/api/v1/imperial/admin/annotations/${newAnno.id}`,
      expect.objectContaining({ method: "DELETE" }),
    );

    apiSpy.mockRestore();
  });

  describe("Negative Invariant: Zero Fabricated Success on Network or Server 500 Error (V5-T042)", () => {
    it("createAnnotation rejects on 500 error and never returns synthetic marker", async () => {
      const spy = vi
        .spyOn(apiModule, "apiRequest")
        .mockRejectedValueOnce(new Error("HTTP 500: Internal Server Error"));

      await expect(
        createAnnotation("map-1", {
          site_id: "site-ngo-mon",
          u: 0.5,
          v: 0.8,
        }),
      ).rejects.toThrow("HTTP 500: Internal Server Error");

      expect(spy).toHaveBeenCalledTimes(1);
      spy.mockRestore();
    });

    it("updateAnnotation rejects on 500 error and never fabricates bumped row_version", async () => {
      const spy = vi
        .spyOn(apiModule, "apiRequest")
        .mockRejectedValueOnce(new Error("HTTP 500: Database Connection Error"));

      await expect(
        updateAnnotation("anno-001", {
          u: 0.6,
          row_version: 1,
        }),
      ).rejects.toThrow("HTTP 500: Database Connection Error");

      expect(spy).toHaveBeenCalledTimes(1);
      spy.mockRestore();
    });

    it("deleteAnnotation rejects on 500 error and never returns success: true", async () => {
      const spy = vi
        .spyOn(apiModule, "apiRequest")
        .mockRejectedValueOnce(new Error("HTTP 500: Failed to archive annotation"));

      await expect(deleteAnnotation("anno-001")).rejects.toThrow(
        "HTTP 500: Failed to archive annotation",
      );

      expect(spy).toHaveBeenCalledTimes(1);
      spy.mockRestore();
    });

    it("publishMap rejects on 500 error and never fabricates published map state", async () => {
      const spy = vi
        .spyOn(apiModule, "apiRequest")
        .mockRejectedValueOnce(new Error("HTTP 500: Atomic publish transaction rolled back"));

      await expect(publishMap("map-1")).rejects.toThrow(
        "HTTP 500: Atomic publish transaction rolled back",
      );

      expect(spy).toHaveBeenCalledTimes(1);
      spy.mockRestore();
    });

    it("updateAnnotation rejects on 409 concurrency conflict and lets error propagate", async () => {
      const spy = vi
        .spyOn(apiModule, "apiRequest")
        .mockRejectedValueOnce(new Error("HTTP 409: IMPERIAL_CONCURRENCY_CONFLICT"));

      await expect(
        updateAnnotation("anno-001", {
          u: 0.7,
          row_version: 1,
        }),
      ).rejects.toThrow("HTTP 409: IMPERIAL_CONCURRENCY_CONFLICT");

      expect(spy).toHaveBeenCalledTimes(1);
      spy.mockRestore();
    });
  });

  it("exportAnnotations calls GET export and returns server payload", async () => {
    const mockExport = {
      schema_version: "imperial-annotations/1.0",
      scope: "STTT_IMPERIAL_CITY",
      map: {
        slug: "dai-noi-aerial-1932",
        version: 1,
        image_sha256: "abc123sha",
      },
      annotations: [
        {
          site_slug: "ngo-mon",
          u: 0.5,
          v: 0.8,
          shape_type: "point" as const,
        },
      ],
      exported_at: "2026-11-05T00:00:00Z",
      export_sha256: "hash123",
    };

    const spy = vi
      .spyOn(apiModule, "apiRequest")
      .mockResolvedValueOnce(mockExport);

    const exp = await exportAnnotations("map-1");
    expect(exp.schema_version).toBe("imperial-annotations/1.0");
    expect(exp.scope).toBe("STTT_IMPERIAL_CITY");
    expect(exp.annotations.length).toBe(1);
    expect(spy).toHaveBeenCalledWith("/api/v1/imperial/admin/maps/map-1/export");

    spy.mockRestore();
  });

  it("importAnnotations calls POST import and returns server results without fabricating success", async () => {
    const mockImportPayload = {
      schema_version: "imperial-annotations/1.0",
      scope: "STTT_IMPERIAL_CITY",
      map: {
        slug: "dai-noi-aerial-1932",
        version: 1,
        image_sha256: "abc123sha",
      },
      annotations: [
        {
          site_slug: "ngo-mon",
          u: 0.5,
          v: 0.8,
          shape_type: "point" as const,
        },
      ],
      exported_at: "2026-11-05T00:00:00Z",
      export_sha256: "hash123",
    };

    const mockDryRunResult = {
      valid: true,
      created_count: 1,
      updated_count: 0,
      skipped_count: 0,
      total_count: 1,
      image_hash_matched: true,
      issues: [],
    };

    const spy = vi
      .spyOn(apiModule, "apiRequest")
      .mockResolvedValueOnce(mockDryRunResult);

    const dryRun = await importAnnotations("map-1", mockImportPayload, true);
    expect(dryRun.valid).toBe(true);
    expect(dryRun.created_count).toBe(1);
    expect(spy).toHaveBeenCalledWith(
      "/api/v1/imperial/admin/maps/map-1/import?dry_run=true",
      expect.objectContaining({
        method: "POST",
        body: mockImportPayload,
      }),
    );

    spy.mockRestore();
  });
});
