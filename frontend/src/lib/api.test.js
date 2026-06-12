import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import * as api from "./api";
import { submitUrnExam, ApiError } from "./api";

// Helper to build a fake `fetch` Response with just the surface api.js touches.
function makeResponse({ ok, status, statusText = "", json, text = "" }) {
  return {
    ok,
    status,
    statusText,
    json: json ? async () => json : async () => {
      throw new Error("no json body");
    },
    text: async () => text,
  };
}

beforeEach(() => {
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
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
