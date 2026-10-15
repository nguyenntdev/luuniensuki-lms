import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import * as api from "./api";
import {
  submitUrnExam,
  ApiError,
  buildApiError,
  apiRequest,
  apiRequestFormData,
  apiRequestBinary,
} from "./api";
import { safeJsonLd } from "./seo";

// Helper to build a fake `fetch` Response with just the surface api.js touches.
function makeResponse({ ok, status, statusText = "", json, text }) {
  const bodyText = text !== undefined ? text : (json !== undefined ? JSON.stringify(json) : "");
  return {
    ok,
    status,
    statusText,
    json: json !== undefined ? async () => json : async () => {
      throw new Error("no json body");
    },
    text: async () => bodyText,
  };
}

beforeEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

afterEach(() => {
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("submitUrnExam server-authoritative grading (Req 4.x / 13.1 exam flow)", () => {
  it("surfaces a server error and does NOT fall back to local grading", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      makeResponse({
        ok: false,
        status: 500,
        statusText: "Internal Server Error",
        json: { error: { message: "grading service unavailable" } },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const promise = submitUrnExam({
      urnSlug: "cao-dinh",
      answers: { q1: "A", q2: "B" },
      timeTakenSeconds: 120,
    });

    // It must reject (propagate the server error), never resolve with a
    // client-computed score.
    await expect(promise).rejects.toBeInstanceOf(ApiError);
    await expect(promise).rejects.toMatchObject({
      status: 500,
      message: "grading service unavailable",
    });

    // Exactly one network call (the submit). No second fetch to a static
    // answer-key asset and no refresh loop on a non-401 error.
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const calledUrl = fetchMock.mock.calls[0][0];
    expect(calledUrl).toContain("/api/v1/urns/cao-dinh/exam/submit");
  });

  it("returns the server-computed score on success (no local scoring)", async () => {
    const serverPayload = {
      score: 7,
      total: 10,
      passed: false,
      correct_count: 7,
    };
    const fetchMock = vi.fn().mockResolvedValue(
      makeResponse({ ok: true, status: 200, text: JSON.stringify(serverPayload) }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await submitUrnExam({
      urnSlug: "cao-dinh",
      answers: { q1: "A" },
      timeTakenSeconds: 30,
    });

    // The function returns exactly what the server returned — the authoritative
    // score — rather than anything graded on the client.
    expect(result).toEqual(serverPayload);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("posts answers as an array with the configured method/body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      makeResponse({ ok: true, status: 200, text: JSON.stringify({ score: 1 }) }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await submitUrnExam({
      urnSlug: "an example/urn",
      answers: { q1: "A", q2: 3 },
      timeTakenSeconds: 99,
    });

    const [url, init] = fetchMock.mock.calls[0];
    // urnSlug is URL-encoded.
    expect(url).toContain(encodeURIComponent("an example/urn"));
    expect(init.method).toBe("POST");
    const body = JSON.parse(init.body);
    expect(body.time_taken_seconds).toBe(99);
    expect(body.answers).toEqual([
      { question_id: "q1", answer: "A" },
      { question_id: "q2", answer: "3" },
    ]);
  });
});

describe("no client-side static answer-key grading path remains (Req 4.2)", () => {
  it("does not export getUrnExamFromStatic or any static grading helper", () => {
    expect(api.getUrnExamFromStatic).toBeUndefined();
    const exportNames = Object.keys(api);
    expect(exportNames.some((n) => /static/i.test(n))).toBe(false);
    expect(exportNames.some((n) => /answerKey|answer_key/i.test(n))).toBe(false);
  });
});

describe("getReliefHotspot deep-link API (Phase 7)", () => {
  it("requests the hotspot endpoint with the encoded urn and relief slugs", async () => {
    const payload = {
      relief_entity_id: 42,
      urn_entity_id: 7,
      slug: "cao-dinh-02",
      urn_slug: "cao-dinh",
      hotspot: {
        mesh_name: "mesh_urn_cao_dinh_02_v1",
        pos: [-0.5, 0.9, 0.87],
        bounding_radius: 0.35,
      },
    };
    const fetchMock = vi.fn().mockResolvedValue(
      makeResponse({ ok: true, status: 200, text: JSON.stringify(payload) }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await api.getReliefHotspot("cao-dinh", "cao-dinh-02");

    expect(result).toEqual(payload);
    const [url] = fetchMock.mock.calls[0];
    expect(url).toContain("/api/v1/history/reliefs/cao-dinh/cao-dinh-02/hotspot");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("surfaces a null hotspot when the relief has no coordinates", async () => {
    const payload = {
      relief_entity_id: 42,
      urn_entity_id: 7,
      slug: "cao-dinh-02",
      urn_slug: "cao-dinh",
      hotspot: null,
      message: "no coordinates for relief",
    };
    const fetchMock = vi.fn().mockResolvedValue(
      makeResponse({ ok: true, status: 200, text: JSON.stringify(payload) }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await api.getReliefHotspot("cao-dinh", "cao-dinh-02");

    expect(result.hotspot).toBeNull();
    expect(result.message).toBe("no coordinates for relief");
    const [url] = fetchMock.mock.calls[0];
    expect(url).toContain(encodeURIComponent("cao-dinh-02"));
  });
});

describe("buildApiError safe error handling", () => {
  it("extracts error message from structured ApiErrorBody with error.message", async () => {
    const res = makeResponse({
      ok: false,
      status: 400,
      statusText: "Bad Request",
      json: { error: { code: "INVALID_REQUEST", message: "Specific failure message" } },
    });
    const err = await buildApiError(res);
    expect(err).toBeInstanceOf(ApiError);
    expect(err.message).toBe("Specific failure message");
    expect(err.status).toBe(400);
    expect(err.data).toEqual({
      error: { code: "INVALID_REQUEST", message: "Specific failure message" },
    });
  });

  it("extracts error message from detail string (FastAPI style)", async () => {
    const res = makeResponse({
      ok: false,
      status: 404,
      statusText: "Not Found",
      json: { detail: "Item not found" },
    });
    const err = await buildApiError(res);
    expect(err.message).toBe("Item not found");
    expect(err.status).toBe(404);
  });

  it("extracts error message from detail object/array (FastAPI validation style)", async () => {
    const detailObj = [{ loc: ["body", "title"], msg: "field required" }];
    const res = makeResponse({
      ok: false,
      status: 422,
      statusText: "Unprocessable Entity",
      json: { detail: detailObj },
    });
    const err = await buildApiError(res);
    expect(err.message).toBe(JSON.stringify(detailObj));
    expect(err.status).toBe(422);
  });

  it("handles non-JSON plain text / HTML responses safely without failing stream read", async () => {
    const htmlBody = "<html><head><title>502 Bad Gateway</title></head><body>502 Bad Gateway</body></html>";
    const res = makeResponse({
      ok: false,
      status: 502,
      statusText: "Bad Gateway",
      text: htmlBody,
    });
    const err = await buildApiError(res);
    expect(err.message).toBe(`HTTP 502 Bad Gateway: ${htmlBody}`);
    expect(err.status).toBe(502);
    expect(err.data).toBeUndefined();
  });

  it("handles empty response body gracefully", async () => {
    const res = makeResponse({
      ok: false,
      status: 500,
      statusText: "Internal Server Error",
      text: "",
    });
    const err = await buildApiError(res);
    expect(err.message).toBe("HTTP 500 Internal Server Error");
    expect(err.status).toBe(500);
    expect(err.data).toBeUndefined();
  });
});

describe("safeJsonLd XSS prevention", () => {
  it("escapes '<' as '\\u003c' to prevent script breakout", () => {
    const maliciousPayload = {
      "@context": "https://schema.org",
      name: '</script><script>alert("XSS")</script>',
      description: "Sample <tag> content",
    };

    const serialized = safeJsonLd(maliciousPayload);

    // Must not contain raw '<' characters
    expect(serialized).not.toContain("<");
    expect(serialized).toContain("\\u003c/script>\\u003cscript>alert(\\\"XSS\\\")\\u003c/script>");
    expect(serialized).toContain("Sample \\u003ctag> content");

    // Must parse back to the original object using JSON.parse
    const parsed = JSON.parse(serialized);
    expect(parsed).toEqual(maliciousPayload);
  });

  it("handles nested objects and arrays correctly", () => {
    const complexData = {
      items: [
        { id: 1, text: "<img src=x onerror=alert(1)>" },
        { id: 2, nested: { value: "<<<escaped>>>" } },
      ],
    };

    const serialized = safeJsonLd(complexData);
    expect(serialized).not.toContain("<");
    expect(serialized).toContain("\\u003cimg src=x onerror=alert(1)>");
    expect(serialized).toContain("\\u003c\\u003c\\u003cescaped>>>");

    const parsed = JSON.parse(serialized);
    expect(parsed).toEqual(complexData);
  });
});

describe("CSRF Defense-in-depth: X-Requested-With header on mutating requests", () => {
  it("attaches X-Requested-With header to mutating apiRequest (POST, PUT, PATCH, DELETE)", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      makeResponse({ ok: true, status: 200, json: { success: true } }),
    );
    vi.stubGlobal("fetch", fetchMock);

    // POST
    await apiRequest("/api/v1/test", { method: "POST", body: { foo: "bar" } });
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringContaining("/api/v1/test"),
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          "X-Requested-With": "XMLHttpRequest",
          "content-type": "application/json",
        }),
      }),
    );

    // PUT
    await apiRequest("/api/v1/test", { method: "PUT", body: { foo: "bar" } });
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringContaining("/api/v1/test"),
      expect.objectContaining({
        method: "PUT",
        headers: expect.objectContaining({
          "X-Requested-With": "XMLHttpRequest",
        }),
      }),
    );

    // PATCH
    await apiRequest("/api/v1/test", { method: "PATCH", body: { foo: "bar" } });
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringContaining("/api/v1/test"),
      expect.objectContaining({
        method: "PATCH",
        headers: expect.objectContaining({
          "X-Requested-With": "XMLHttpRequest",
        }),
      }),
    );

    // DELETE
    await apiRequest("/api/v1/test", { method: "DELETE" });
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringContaining("/api/v1/test"),
      expect.objectContaining({
        method: "DELETE",
        headers: expect.objectContaining({
          "X-Requested-With": "XMLHttpRequest",
        }),
      }),
    );
  });

  it("does NOT attach X-Requested-With header to GET requests by default", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      makeResponse({ ok: true, status: 200, json: { data: [] } }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await apiRequest("/api/v1/test", { method: "GET" });
    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers["X-Requested-With"]).toBeUndefined();
  });

  it("attaches X-Requested-With header to apiRequestFormData for mutating requests", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      makeResponse({ ok: true, status: 200, json: { uploaded: true } }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await apiRequestFormData("/api/v1/upload", {
      method: "POST",
      body: "dummy body",
    });

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers).toEqual(
      expect.objectContaining({
        "X-Requested-With": "XMLHttpRequest",
      }),
    );
  });

  it("attaches X-Requested-With header to apiRequestBinary for mutating requests", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      blob: async () => new Blob(["data"]),
      headers: new Headers({ "content-type": "audio/mpeg" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await apiRequestBinary("/api/v1/tts", {
      method: "POST",
      body: "dummy body",
    });

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers).toEqual(
      expect.objectContaining({
        "X-Requested-With": "XMLHttpRequest",
      }),
    );
  });

  it("preserves custom headers alongside X-Requested-With", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      makeResponse({ ok: true, status: 200, json: { ok: true } }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await apiRequest("/api/v1/test", {
      method: "POST",
      headers: { "X-Custom-Header": "custom-value" },
      body: { a: 1 },
    });

    const [, init] = fetchMock.mock.calls[0];
    expect(init.headers).toEqual({
      "X-Requested-With": "XMLHttpRequest",
      "content-type": "application/json",
      "X-Custom-Header": "custom-value",
    });
  });
});
