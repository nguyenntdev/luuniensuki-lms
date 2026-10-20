import { describe, it, expect } from "vitest";
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

  it("createAnnotation, updateAnnotation, deleteAnnotation lifecycle", async () => {
    const newAnno = await createAnnotation("map-1", {
      site_id: "site-ngo-mon",
      u: 0.5,
      v: 0.8,
      label: "Thử nghiệm",
    });
    expect(newAnno.id).toBeDefined();
    expect(newAnno.u).toBe(0.5);

    const updated = await updateAnnotation(newAnno.id, {
      ...newAnno,
      u: 0.55,
      row_version: newAnno.row_version,
    });
    expect(updated.u).toBe(0.55);

    const delRes = await deleteAnnotation(newAnno.id);
    expect(delRes.success).toBe(true);
  });

  it("exportAnnotations outputs valid schema imperial-annotations/1.0", async () => {
    const exp = await exportAnnotations("map-1");
    expect(exp.schema_version).toBe("imperial-annotations/1.0");
    expect(exp.scope).toBe("STTT_IMPERIAL_CITY");
    expect(exp.annotations.length).toBeGreaterThanOrEqual(12);
  });

  it("importAnnotations validates schema and returns dry-run results", async () => {
    const exp = await exportAnnotations("map-1");
    const dryRun = await importAnnotations("map-1", exp, true);
    expect(dryRun.valid).toBe(true);
    expect(dryRun.total_count).toBe(exp.annotations.length);
  });
});
