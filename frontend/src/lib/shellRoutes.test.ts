import { describe, it, expect } from "vitest";
import { isShellRoute } from "./shellRoutes";

describe("isShellRoute", () => {
  it("suppresses shell on login and register", () => {
    expect(isShellRoute("/login")).toBe(false);
    expect(isShellRoute("/register")).toBe(false);
  });

  it("suppresses shell on motif quiz", () => {
    expect(isShellRoute("/motif/cao-dinh-01/quiz")).toBe(false);
  });

  it("suppresses shell on 3D Viewer (/urns/[urnSlug]) but keeps it on /urns", () => {
    expect(isShellRoute("/urns/cao-dinh")).toBe(false);
    expect(isShellRoute("/urns/nhan-dinh")).toBe(false);
    expect(isShellRoute("/urns")).toBe(true);
  });

  it("suppresses shell on urn exams", () => {
    expect(isShellRoute("/urns/cao-dinh/exam")).toBe(false);
    expect(isShellRoute("/urns/cao-dinh/exam/result")).toBe(false);
    expect(isShellRoute("/urns/cao-dinh/exam/details/1")).toBe(false);
  });

  it("suppresses shell on live classroom but keeps shell on dashboard", () => {
    expect(isShellRoute("/live/session-xyz")).toBe(false);
    expect(isShellRoute("/live/session-xyz/dashboard")).toBe(true);
    expect(isShellRoute("/live")).toBe(true);
  });

  it("keeps shell on standard routes", () => {
    expect(isShellRoute("/")).toBe(true);
    expect(isShellRoute("/atlas")).toBe(true);
    expect(isShellRoute("/collection")).toBe(true);
    expect(isShellRoute("/cuu-dinh")).toBe(true);
  });
});
