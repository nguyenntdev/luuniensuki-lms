import type {
  ApiErrorBody,
  AuthMeResponse,
  AuthSessionResponse,
  LeaderboardEntry,
  LeaderboardResponse,
  User,
} from "@/types/api";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "";

export interface ApiErrorOptions {
  status?: number;
  data?: ApiErrorBody | unknown;
}

export class ApiError extends Error {
  status?: number;
  data?: ApiErrorBody | unknown;

  constructor(message: string, { status, data }: ApiErrorOptions = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export function deriveUsernameFromEmail(
  email: string | null | undefined,
): string | null {
  const localPart = String(email || "").split("@", 1)[0] || "";
  const normalized = localPart
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_]+/g, "_")
    .replace(/_{2,}/g, "_")
    .replace(/^_+|_+$/g, "");

  return normalized || null;
}

export function normalizeUser(
  user: User | null | undefined,
  { fallbackUsername }: { fallbackUsername?: string | null } = {},
): User | null | undefined {
  if (!user || typeof user !== "object") return user;

  const username =
    user.username ??
    fallbackUsername ??
    deriveUsernameFromEmail(user.email) ??
    null;
  return { ...user, username };
}

let refreshPromise: Promise<unknown> | null = null;

async function buildApiError(res: Response): Promise<ApiError> {
  let errorMessage = `HTTP ${res.status} ${res.statusText}`;
  let errorData: ApiErrorBody | undefined;
  try {
    errorData = (await res.json()) as ApiErrorBody;
    if (errorData?.error?.message) {
      errorMessage = errorData.error.message;
    } else if (errorData?.detail) {
      errorMessage =
        typeof errorData.detail === "string"
          ? errorData.detail
          : JSON.stringify(errorData.detail);
    }
  } catch {
    const text = await res.text().catch(() => "");
    if (text) errorMessage = `${errorMessage}: ${text}`;
  }
  return new ApiError(errorMessage, {
    status: res.status,
    data: errorData,
  });
}

async function refreshSession(): Promise<unknown> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    const res = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
      method: "POST",
      cache: "no-store",
      credentials: "include",
    });
    if (!res.ok) {
      throw await buildApiError(res);
    }
    return res.json();
  })().finally(() => {
    refreshPromise = null;
  });
  return refreshPromise;
}

async function parseApiResponse(res: Response): Promise<unknown> {
  if (res.status === 204 || res.status === 205) return null;

  const text = await res.text().catch(() => "");
  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export interface ApiRequestOptions {
  method?: string;
  body?: unknown;
  skipRefresh?: boolean;
  cache?: RequestCache;
  keepalive?: boolean;
}

const AUTH_ENDPOINTS = [
  "/api/v1/auth/login",
  "/api/v1/auth/register",
  "/api/v1/auth/logout",
  "/api/v1/auth/refresh",
];

export async function apiRequest<T = unknown>(
  path: string,
  {
    method = "GET",
    body,
    skipRefresh,
    cache = "no-store",
    keepalive,
  }: ApiRequestOptions = {},
): Promise<T> {
  const headers: Record<string, string> = {};
  if (body) headers["content-type"] = "application/json";

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    cache,
    credentials: "include",
    keepalive,
  });

  if (res.status === 401 && !skipRefresh) {
    const isAuthEndpoint = AUTH_ENDPOINTS.includes(path);
    if (!isAuthEndpoint) {
      await refreshSession();
      return apiRequest<T>(path, { method, body, skipRefresh: true });
    }
  }

  if (!res.ok) {
    throw await buildApiError(res);
  }

  return (await parseApiResponse(res)) as T;
}

export interface ApiFormDataOptions {
  method?: string;
  body?: BodyInit;
  skipRefresh?: boolean;
  cache?: RequestCache;
  keepalive?: boolean;
}

export async function apiRequestFormData<T = unknown>(
  path: string,
  {
    method = "POST",
    body,
    skipRefresh,
    cache = "no-store",
    keepalive,
  }: ApiFormDataOptions = {},
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    body,
    cache,
    credentials: "include",
    keepalive,
  });

  if (res.status === 401 && !skipRefresh) {
    const isAuthEndpoint = AUTH_ENDPOINTS.includes(path);
    if (!isAuthEndpoint) {
      await refreshSession();
      return apiRequestFormData<T>(path, { method, body, skipRefresh: true });
    }
  }

  if (!res.ok) {
    throw await buildApiError(res);
  }

  return (await parseApiResponse(res)) as T;
}

export interface ApiBinaryOptions {
  method?: string;
  body?: BodyInit;
  headers?: HeadersInit;
  skipRefresh?: boolean;
  cache?: RequestCache;
  keepalive?: boolean;
  signal?: AbortSignal;
}

export interface BinaryResponse {
  blob: Blob;
  contentType: string;
  headers: Headers;
}

export async function apiRequestBinary(
  path: string,
  {
    method = "POST",
    body,
    headers,
    skipRefresh,
    cache = "no-store",
    keepalive,
    signal,
  }: ApiBinaryOptions = {},
): Promise<BinaryResponse> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body,
    cache,
    credentials: "include",
    keepalive,
    signal,
  });

  if (res.status === 401 && !skipRefresh) {
    const isAuthEndpoint = AUTH_ENDPOINTS.includes(path);
    if (!isAuthEndpoint) {
      await refreshSession();
      return apiRequestBinary(path, {
        method,
        body,
        headers,
        skipRefresh: true,
        cache,
        keepalive,
        signal,
      });
    }
  }

  if (!res.ok) {
    throw await buildApiError(res);
  }

  const blob = await res.blob();
  return {
    blob,
    contentType: res.headers.get("content-type") || "",
    headers: res.headers,
  };
}

function withNormalizedUser(
  res: AuthSessionResponse | AuthMeResponse | null,
): AuthSessionResponse | AuthMeResponse | null {
  if (res && "user" in res && res.user) {
    return { ...res, user: normalizeUser(res.user) ?? null };
  }
  return res;
}

export function register({
  email,
  password,
  displayName,
}: {
  email: string;
  password: string;
  displayName?: string;
}): Promise<AuthSessionResponse | null> {
  return apiRequest<AuthSessionResponse>(`/api/v1/auth/register`, {
    method: "POST",
    body: { email, password, display_name: displayName },
  }).then((res) => withNormalizedUser(res) as AuthSessionResponse | null);
}

export function login({
  email,
  password,
}: {
  email: string;
  password: string;
}): Promise<AuthSessionResponse | null> {
  return apiRequest<AuthSessionResponse>(`/api/v1/auth/login`, {
    method: "POST",
    body: { email, password },
  }).then((res) => withNormalizedUser(res) as AuthSessionResponse | null);
}

export function logout(): Promise<unknown> {
  return apiRequest(`/api/v1/auth/logout`, { method: "POST" });
}

export function getMe(): Promise<AuthMeResponse | null> {
  return apiRequest<AuthMeResponse>(`/api/v1/auth/me`).then(
    (res) => withNormalizedUser(res) as AuthMeResponse | null,
  );
}

export function getMyCollection(): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/collection`);
}

export function getMotifsByUrn(urnNameOrSlug: string): Promise<unknown> {
  const encoded = encodeURIComponent(urnNameOrSlug);
  return apiRequest(`/motifs/${encoded}`);
}

export function unlockProgress({
  motifId,
  meshName,
  tapPosition,
}: {
  motifId: string | number;
  meshName?: string;
  tapPosition?: unknown;
}): Promise<unknown> {
  return apiRequest(`/progress/unlock`, {
    method: "POST",
    body: {
      motif_id: motifId,
      mesh_name: meshName,
      tap_position: tapPosition,
    },
  });
}

export function getUrns(): Promise<unknown> {
  return apiRequest(`/api/v1/urns`);
}

/**
 * Persist annotated motif coordinates (admin-only). Mirrors the
 * import_coordinates.py matching logic server-side: each marker is matched to a
 * motif within its urn by mesh_name then motif_name and its position updated.
 */
export function saveMotifCoordinates({
  coordinates,
}: {
  coordinates: unknown;
}): Promise<unknown> {
  return apiRequest(`/api/v1/admin/motif-coordinates`, {
    method: "POST",
    body: { coordinates },
  });
}

export function getDashboardSummary(): Promise<unknown> {
  return apiRequest(`/api/v1/dashboard/summary`);
}

export function getUrnDetail(urnSlug: string): Promise<unknown> {
  const encoded = encodeURIComponent(urnSlug);
  return apiRequest(`/api/v1/urns/${encoded}`);
}

export function getUrnProgress({
  urnSlug,
}: {
  urnSlug: string;
}): Promise<unknown> {
  const encoded = encodeURIComponent(urnSlug);
  return apiRequest(`/api/v1/urns/${encoded}/progress`);
}

export function getMotifDetail(motifId: string | number): Promise<unknown> {
  const encoded = encodeURIComponent(motifId);
  return apiRequest(`/api/v1/motifs/${encoded}`);
}

export function completeLesson({
  motifId,
}: {
  motifId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(motifId);
  return apiRequest(`/api/v1/motifs/${encoded}/complete-lesson`, {
    method: "POST",
  });
}

export function getMotifQuiz({
  motifId,
}: {
  motifId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(motifId);
  return apiRequest(`/api/v1/motifs/${encoded}/quiz`);
}

export function submitQuiz({
  motifId,
  answers,
  timeTakenSeconds,
}: {
  motifId: string | number;
  answers: unknown;
  timeTakenSeconds?: number;
}): Promise<unknown> {
  return apiRequest(`/api/v1/quizzes/submit`, {
    method: "POST",
    body: {
      motif_id: motifId,
      answers,
      time_taken_seconds: timeTakenSeconds,
    },
  });
}

export async function getUrnExam({
  urnSlug,
}: {
  urnSlug: string;
}): Promise<unknown> {
  const encoded = encodeURIComponent(urnSlug);
  return await apiRequest(`/api/v1/urns/${encoded}/exam`);
}

export async function submitUrnExam({
  urnSlug,
  answers,
  timeTakenSeconds,
}: {
  urnSlug: string;
  answers: Record<string, unknown>;
  timeTakenSeconds?: number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(urnSlug);

  // Convert answers object to array format expected by backend
  const answersArray = Object.entries(answers).map(([question_id, answer]) => ({
    question_id,
    answer: String(answer || ""),
  }));

  return await apiRequest(`/api/v1/urns/${encoded}/exam/submit`, {
    method: "POST",
    body: {
      answers: answersArray,
      time_taken_seconds: timeTakenSeconds,
    },
  });
}

export function getLatestUrnExamAttempt({
  urnSlug,
}: {
  urnSlug: string;
}): Promise<unknown> {
  const encoded = encodeURIComponent(urnSlug);
  return apiRequest(`/api/v1/urns/${encoded}/exam/attempts/latest`);
}

export function getCertificate({
  code,
}: {
  code: string;
}): Promise<unknown> {
  const encoded = encodeURIComponent(code);
  return apiRequest(`/api/v1/certificates/${encoded}`);
}

function normalizeLeaderboardPayload(
  payload: unknown,
  scope = "global",
): LeaderboardResponse {
  if (Array.isArray(payload)) {
    return {
      scope,
      entries: payload as LeaderboardEntry[],
      user_rank: null,
      user_entry: null,
      total_users: payload.length,
    };
  }

  if (payload && typeof payload === "object") {
    const p = payload as Record<string, unknown>;
    const entries = Array.isArray(p.entries)
      ? (p.entries as LeaderboardEntry[])
      : [];
    return {
      scope: typeof p.scope === "string" && p.scope ? p.scope : scope,
      entries,
      user_rank: typeof p.user_rank === "number" ? p.user_rank : null,
      user_entry:
        p.user_entry && typeof p.user_entry === "object"
          ? (p.user_entry as LeaderboardEntry)
          : null,
      total_users:
        typeof p.total_users === "number" ? p.total_users : entries.length,
    };
  }

  return {
    scope,
    entries: [],
    user_rank: null,
    user_entry: null,
    total_users: 0,
  };
}

export async function getLeaderboardData({
  limit = 50,
  scope = "global",
  orderBy = "xp",
  classroomId,
}: {
  limit?: number;
  scope?: string;
  orderBy?: string;
  classroomId?: string | number;
} = {}): Promise<LeaderboardResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    scope: String(scope || "global"),
    order_by: String(orderBy || "xp"),
  });

  if (scope === "class" && classroomId) {
    params.set("classroom_id", String(classroomId));
  }

  const payload = await apiRequest(`/api/v1/leaderboard?${params.toString()}`);
  return normalizeLeaderboardPayload(payload, scope);
}

export async function getLeaderboard({
  limit = 50,
}: {
  limit?: number;
} = {}): Promise<LeaderboardEntry[]> {
  const payload = await getLeaderboardData({ limit });
  return payload.entries;
}

export function getMyBadges(): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/badges`);
}

export function getAllBadges(): Promise<unknown> {
  return apiRequest(`/api/v1/badges`);
}

export function getMyStreak(): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/streak`);
}

export function getMilestones(): Promise<unknown> {
  return apiRequest(`/api/v1/milestones`);
}

export function getPendingMilestones(): Promise<unknown> {
  return apiRequest(`/api/v1/milestones/pending-celebration`);
}

export function celebrateMilestone({
  milestoneId,
}: {
  milestoneId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(milestoneId);
  return apiRequest(`/api/v1/milestones/${encoded}/celebrate`, {
    method: "POST",
  });
}

export function getUserPublicProfile({
  userId,
}: {
  userId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(userId);
  return apiRequest(`/api/v1/users/${encoded}/public`);
}

export function getUserPublicProfileByUsername({
  usernameOrId,
}: {
  usernameOrId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(usernameOrId);
  return apiRequest(`/api/v1/u/${encoded}`);
}

export function setStartingPath({
  urnId,
  urnSlug,
}: {
  urnId?: string | number;
  urnSlug?: string;
}): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/starting-path`, {
    method: "POST",
    body: {
      urn_id: urnId,
      urn_slug: urnSlug,
    },
  });
}

const ANALYTICS_FLUSH_DELAY_MS = 1500;
const ANALYTICS_MAX_BATCH = 10;

export interface AnalyticsEvent {
  name?: string;
  payload?: unknown;
  path?: string | null;
  event_name?: string;
  event_category?: string;
}

let analyticsQueue: AnalyticsEvent[] = [];
let analyticsFlushTimer: number | null = null;
let analyticsFlushPromise: Promise<unknown> | null = null;

function scheduleAnalyticsFlush(): void {
  if (typeof window === "undefined") return;
  if (analyticsFlushTimer) return;

  analyticsFlushTimer = window.setTimeout(() => {
    analyticsFlushTimer = null;
    flushAnalyticsQueue().catch(() => null);
  }, ANALYTICS_FLUSH_DELAY_MS);
}

async function flushAnalyticsQueue({
  keepalive = false,
}: { keepalive?: boolean } = {}): Promise<unknown> {
  if (!analyticsQueue.length) return null;
  if (analyticsFlushPromise) return analyticsFlushPromise;

  const payload = analyticsQueue;
  analyticsQueue = [];
  analyticsFlushPromise = logAnalyticsEvents({
    events: payload,
    keepalive,
  })
    .catch((err) => {
      analyticsQueue = payload.concat(analyticsQueue);
      throw err;
    })
    .finally(() => {
      analyticsFlushPromise = null;
    });
  return analyticsFlushPromise;
}

if (typeof window !== "undefined") {
  const flushOnHide = () => {
    flushAnalyticsQueue({ keepalive: true }).catch(() => null);
  };

  window.addEventListener("pagehide", flushOnHide);
  window.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
      flushOnHide();
    }
  });
}

export function logAnalyticsEvents({
  events,
  keepalive,
}: { events?: AnalyticsEvent[]; keepalive?: boolean } = {}): Promise<unknown> {
  if (!events?.length) {
    return Promise.resolve({ success: true, count: 0 });
  }
  return apiRequest(`/api/v1/analytics/events`, {
    method: "POST",
    body: { events },
    keepalive,
  });
}

export function logAnalyticsEvent({
  name,
  payload,
  path,
}: {
  name?: string;
  payload?: unknown;
  path?: string | null;
}): Promise<unknown> {
  if (!name) return Promise.resolve({ success: true, count: 0 });
  if (typeof window === "undefined") {
    return logAnalyticsEvents({
      events: [{ name, payload, path }],
    });
  }

  analyticsQueue.push({ name, payload, path });
  if (analyticsQueue.length >= ANALYTICS_MAX_BATCH) {
    return flushAnalyticsQueue();
  }

  scheduleAnalyticsFlush();
  return Promise.resolve({ success: true, count: analyticsQueue.length });
}

const API_BASE = `${API_BASE_URL.replace(/\/$/, "")}/api/v1`;

export async function updateProfile(
  data: Record<string, unknown>,
): Promise<AuthMeResponse | null> {
  return apiRequest<AuthMeResponse>(`/api/v1/users/me`, {
    method: "PATCH",
    body: data,
  }).then((res) => withNormalizedUser(res) as AuthMeResponse | null);
}

export async function uploadAvatar(file: File): Promise<unknown> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/users/me/avatar`, {
    method: "POST",
    body: formData,
    cache: "no-store",
    credentials: "include",
  });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function changePassword(
  data: Record<string, unknown>,
): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/change-password`, {
    method: "POST",
    body: data,
  });
}

export function getQuests(): Promise<unknown> {
  return apiRequest(`/api/v1/quests`);
}

export function getQuestDetail({
  questSlug,
}: {
  questSlug: string;
}): Promise<unknown> {
  const encoded = encodeURIComponent(questSlug);
  return apiRequest(`/api/v1/quests/${encoded}`);
}

export function startQuest({
  questSlug,
}: {
  questSlug: string;
}): Promise<unknown> {
  const encoded = encodeURIComponent(questSlug);
  return apiRequest(`/api/v1/quests/${encoded}/start`, { method: "POST" });
}

export function getQuestSummary(): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/quest-summary`);
}

// =============================================================================
// XP BOOST API
// =============================================================================

export function getXpBoostStatus(): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/xp-boost`);
}

export function activateXpBoost({
  durationMinutes = 15,
}: {
  durationMinutes?: number;
} = {}): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/xp-boost/activate`, {
    method: "POST",
    body: { duration_minutes: durationMinutes },
  });
}

// =============================================================================
// CLASS/CLASSROOM API
// =============================================================================

function normalizeClassListPayload(payload: unknown): unknown[] {
  if (Array.isArray(payload)) return payload;
  const p = payload as Record<string, unknown> | null | undefined;
  if (Array.isArray(p?.classes)) return p.classes as unknown[];
  if (Array.isArray(p?.classrooms)) return p.classrooms as unknown[];
  return [];
}

export async function getClasses(): Promise<unknown[]> {
  try {
    const payload = await apiRequest(`/api/v1/classes`);
    return normalizeClassListPayload(payload);
  } catch (err) {
    // Compatibility fallback for environments exposing only /classrooms.
    if (err instanceof ApiError && err.status === 404) {
      const payload = await apiRequest(`/api/v1/classrooms`);
      return normalizeClassListPayload(payload);
    }
    throw err;
  }
}

export async function getEnrolledClassrooms(): Promise<unknown[]> {
  const payload = await apiRequest(`/api/v1/classrooms/enrolled`);
  return normalizeClassListPayload(payload);
}

export function createClass({
  name,
  description,
}: {
  name: string;
  description?: string;
}): Promise<unknown> {
  return apiRequest(`/api/v1/classes`, {
    method: "POST",
    body: { name, description },
  });
}

export function getClassDetail({
  classId,
}: {
  classId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(classId);
  return apiRequest(`/api/v1/classes/${encoded}`);
}

export function addClassMember({
  classId,
  userId,
  email,
}: {
  classId: string | number;
  userId?: string | number;
  email?: string;
}): Promise<unknown> {
  const encoded = encodeURIComponent(classId);
  return apiRequest(`/api/v1/classes/${encoded}/members`, {
    method: "POST",
    body: { user_id: userId, email },
  });
}

export function removeClassMember({
  classId,
  userId,
}: {
  classId: string | number;
  userId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(classId);
  const encodedUser = encodeURIComponent(userId);
  return apiRequest(`/api/v1/classes/${encoded}/members/${encodedUser}`, {
    method: "DELETE",
  });
}

export function assignQuestToClass({
  classId,
  questId,
  dueAt,
}: {
  classId: string | number;
  questId: string | number;
  dueAt?: string;
}): Promise<unknown> {
  const encoded = encodeURIComponent(classId);
  return apiRequest(`/api/v1/classes/${encoded}/assignments`, {
    method: "POST",
    body: { quest_id: questId, due_at: dueAt },
  });
}

// =============================================================================
// LIVE SESSIONS API
// =============================================================================

export function listLiveSessions({
  classroomId,
  limit = 20,
}: {
  classroomId: string | number;
  limit?: number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(classroomId);
  const query = new URLSearchParams({ limit: String(limit) }).toString();
  return apiRequest(`/api/v1/classrooms/${encoded}/live-sessions?${query}`);
}

export function createLiveSession({
  classroomId,
  title,
  startsAt,
  sessionMetadata,
}: {
  classroomId: string | number;
  title?: string;
  startsAt?: string;
  sessionMetadata?: unknown;
}): Promise<unknown> {
  const encoded = encodeURIComponent(classroomId);
  return apiRequest(`/api/v1/classrooms/${encoded}/live-sessions`, {
    method: "POST",
    body: {
      title,
      starts_at: startsAt,
      session_metadata: sessionMetadata,
    },
  });
}

export function getLiveSessionDetail({
  sessionId,
}: {
  sessionId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}`);
}

export function issueLiveSessionToken({
  sessionId,
}: {
  sessionId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/token`, {
    method: "POST",
  });
}

export function joinLiveSession({
  sessionId,
}: {
  sessionId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/join`, {
    method: "POST",
  });
}

export function leaveLiveSession({
  sessionId,
  keepalive = false,
}: {
  sessionId: string | number;
  keepalive?: boolean;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/leave`, {
    method: "POST",
    keepalive,
  });
}

export function listLiveSessionParticipants({
  sessionId,
  includeInactive = false,
}: {
  sessionId: string | number;
  includeInactive?: boolean;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  const query = new URLSearchParams({
    include_inactive: includeInactive ? "true" : "false",
  }).toString();
  return apiRequest(`/api/v1/live-sessions/${encoded}/participants?${query}`);
}

export function listLiveSessionEvents({
  sessionId,
  limit = 50,
  since = null,
}: {
  sessionId: string | number;
  limit?: number;
  since?: string | number | null;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  const params = new URLSearchParams({ limit: String(limit) });
  if (since) params.set("since", String(since));
  return apiRequest(
    `/api/v1/live-sessions/${encoded}/events?${params.toString()}`,
  );
}

export function createLiveSessionEvent({
  sessionId,
  eventType,
  payload = null,
}: {
  sessionId: string | number;
  eventType: string;
  payload?: Record<string, unknown> | null;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/events`, {
    method: "POST",
    body: {
      event_type: eventType,
      payload: payload || {},
    },
  });
}

export function updateLiveParticipantRole({
  sessionId,
  participantId,
  role,
}: {
  sessionId: string | number;
  participantId: string | number;
  role: string;
}): Promise<unknown> {
  const sessionEncoded = encodeURIComponent(sessionId);
  const participantEncoded = encodeURIComponent(participantId);
  return apiRequest(
    `/api/v1/live-sessions/${sessionEncoded}/participants/${participantEncoded}/role`,
    {
      method: "PATCH",
      body: { role },
    },
  );
}

export function hostMuteAllLiveParticipants({
  sessionId,
  includeCohosts = false,
}: {
  sessionId: string | number;
  includeCohosts?: boolean;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/host/mute-all`, {
    method: "POST",
    body: { include_cohosts: includeCohosts },
  });
}

export function updateLiveHostSettings({
  sessionId,
  lockRoom,
  aiEnabled,
  gradeLevel,
  aiCostCeilingUsd,
}: {
  sessionId: string | number;
  lockRoom?: boolean;
  aiEnabled?: boolean;
  gradeLevel?: string;
  aiCostCeilingUsd?: number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  const body: Record<string, unknown> = {};
  if (typeof lockRoom === "boolean") body.lock_room = lockRoom;
  if (typeof aiEnabled === "boolean") body.ai_enabled = aiEnabled;
  if (typeof gradeLevel === "string" && gradeLevel.trim())
    body.grade_level = gradeLevel.trim();
  if (typeof aiCostCeilingUsd === "number" && Number.isFinite(aiCostCeilingUsd)) {
    body.ai_cost_ceiling_usd = aiCostCeilingUsd;
  }
  return apiRequest(`/api/v1/live-sessions/${encoded}/host/settings`, {
    method: "POST",
    body,
  });
}

export function hostRemoveLiveParticipant({
  sessionId,
  participantId,
}: {
  sessionId: string | number;
  participantId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/host/remove-participant`, {
    method: "POST",
    body: { participant_id: participantId },
  });
}

export function askLiveAiTeacher({
  sessionId,
  message,
  mode,
  history,
  gradeLevel,
  speakerName,
}: {
  sessionId: string | number;
  message?: string;
  mode?: string;
  history?: unknown;
  gradeLevel?: string;
  speakerName?: string;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/ai-teacher/reply`, {
    method: "POST",
    body: {
      message,
      mode,
      history,
      grade_level: gradeLevel,
      ...(speakerName ? { speaker_name: speakerName } : {}),
    },
  });
}

export function transcribeLiveAiTeacherVoice({
  sessionId,
  file,
}: {
  sessionId: string | number;
  file: File;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  const formData = new FormData();
  formData.append("file", file);
  return apiRequestFormData(`/api/v1/live-sessions/${encoded}/ai-teacher/stt`, {
    method: "POST",
    body: formData,
  });
}

export function synthesizeLiveAiTeacherVoice({
  sessionId,
  text,
  voice,
  signal,
}: {
  sessionId: string | number;
  text: string;
  voice?: string;
  signal?: AbortSignal;
}): Promise<BinaryResponse> {
  const encoded = encodeURIComponent(sessionId);
  return apiRequestBinary(`/api/v1/live-sessions/${encoded}/ai-teacher/tts`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      text,
      ...(voice ? { voice } : {}),
    }),
    signal,
  });
}

export function ensureLiveAiTeacherPresence({
  sessionId,
}: {
  sessionId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/ai-teacher/presence`, {
    method: "POST",
  });
}

export interface StreamLiveAiTeacherResult {
  answer: string;
  [key: string]: unknown;
}

/**
 * Stream an AI teacher reply via SSE. Calls onDelta(deltaText) as tokens arrive
 * and resolves with the final structured payload ({ answer, mode, citations,
 * rubric, ... }). Falls back to throwing on transport errors so callers can use
 * the non-streaming askLiveAiTeacher instead.
 */
export async function streamLiveAiTeacherReply({
  sessionId,
  message,
  mode,
  speakerName,
  signal,
  onDelta,
}: {
  sessionId: string | number;
  message?: string;
  mode?: string;
  speakerName?: string;
  signal?: AbortSignal;
  onDelta?: (delta: string) => void;
}): Promise<StreamLiveAiTeacherResult> {
  const encoded = encodeURIComponent(sessionId);
  const res = await fetch(
    `${API_BASE_URL}/api/v1/live-sessions/${encoded}/ai-teacher/reply/stream`,
    {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        message,
        mode,
        ...(speakerName ? { speaker_name: speakerName } : {}),
      }),
      credentials: "include",
      cache: "no-store",
      signal,
    },
  );
  if (!res.ok || !res.body) {
    throw new ApiError(`HTTP ${res.status}`, { status: res.status });
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let final: StreamLiveAiTeacherResult = { answer: "" };
  const handleLine = (line: string) => {
    const trimmed = line.trim();
    if (!trimmed.startsWith("data:")) return;
    const jsonStr = trimmed.slice(5).trim();
    if (!jsonStr) return;
    let obj: Record<string, unknown>;
    try {
      obj = JSON.parse(jsonStr) as Record<string, unknown>;
    } catch {
      return;
    }
    if (obj.delta) {
      onDelta?.(String(obj.delta));
    } else if (obj.done) {
      final = obj as StreamLiveAiTeacherResult;
    }
  };
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buffer.indexOf("\n\n")) >= 0) {
      const chunk = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      chunk.split("\n").forEach(handleLine);
    }
  }
  if (buffer.trim()) buffer.split("\n").forEach(handleLine);
  return final;
}

export function endLiveSession({
  sessionId,
}: {
  sessionId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/end`, {
    method: "POST",
  });
}

export function getLiveSessionDashboard({
  sessionId,
}: {
  sessionId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/dashboard`);
}

export function getLiveSessionObservability({
  sessionId,
}: {
  sessionId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/observability`);
}

export function exportLiveSessionTranscriptsJson({
  sessionId,
}: {
  sessionId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/transcripts/export.json`);
}

export function exportLiveSessionTranscriptsCsv({
  sessionId,
}: {
  sessionId: string | number;
}): Promise<BinaryResponse> {
  const encoded = encodeURIComponent(sessionId);
  return apiRequestBinary(
    `/api/v1/live-sessions/${encoded}/transcripts/export.csv`,
    {
      method: "GET",
    },
  );
}

// =============================================================================
// ADMIN / RAG API
// =============================================================================

export function getAdminLessons({
  motifId,
}: {
  motifId?: string | number;
} = {}): Promise<unknown> {
  const qs = motifId
    ? `?${new URLSearchParams({ motif_id: String(motifId) }).toString()}`
    : "";
  return apiRequest(`/api/v1/admin/lessons${qs}`);
}

export function createAdminLesson(
  payload: Record<string, unknown>,
): Promise<unknown> {
  return apiRequest(`/api/v1/admin/lessons`, {
    method: "POST",
    body: payload,
  });
}

export function updateAdminLesson({
  lessonId,
  ...payload
}: {
  lessonId: string | number;
  [key: string]: unknown;
}): Promise<unknown> {
  const encoded = encodeURIComponent(lessonId);
  return apiRequest(`/api/v1/admin/lessons/${encoded}`, {
    method: "PATCH",
    body: payload,
  });
}

export function getAdminQuizQuestions({
  motifId,
}: {
  motifId?: string | number;
} = {}): Promise<unknown> {
  const qs = motifId
    ? `?${new URLSearchParams({ motif_id: String(motifId) }).toString()}`
    : "";
  return apiRequest(`/api/v1/admin/quiz-questions${qs}`);
}

export function createAdminQuizQuestion(
  payload: Record<string, unknown>,
): Promise<unknown> {
  return apiRequest(`/api/v1/admin/quiz-questions`, {
    method: "POST",
    body: payload,
  });
}

export function updateAdminQuizQuestion({
  questionId,
  ...payload
}: {
  questionId: string | number;
  [key: string]: unknown;
}): Promise<unknown> {
  const encoded = encodeURIComponent(questionId);
  return apiRequest(`/api/v1/admin/quiz-questions/${encoded}`, {
    method: "PATCH",
    body: payload,
  });
}

export function getRagDocuments(): Promise<unknown> {
  return apiRequest(`/api/v1/admin/rag/documents`);
}

export function createRagDocument(
  payload: Record<string, unknown>,
): Promise<unknown> {
  return apiRequest(`/api/v1/admin/rag/documents`, {
    method: "POST",
    body: payload,
  });
}

export function uploadRagDocument({
  file,
  title,
}: {
  file: File;
  title?: string;
}): Promise<unknown> {
  const formData = new FormData();
  formData.append("file", file);
  const qs = title
    ? `?${new URLSearchParams({ title: String(title) }).toString()}`
    : "";
  return apiRequestFormData(`/api/v1/admin/rag/documents/upload${qs}`, {
    method: "POST",
    body: formData,
  });
}

export function updateRagDocument({
  docId,
  ...payload
}: {
  docId: string | number;
  [key: string]: unknown;
}): Promise<unknown> {
  const encoded = encodeURIComponent(docId);
  return apiRequest(`/api/v1/admin/rag/documents/${encoded}`, {
    method: "PATCH",
    body: payload,
  });
}

export function deleteRagDocument({
  docId,
}: {
  docId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(docId);
  return apiRequest(`/api/v1/admin/rag/documents/${encoded}`, {
    method: "DELETE",
  });
}

export function getRagSettings(): Promise<unknown> {
  return apiRequest(`/api/v1/admin/rag/settings`);
}

export function updateRagSettings(
  payload: Record<string, unknown>,
): Promise<unknown> {
  return apiRequest(`/api/v1/admin/rag/settings`, {
    method: "PUT",
    body: payload,
  });
}

export function rebuildRagEmbeddings(): Promise<unknown> {
  return apiRequest(`/api/v1/admin/rag/embeddings/rebuild`, {
    method: "POST",
  });
}

export function getRagHealth(): Promise<unknown> {
  return apiRequest(`/api/v1/admin/rag/health`);
}

export function getRecommendations(): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/recommendations`);
}

export function refreshRecommendations({
  useLlm = false,
}: {
  useLlm?: boolean;
} = {}): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/recommendations/refresh`, {
    method: "POST",
    body: { use_llm: useLlm },
  });
}

export function getAiJobs(): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/ai-jobs`);
}

export function retryAiJob({
  jobId,
}: {
  jobId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(jobId);
  return apiRequest(`/api/v1/users/me/ai-jobs/${encoded}/retry`, {
    method: "POST",
  });
}

export function createContentFlag({
  contentType,
  contentId,
  reason,
}: {
  contentType: string;
  contentId: string | number;
  reason?: string;
}): Promise<unknown> {
  return apiRequest(`/api/v1/content/flags`, {
    method: "POST",
    body: {
      content_type: contentType,
      content_id: contentId,
      reason,
    },
  });
}

// =============================================================================
// AI API
// =============================================================================

export interface AiStreamCallbacks {
  onChunk?: (chunk: string) => void;
  onDone?: (full: string, citations: unknown[]) => void;
  onError?: (message: string) => void;
}

export function aiTutor({
  message,
  history = [],
  context,
  level,
}: {
  message?: string;
  history?: unknown[];
  context?: unknown;
  level?: string;
} = {}): Promise<unknown> {
  return apiRequest(`/api/v1/ai/tutor`, {
    method: "POST",
    body: { message, history, context, level },
  });
}

export async function aiTutorStream({
  message,
  history = [],
  context,
  level,
  onChunk,
  onDone,
  onError,
}: {
  message?: string;
  history?: unknown[];
  context?: unknown;
  level?: string;
} & AiStreamCallbacks = {}): Promise<void> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/ai/tutor/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ message, history, context, level }),
      cache: "no-store",
      credentials: "include",
    });

    if (res.status === 401) {
      await refreshSession();
      return aiTutorStream({
        message,
        history,
        context,
        level,
        onChunk,
        onDone,
        onError,
      });
    }

    if (!res.ok) {
      const error = await buildApiError(res);
      onError?.(error.message);
      return;
    }

    if (!res.body) {
      onError?.("AI stream response body is empty");
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    const handleSseLine = (line: string) => {
      if (!line.startsWith("data: ")) return;
      try {
        const data = JSON.parse(line.slice(6)) as Record<string, unknown>;
        if (data.type === "chunk") {
          const chunk = typeof data.content === "string" ? data.content : "";
          if (chunk) onChunk?.(chunk);
        } else if (data.type === "done") {
          onDone?.(
            (data.full_response as string) ?? (data.answer as string) ?? "",
            Array.isArray(data.citations) ? data.citations : [],
          );
        } else if (data.type === "error") {
          onError?.(
            (data.error as string) ??
              (data.message as string) ??
              "AI stream error",
          );
        }
      } catch (e) {
        console.error("Failed to parse SSE data:", e);
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        handleSseLine(line);
      }
    }

    if (buffer.trim()) {
      handleSseLine(buffer.trim());
    }
  } catch (error) {
    onError?.(error instanceof Error ? error.message : String(error));
  }
}

export function aiQa({
  question,
  context,
  limit = 6,
}: {
  question?: string;
  context?: unknown;
  limit?: number;
} = {}): Promise<unknown> {
  return apiRequest(`/api/v1/ai/qa`, {
    method: "POST",
    body: { question, context, limit },
  });
}

export async function aiQaStream({
  question,
  context,
  limit = 6,
  onChunk,
  onDone,
  onError,
}: {
  question?: string;
  context?: unknown;
  limit?: number;
} & AiStreamCallbacks = {}): Promise<void> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/ai/qa/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question, context, limit }),
      cache: "no-store",
      credentials: "include",
    });

    if (res.status === 401) {
      await refreshSession();
      return aiQaStream({ question, context, limit, onChunk, onDone, onError });
    }

    if (!res.ok) {
      const error = await buildApiError(res);
      onError?.(error.message);
      return;
    }

    if (!res.body) {
      onError?.("AI stream response body is empty");
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    const handleSseLine = (line: string) => {
      if (!line.startsWith("data: ")) return;
      try {
        const data = JSON.parse(line.slice(6)) as Record<string, unknown>;
        if (data.type === "chunk") {
          const chunk = typeof data.content === "string" ? data.content : "";
          if (chunk) onChunk?.(chunk);
        } else if (data.type === "done") {
          onDone?.(
            (data.full_response as string) ?? (data.answer as string) ?? "",
            Array.isArray(data.citations) ? data.citations : [],
          );
        } else if (data.type === "error") {
          onError?.(
            (data.error as string) ??
              (data.message as string) ??
              "AI stream error",
          );
        }
      } catch (e) {
        console.error("Failed to parse SSE data:", e);
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        handleSseLine(line);
      }
    }

    if (buffer.trim()) {
      handleSseLine(buffer.trim());
    }
  } catch (error) {
    onError?.(error instanceof Error ? error.message : String(error));
  }
}

export function aiSummary({
  motifId,
  urnSlug,
  level,
}: {
  motifId?: string | number;
  urnSlug?: string;
  level?: string;
} = {}): Promise<unknown> {
  return apiRequest(`/api/v1/ai/summary`, {
    method: "POST",
    body: { motif_id: motifId, urn_slug: urnSlug, level },
  });
}

export function aiFlashcards({
  topic,
  motifId,
  count = 8,
  level,
}: {
  topic?: string;
  motifId?: string | number;
  count?: number;
  level?: string;
} = {}): Promise<unknown> {
  return apiRequest(`/api/v1/ai/flashcards`, {
    method: "POST",
    body: { topic, motif_id: motifId, count, level },
  });
}

export function aiExplain({
  text,
  level,
}: {
  text?: string;
  level?: string;
}): Promise<unknown> {
  return apiRequest(`/api/v1/ai/explain`, {
    method: "POST",
    body: { text, level },
  });
}

export function aiCoach({
  goal,
  availabilityMinutesPerDay,
  daysPerWeek,
}: {
  goal?: string;
  availabilityMinutesPerDay?: number;
  daysPerWeek?: number;
} = {}): Promise<unknown> {
  return apiRequest(`/api/v1/ai/coach`, {
    method: "POST",
    body: {
      goal,
      availability_minutes_per_day: availabilityMinutesPerDay,
      days_per_week: daysPerWeek,
    },
  });
}

export function aiFeedback({
  question,
  correctAnswer,
  userAnswer,
  context,
}: {
  question?: string;
  correctAnswer?: string;
  userAnswer?: string;
  context?: unknown;
} = {}): Promise<unknown> {
  return apiRequest(`/api/v1/ai/feedback`, {
    method: "POST",
    body: {
      question,
      correct_answer: correctAnswer,
      user_answer: userAnswer,
      context,
    },
  });
}

export function aiReviewPlan(): Promise<unknown> {
  return apiRequest(`/api/v1/ai/review-plan`);
}

export function aiDiagnostic({
  urnId,
  urnSlug,
  count = 6,
  level,
}: {
  urnId?: string | number;
  urnSlug?: string;
  count?: number;
  level?: string;
} = {}): Promise<unknown> {
  return apiRequest(`/api/v1/ai/diagnostic`, {
    method: "POST",
    body: {
      urn_id: urnId,
      urn_slug: urnSlug,
      count,
      level,
    },
  });
}

export function aiGenerateLesson(
  payload: Record<string, unknown>,
): Promise<unknown> {
  return apiRequest(`/api/v1/ai/lessons/generate`, {
    method: "POST",
    body: payload,
  });
}

export function aiGenerateQuiz(
  payload: Record<string, unknown>,
): Promise<unknown> {
  return apiRequest(`/api/v1/ai/quizzes/generate`, {
    method: "POST",
    body: payload,
  });
}

export function getQuizHint(
  questionId: string | number,
  hintType: string,
  quizId?: string | number,
): Promise<unknown> {
  return apiRequest(`/api/v1/quiz/questions/${questionId}/hint`, {
    method: "POST",
    body: { hint_type: hintType, quiz_id: quizId },
  });
}

// =============================================================================
// Daily Goal Functions
// =============================================================================

const DAILY_GOAL_STORAGE_KEY = "luuniensuki-daily-goal-storage";
const DAILY_GOAL_LEVELS: Record<string, number> = {
  CASUAL: 10,
  REGULAR: 20,
  SERIOUS: 30,
  INTENSE: 50,
  INSANE: 100,
};

export interface DailyGoalResponse {
  goal_level: string;
  xp_target: number;
  updated_at: string;
  source: string;
}

function readDailyGoalStoreSnapshot(): Record<string, unknown> | null {
  if (typeof window === "undefined") return null;

  try {
    const raw = window.localStorage.getItem(DAILY_GOAL_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    const state = parsed?.state;
    if (!state || typeof state !== "object") return null;
    return state as Record<string, unknown>;
  } catch {
    return null;
  }
}

function buildLocalDailyGoalResponse(): DailyGoalResponse {
  const state = readDailyGoalStoreSnapshot();
  const level = String(state?.goalLevel || "REGULAR").toUpperCase();
  const normalizedLevel = DAILY_GOAL_LEVELS[level] ? level : "REGULAR";
  const updatedAt =
    (state?.lastUpdated as string) || new Date().toISOString();

  return {
    goal_level: normalizedLevel,
    xp_target: DAILY_GOAL_LEVELS[normalizedLevel],
    updated_at: updatedAt,
    source: "local",
  };
}

export async function getDailyGoal(): Promise<unknown> {
  try {
    return await apiRequest("/api/v1/daily-goal/settings");
  } catch {
    return buildLocalDailyGoalResponse();
  }
}

export async function updateDailyGoal(
  goalLevelOrXpTarget: string | number,
): Promise<unknown> {
  const body =
    typeof goalLevelOrXpTarget === "number"
      ? { xp_target: goalLevelOrXpTarget }
      : { goal_level: String(goalLevelOrXpTarget || "").toUpperCase() };

  try {
    return await apiRequest("/api/v1/daily-goal/settings", {
      method: "PUT",
      body,
    });
  } catch {
    return buildLocalDailyGoalResponse();
  }
}

// =============================================================================
// Daily Missions Functions
// =============================================================================

export async function getDailyMissions(): Promise<unknown> {
  return apiRequest("/api/v1/daily-missions");
}

export async function updateMissionProgress(
  missionId: string | number,
  increment = 1,
): Promise<unknown> {
  return apiRequest(`/api/v1/daily-missions/${missionId}/progress`, {
    method: "POST",
    body: { increment },
  });
}

export async function getDailyMissionHistory(days = 30): Promise<unknown> {
  return apiRequest(`/api/v1/daily-missions/history?days=${days}`);
}

// =============================================================================
// Social / Friends Functions
// =============================================================================

export async function getFriends(): Promise<unknown> {
  return apiRequest("/api/v1/social/friends");
}

export async function getFriendRequests(status?: string): Promise<unknown> {
  const query = status ? `?status=${status}` : "";
  return apiRequest(`/api/v1/social/friend-requests${query}`);
}

export async function sendFriendRequest(
  toUserId: string | number,
): Promise<unknown> {
  return apiRequest("/api/v1/social/friend-requests", {
    method: "POST",
    body: { to_user_id: toUserId },
  });
}

export async function acceptFriendRequest(
  requestId: string | number,
): Promise<unknown> {
  return apiRequest(`/api/v1/social/friend-requests/${requestId}/accept`, {
    method: "POST",
  });
}

export async function rejectFriendRequest(
  requestId: string | number,
): Promise<unknown> {
  return apiRequest(`/api/v1/social/friend-requests/${requestId}/reject`, {
    method: "POST",
  });
}

export async function removeFriend(
  friendId: string | number,
): Promise<unknown> {
  return apiRequest(`/api/v1/social/follow/${friendId}`, {
    method: "DELETE",
  });
}

export async function followUser(userId: string | number): Promise<unknown> {
  return apiRequest(`/api/v1/social/follow/${userId}`, {
    method: "POST",
  });
}

export async function unfollowUser(userId: string | number): Promise<unknown> {
  return apiRequest(`/api/v1/social/follow/${userId}`, {
    method: "DELETE",
  });
}

export async function getFollowing(page = 1, pageSize = 20): Promise<unknown> {
  return apiRequest(
    `/api/v1/social/following?page=${page}&page_size=${pageSize}`,
  );
}

export async function getFollowers(page = 1, pageSize = 20): Promise<unknown> {
  return apiRequest(
    `/api/v1/social/followers?page=${page}&page_size=${pageSize}`,
  );
}

export async function searchUsers(query: string): Promise<unknown> {
  const encodedQuery = encodeURIComponent(query);
  return apiRequest(`/api/v1/social/search?q=${encodedQuery}`);
}

export async function sendPeerFeedback({
  toUserId,
  templateKey,
  shareId,
}: {
  toUserId?: string | number;
  templateKey?: string;
  shareId?: string | number;
} = {}): Promise<unknown> {
  return apiRequest(`/api/v1/social/peer-feedback`, {
    method: "POST",
    body: {
      to_user_id: toUserId,
      template_key: templateKey,
      share_id: shareId,
    },
  });
}

export async function getActivityFeed({
  page = 1,
  pageSize = 20,
}: {
  page?: number;
  pageSize?: number;
} = {}): Promise<unknown> {
  return apiRequest(`/api/v1/social/feed?page=${page}&page_size=${pageSize}`);
}

export async function createShare({
  shareType,
  contentId,
  caption,
  visibility = "public",
}: {
  shareType: string;
  contentId: string | number;
  caption?: string;
  visibility?: string;
}): Promise<unknown> {
  return apiRequest(`/api/v1/social/share`, {
    method: "POST",
    body: {
      share_type: shareType,
      content_id: contentId,
      caption,
      visibility,
    },
  });
}

export async function getMyShares({
  page = 1,
  pageSize = 20,
}: {
  page?: number;
  pageSize?: number;
} = {}): Promise<unknown> {
  return apiRequest(
    `/api/v1/social/shares/mine?page=${page}&page_size=${pageSize}`,
  );
}

export async function getShareById({
  shareId,
}: {
  shareId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(shareId);
  return apiRequest(`/api/v1/social/shares/${encoded}`);
}

export async function deleteShare({
  shareId,
}: {
  shareId: string | number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(shareId);
  return apiRequest(`/api/v1/social/shares/${encoded}`, {
    method: "DELETE",
  });
}

export async function getUserActivity({
  userId,
  page = 1,
  pageSize = 20,
}: {
  userId: string | number;
  page?: number;
  pageSize?: number;
}): Promise<unknown> {
  const encoded = encodeURIComponent(userId);
  return apiRequest(
    `/api/v1/users/${encoded}/activity?page=${page}&page_size=${pageSize}`,
  );
}

// =============================================================================
// Spaced Repetition / Practice Functions
// =============================================================================

export async function getDueReviewCards(limit = 20): Promise<unknown> {
  return apiRequest(`/api/v1/review/due?limit=${limit}`);
}

export async function submitReviewResult(
  cardId: string | number,
  quality: number,
): Promise<unknown> {
  return apiRequest(`/api/v1/review/${cardId}`, {
    method: "POST",
    body: { quality },
  });
}

export async function getReviewStats(): Promise<unknown> {
  return apiRequest("/api/v1/review/stats");
}

export async function addCardToReviewDeck(
  motifId: string | number,
): Promise<unknown> {
  return apiRequest("/api/v1/review/cards", {
    method: "POST",
    body: { motif_id: motifId },
  });
}

// =============================================================================
// Gems / Currency Functions
// =============================================================================

export async function getGems(): Promise<unknown> {
  return apiRequest("/api/v1/gems");
}

export async function spendGems(
  amount: number,
  reason?: string,
): Promise<unknown> {
  return apiRequest("/api/v1/gems/spend", {
    method: "POST",
    body: { amount, reason },
  });
}

export async function getGemTransactions(limit = 20): Promise<unknown> {
  return apiRequest(`/api/v1/gems/transactions?limit=${limit}`);
}

// =============================================================================
// Heritage Time-Lapse (.kiro/specs/heritage-time-lapse)
// =============================================================================

export function fetchTimelineEvents({
  from,
  to,
}: {
  from?: string | number;
  to?: string | number;
} = {}): Promise<unknown> {
  const params = new URLSearchParams();
  if (from) params.set("from", String(from));
  if (to) params.set("to", String(to));
  const qs = params.toString();
  const path = `/api/v1/timeline/events${qs ? `?${qs}` : ""}`;
  return apiRequest(path);
}

export function fetchTimelineMotifsByEra(eraSlug: string): Promise<unknown> {
  const params = new URLSearchParams({ era: eraSlug });
  return apiRequest(`/api/v1/timeline/motifs?${params.toString()}`);
}

export function compareMotifs(
  idA: string | number,
  idB: string | number,
): Promise<unknown> {
  const params = new URLSearchParams({ ids: `${idA},${idB}` });
  return apiRequest(`/api/v1/motifs/compare?${params.toString()}`);
}

// =============================================================================
// Heritage Trail Mode (.kiro/specs/heritage-trail-mode)
// =============================================================================

export function listTrails({
  page = 1,
  perPage = 20,
}: {
  page?: number;
  perPage?: number;
} = {}): Promise<unknown> {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(perPage),
  });
  return apiRequest(`/api/v1/trails?${params.toString()}`);
}

export function getTrailDetail(slug: string): Promise<unknown> {
  const encoded = encodeURIComponent(slug);
  return apiRequest(`/api/v1/trails/${encoded}`);
}

export function startTrail(slug: string): Promise<unknown> {
  const encoded = encodeURIComponent(slug);
  return apiRequest(`/api/v1/trails/${encoded}/start`, { method: "POST" });
}

export function completeTrailStep(
  slug: string,
  position: number,
): Promise<unknown> {
  const encoded = encodeURIComponent(slug);
  return apiRequest(`/api/v1/trails/${encoded}/step/${position}/complete`, {
    method: "POST",
  });
}

export function submitTrailCheckpoint(
  slug: string,
  idx: number,
  response: unknown,
): Promise<unknown> {
  const encoded = encodeURIComponent(slug);
  return apiRequest(`/api/v1/trails/${encoded}/checkpoint/${idx}`, {
    method: "POST",
    body: { response },
  });
}

export function setTrailPace(
  trailId: string | number,
  pace: string | number,
): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/trails/${trailId}/pace`, {
    method: "PUT",
    body: { pace },
  });
}

export function verifyTrailCertificate(hash: string): Promise<unknown> {
  const encoded = encodeURIComponent(hash);
  return apiRequest(`/api/v1/certificates/${encoded}/verify`);
}

// =============================================================================
// FSRS Spaced Repetition (.kiro/specs/fsrs-spaced-repetition)
// =============================================================================

export function getDueReviews({
  page = 1,
  pageSize = 20,
}: {
  page?: number;
  pageSize?: number;
} = {}): Promise<unknown> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  return apiRequest(`/api/v1/reviews/due?${params.toString()}`);
}

export function rateReviewCard(
  cardId: string | number,
  rating: number | string,
): Promise<unknown> {
  const encoded = encodeURIComponent(cardId);
  return apiRequest(`/api/v1/reviews/${encoded}/rate`, {
    method: "POST",
    body: { rating },
  });
}

export function getFsrsSettings(): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/fsrs-settings`);
}

export function updateFsrsSettings({
  optimalRetention,
}: {
  optimalRetention?: number;
}): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/fsrs-settings`, {
    method: "PUT",
    body: { optimal_retention: optimalRetention },
  });
}

// =============================================================================
// Streak Repair Economy (.kiro/specs/streak-repair-economy)
// =============================================================================

export function getStreakRepairOptions(): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/streak/repair-options`);
}

export function repairStreak({
  payment,
}: {
  payment?: unknown;
  /**
   * Accepted for call-site compatibility. NOTE: `apiRequest` does not forward
   * custom headers, so this value is not sent — matching the prior JS behavior
   * where the option was silently ignored.
   */
  idempotencyKey?: string;
} = {}): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/streak/repair`, {
    method: "POST",
    body: { payment },
  });
}

export function getMyFriendStreaks(): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/friend-streaks`);
}

export function getFriendStreak(
  otherUserId: string | number,
): Promise<unknown> {
  const encoded = encodeURIComponent(otherUserId);
  return apiRequest(`/api/v1/users/${encoded}/friend-streak`);
}

export function getStreakComebackStatus(): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/streak/comeback-status`);
}

export function getStreakInsurance(): Promise<unknown> {
  return apiRequest(`/api/v1/users/me/streak-insurance`);
}

// --------------------------------------------------------------------------- //
// History-First public surface (Phase 3+)
// --------------------------------------------------------------------------- //
export function listHistoryEntities(params: {
  entityType?: string;
  publicationStatus?: string;
  search?: string;
  offset?: number;
  limit?: number;
} = {}): Promise<unknown> {
  const q = new URLSearchParams();
  if (params.entityType) q.set("entity_type", params.entityType);
  if (params.publicationStatus) q.set("publication_status", params.publicationStatus);
  if (params.search) q.set("search", params.search);
  if (params.offset != null) q.set("offset", String(params.offset));
  if (params.limit != null) q.set("limit", String(params.limit));
  const qs = q.toString();
  return apiRequest(`/api/v1/history/entities${qs ? `?${qs}` : ""}`);
}

export function getHistoryEntityById(id: string | number): Promise<unknown> {
  return apiRequest(`/api/v1/history/entities/${encodeURIComponent(id)}`);
}

export function getHistoryEntityBySlug(slug: string): Promise<unknown> {
  return apiRequest(`/api/v1/history/entities/by-slug/${encodeURIComponent(slug)}`);
}

export function listHistoryEntityClaims(
  entityId: string | number,
  params: { verificationStatus?: string; claimType?: string } = {},
): Promise<unknown> {
  const q = new URLSearchParams();
  if (params.verificationStatus) q.set("verification_status", params.verificationStatus);
  if (params.claimType) q.set("claim_type", params.claimType);
  const qs = q.toString();
  return apiRequest(`/api/v1/history/entities/${encodeURIComponent(entityId)}/claims${qs ? `?${qs}` : ""}`);
}

export function getHistoryClaim(claimId: string | number): Promise<unknown> {
  return apiRequest(`/api/v1/history/claims/${encodeURIComponent(claimId)}`);
}

export function listHistoryClaimSources(claimId: string | number): Promise<unknown> {
  return apiRequest(`/api/v1/history/claims/${encodeURIComponent(claimId)}/sources`);
}

export function listHistorySources(params: {
  sourceType?: string;
  search?: string;
  offset?: number;
  limit?: number;
} = {}): Promise<unknown> {
  const q = new URLSearchParams();
  if (params.sourceType) q.set("source_type", params.sourceType);
  if (params.search) q.set("search", params.search);
  if (params.offset != null) q.set("offset", String(params.offset));
  if (params.limit != null) q.set("limit", String(params.limit));
  const qs = q.toString();
  return apiRequest(`/api/v1/history/sources${qs ? `?${qs}` : ""}`);
}

export function getHistorySource(sourceId: string | number): Promise<unknown> {
  return apiRequest(`/api/v1/history/sources/${encodeURIComponent(sourceId)}`);
}

export function listHistoryEntityRelations(
  entityId: string | number,
): Promise<unknown> {
  return apiRequest(`/api/v1/history/entities/${encodeURIComponent(entityId)}/relations`);
}

export function getHistoryEntityGeography(entityId: string | number): Promise<unknown> {
  return apiRequest(`/api/v1/history/entities/${encodeURIComponent(entityId)}/geography`);
}

export interface ReliefHotspotResponse {
  relief_entity_id?: string | number | null;
  urn_entity_id?: string | number | null;
  slug?: string | null;
  urn_slug?: string | null;
  hotspot?: {
    mesh_name?: string | null;
    pos?: [number, number, number] | number[] | null;
    bounding_radius?: number | null;
  } | null;
  message?: string | null;
}

export function getReliefHotspot(
  urnSlug: string,
  reliefSlug: string,
): Promise<ReliefHotspotResponse> {
  const urn = encodeURIComponent(urnSlug);
  const relief = encodeURIComponent(reliefSlug);
  return apiRequest<ReliefHotspotResponse>(
    `/api/v1/history/reliefs/${urn}/${relief}/hotspot`,
  );
}

export function searchHistory(q: string, limit = 20): Promise<unknown> {
  const params = new URLSearchParams({ q, limit: String(limit) });
  return apiRequest(`/api/v1/history/search?${params.toString()}`);
}

export function getHistoryMap(params: { entityType?: string } = {}): Promise<unknown> {
  const q = new URLSearchParams();
  if (params.entityType) q.set("entity_type", params.entityType);
  const qs = q.toString();
  return apiRequest(`/api/v1/history/map${qs ? `?${qs}` : ""}`);
}

export function listHistoryUrns(): Promise<unknown> {
  return apiRequest(`/api/v1/history/urns`);
}

export interface HistoryGraphNode {
  id?: string | number;
  entity_type?: string | null;
  slug?: string | null;
  name_vi?: string | null;
  name_en?: string | null;
  publication_status?: string | null;
  summary_vi?: string | null;
  summary?: string | null;
  [key: string]: unknown;
}

export interface HistoryGraphEdge {
  source?: string | number;
  target?: string | number;
  predicate?: string | null;
  verification_status?: string | null;
  source_id?: string | number | null;
  [key: string]: unknown;
}

export interface HistoryGraph {
  root_id?: string | number | null;
  nodes?: HistoryGraphNode[];
  edges?: HistoryGraphEdge[];
  [key: string]: unknown;
}

export function getHistoryGraph(
  entityId: string | number,
  depth = 1,
): Promise<HistoryGraph> {
  const params = new URLSearchParams({ depth: String(depth) });
  return apiRequest<HistoryGraph>(
    `/api/v1/history/entities/${encodeURIComponent(entityId)}/graph?${params.toString()}`,
  );
}

export interface HistoryEventItem {
  id?: string | number;
  slug?: string | null;
  name_vi?: string | null;
  name_en?: string | null;
  occurred_on?: string | null;
  description_vi?: string | null;
  era_id?: string | number | null;
  [key: string]: unknown;
}

export interface HistoryEventsResponse {
  items?: HistoryEventItem[];
  meta?: { count?: number };
  [key: string]: unknown;
}

export function getHistoryEvents(
  params: { limit?: number } = {},
): Promise<HistoryEventsResponse> {
  const q = new URLSearchParams();
  if (params.limit != null) q.set("limit", String(params.limit));
  const qs = q.toString();
  return apiRequest<HistoryEventsResponse>(
    `/api/v1/history/events${qs ? `?${qs}` : ""}`,
  );
}

// --------------------------------------------------------------------------- //
// History Story Engine (Phase 10, Spec section 30)
// --------------------------------------------------------------------------- //
export interface StoryBlock {
  type?: string | null;
  title?: string | null;
  body?: string | null;
  quote?: string | null;
  attribution?: string | null;
  image_url?: string | null;
  caption?: string | null;
  entity_id?: string | number | null;
  entity_slug?: string | null;
  entity_ids?: Array<string | number> | null;
  urn_slug?: string | null;
  source_id?: string | number | null;
  quiz_id?: string | number | null;
  question?: string | null;
  [key: string]: unknown;
}

export interface HistoryStory {
  id?: string | number;
  slug?: string | null;
  title_vi?: string | null;
  title_en?: string | null;
  summary_vi?: string | null;
  summary_en?: string | null;
  hero_image_url?: string | null;
  blocks?: StoryBlock[];
  status?: string | null;
  publication_status?: string | null;
  featured?: boolean | null;
  published_at?: string | null;
  [key: string]: unknown;
}

export function listHistoryStories(params: {
  featuredOnly?: boolean;
} = {}): Promise<unknown> {
  const q = new URLSearchParams();
  if (params.featuredOnly) q.set("featured_only", "true");
  const qs = q.toString();
  return apiRequest(`/api/v1/history/stories${qs ? `?${qs}` : ""}`);
}

export function getHistoryStory(slug: string): Promise<unknown> {
  return apiRequest(`/api/v1/history/stories/${encodeURIComponent(slug)}`);
}

export interface HistoryCollectionItem {
  id?: string | number;
  slug?: string | null;
  title_vi?: string | null;
  title_en?: string | null;
  description_vi?: string | null;
  status?: string | null;
  visibility?: string | null;
  entity_ids?: string[];
  source_ids?: string[];
  story_ids?: string[];
  question_ids?: string[];
  published_at?: string | null;
  [key: string]: unknown;
}

export function listHistoryCollections(params: {
  offset?: number;
  limit?: number;
} = {}): Promise<unknown> {
  const q = new URLSearchParams();
  if (params.offset != null) q.set("offset", String(params.offset));
  if (params.limit != null) q.set("limit", String(params.limit));
  const qs = q.toString();
  return apiRequest(`/api/v1/history/collections${qs ? `?${qs}` : ""}`);
}

export function getHistoryCollection(slug: string): Promise<unknown> {
  return apiRequest(`/api/v1/history/collections/${encodeURIComponent(slug)}`);
}

