import { describe, it, expect, vi, beforeEach } from "vitest";

// The middleware reads `process.env.JWT_SECRET_KEY` into a module-level const at
// import time. `vi.hoisted` runs before the (hoisted) imports below, so the
// token-validity branch is active for these tests instead of the presence-only
// fallback.
vi.hoisted(() => {
  process.env.JWT_SECRET_KEY = "test-edge-signing-secret";
});

// Mock `jose` so token validity is driven deterministically and hermetically
// (no real crypto / Edge runtime needed). jwtVerify resolves for a "valid"
// token and rejects for expired/malformed ones.
vi.mock("jose", () => ({
  jwtVerify: vi.fn(),
}));

// Mock `next/server` so NextResponse.next()/redirect() return inspectable
// sentinels instead of real Response objects.
vi.mock("next/server", () => {
  return {
    NextResponse: {
      next: vi.fn(() => ({ kind: "next" })),
      redirect: vi.fn((url: { pathname: string }) => ({
        kind: "redirect",
        url,
      })),
    },
  };
});

import { jwtVerify } from "jose";
import { NextResponse } from "next/server";
import { middleware, stripJsonSuffix } from "./middleware";

const jwtVerifyMock = vi.mocked(jwtVerify);

const ACCESS_COOKIE = "luuniensuki_access";
const REFRESH_COOKIE = "luuniensuki_refresh";

type CookieJar = Record<string, string>;

// Build a minimal NextRequest-shaped object exercising only the fields the
// middleware touches: `nextUrl` (pathname/search/clone/searchParams) and
// `cookies.get(name)?.value`.
function makeRequest({
  pathname = "/dashboard",
  search = "",
  cookies = {},
}: {
  pathname?: string;
  search?: string;
  cookies?: CookieJar;
}) {
  const makeUrl = () => ({
    pathname,
    search,
    searchParams: new URLSearchParams(),
  });
  return {
    nextUrl: {
      ...makeUrl(),
      clone: () => makeUrl(),
    },
    cookies: {
      get: (name: string) =>
        name in cookies ? { value: cookies[name] } : undefined,
    },
  } as never;
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("middleware route guard (Req 13.1)", () => {
  it("redirects to /login when no access or refresh token is present", async () => {
    const res = (await middleware(makeRequest({ cookies: {} }))) as unknown as {
      kind: string;
      url: { pathname: string; searchParams: URLSearchParams };
    };

    expect(res.kind).toBe("redirect");
    expect(res.url.pathname).toBe("/login");
    // jwtVerify should not even be consulted with no access cookie.
    expect(jwtVerifyMock).not.toHaveBeenCalled();
    expect(NextResponse.redirect).toHaveBeenCalledTimes(1);
  });

  it("redirects to /login when the access token is expired", async () => {
    // jose throws (e.g. JWTExpired) for expired tokens.
    jwtVerifyMock.mockRejectedValueOnce(new Error("ERR_JWT_EXPIRED"));

    const res = (await middleware(
      makeRequest({ cookies: { [ACCESS_COOKIE]: "expired.jwt.token" } }),
    )) as unknown as { kind: string; url: { pathname: string } };

    expect(jwtVerifyMock).toHaveBeenCalledTimes(1);
    expect(res.kind).toBe("redirect");
    expect(res.url.pathname).toBe("/login");
  });

  it("redirects to /login when the access token is malformed", async () => {
    jwtVerifyMock.mockRejectedValueOnce(new Error("ERR_JWS_INVALID"));

    const res = (await middleware(
      makeRequest({ cookies: { [ACCESS_COOKIE]: "not-a-jwt" } }),
    )) as unknown as { kind: string; url: { pathname: string } };

    expect(res.kind).toBe("redirect");
    expect(res.url.pathname).toBe("/login");
  });

  it("allows the request when the access token is valid and unexpired", async () => {
    jwtVerifyMock.mockResolvedValueOnce({
      payload: { type: "access", sub: "user-1" },
      protectedHeader: { alg: "HS256" },
    } as never);

    const res = (await middleware(
      makeRequest({ cookies: { [ACCESS_COOKIE]: "valid.jwt.token" } }),
    )) as unknown as { kind: string };

    expect(jwtVerifyMock).toHaveBeenCalledTimes(1);
    expect(res.kind).toBe("next");
    expect(NextResponse.redirect).not.toHaveBeenCalled();
  });

  it("rejects a structurally-valid token whose type is not 'access'", async () => {
    // A refresh token signed with the same secret must not pass the access guard
    // on its own (no refresh cookie present here to fall through).
    jwtVerifyMock.mockResolvedValueOnce({
      payload: { type: "refresh", sub: "user-1" },
      protectedHeader: { alg: "HS256" },
    } as never);

    const res = (await middleware(
      makeRequest({ cookies: { [ACCESS_COOKIE]: "refresh.jwt.token" } }),
    )) as unknown as { kind: string; url: { pathname: string } };

    expect(res.kind).toBe("redirect");
    expect(res.url.pathname).toBe("/login");
  });

  it("preserves the original path as returnUrl on redirect", async () => {
    const res = (await middleware(
      makeRequest({ pathname: "/lessons/42", search: "?tab=quiz" }),
    )) as unknown as { kind: string; url: { searchParams: URLSearchParams } };

    expect(res.kind).toBe("redirect");
    expect(res.url.searchParams.get("returnUrl")).toBe("/lessons/42?tab=quiz");
  });

  it("allows public routes (/login) through without token checks", async () => {
    const res = (await middleware(makeRequest({ pathname: "/login" }))) as unknown as {
      kind: string;
    };

    expect(res.kind).toBe("next");
    expect(jwtVerifyMock).not.toHaveBeenCalled();
  });
});

describe("stripJsonSuffix `.json` route regex (Req 23.2)", () => {
  it("removes a trailing .json suffix", () => {
    expect(stripJsonSuffix("cao-dinh.json")).toBe("cao-dinh");
    expect(stripJsonSuffix("/lessons/intro.json")).toBe("/lessons/intro");
  });

  it("does not strip a non-suffix .json occurrence", () => {
    // Interior occurrence is left intact (anchored `$`).
    expect(stripJsonSuffix("a.json.b")).toBe("a.json.b");
    expect(stripJsonSuffix("config.json.bak")).toBe("config.json.bak");
  });

  it("leaves paths without a .json suffix unchanged", () => {
    expect(stripJsonSuffix("/dashboard")).toBe("/dashboard");
    expect(stripJsonSuffix("")).toBe("");
  });

  it("treats the dot literally (the broken `/\\.json$/` would not)", () => {
    // The fixed regex matches a literal dot, so "Xjson" (no dot) is NOT stripped.
    // The broken pattern `/\\.json$/` matches a backslash + "json", so it would
    // fail to strip real ".json" and behave incorrectly on backslash inputs.
    expect(stripJsonSuffix("Xjson")).toBe("Xjson");
    expect(stripJsonSuffix("page.json")).toBe("page");
  });
});
