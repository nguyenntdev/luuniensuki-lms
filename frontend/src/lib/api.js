const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "";

export class ApiError extends Error {
  constructor(message, { status, data } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export function deriveUsernameFromEmail(email) {
  const localPart = String(email || "").split("@", 1)[0] || "";
  const normalized = localPart
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_]+/g, "_")
    .replace(/_{2,}/g, "_")
    .replace(/^_+|_+$/g, "");

  return normalized || null;
}

export function normalizeUser(user, { fallbackUsername } = {}) {
  if (!user || typeof user !== "object") return user;

  const username =
    user.username ??
    fallbackUsername ??
    deriveUsernameFromEmail(user.email) ??
    null;
  return { ...user, username };
}

let refreshPromise = null;

async function buildApiError(res) {
  let errorMessage = `HTTP ${res.status} ${res.statusText}`;
  let errorData;
  try {
    errorData = await res.json();
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

async function refreshSession() {
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

async function parseApiResponse(res) {
  if (res.status === 204 || res.status === 205) return null;

  const text = await res.text().catch(() => "");
  if (!text) return null;

  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function apiRequest(
  path,
  { method = "GET", body, skipRefresh, cache = "no-store", keepalive } = {},
) {
  const headers = {};
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
    const isAuthEndpoint =
      path === "/api/v1/auth/login" ||
      path === "/api/v1/auth/register" ||
      path === "/api/v1/auth/logout" ||
      path === "/api/v1/auth/refresh";
    if (!isAuthEndpoint) {
      await refreshSession();
      return apiRequest(path, { method, body, skipRefresh: true });
    }
  }

  if (!res.ok) {
    throw await buildApiError(res);
  }

  return parseApiResponse(res);
}

export async function apiRequestFormData(
  path,
  { method = "POST", body, skipRefresh, cache = "no-store", keepalive } = {},
) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    body,
    cache,
    credentials: "include",
    keepalive,
  });

  if (res.status === 401 && !skipRefresh) {
    const isAuthEndpoint =
      path === "/api/v1/auth/login" ||
      path === "/api/v1/auth/register" ||
      path === "/api/v1/auth/logout" ||
      path === "/api/v1/auth/refresh";
    if (!isAuthEndpoint) {
      await refreshSession();
      return apiRequestFormData(path, { method, body, skipRefresh: true });
    }
  }

  if (!res.ok) {
    throw await buildApiError(res);
  }

  return parseApiResponse(res);
}

export async function apiRequestBinary(
  path,
  {
    method = "POST",
    body,
    headers,
    skipRefresh,
    cache = "no-store",
    keepalive,
    signal,
  } = {},
) {
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
    const isAuthEndpoint =
      path === "/api/v1/auth/login" ||
      path === "/api/v1/auth/register" ||
      path === "/api/v1/auth/logout" ||
      path === "/api/v1/auth/refresh";
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

export function register({ email, password, displayName }) {
  return apiRequest(`/api/v1/auth/register`, {
    method: "POST",
    body: { email, password, display_name: displayName },
  }).then((res) =>
    res?.user ? { ...res, user: normalizeUser(res.user) } : res,
  );
}

export function login({ email, password }) {
  return apiRequest(`/api/v1/auth/login`, {
    method: "POST",
    body: { email, password },
  }).then((res) =>
    res?.user ? { ...res, user: normalizeUser(res.user) } : res,
  );
}

export function logout() {
  return apiRequest(`/api/v1/auth/logout`, { method: "POST" });
}

export function getMe() {
  return apiRequest(`/api/v1/auth/me`).then((res) =>
    res?.user ? { ...res, user: normalizeUser(res.user) } : res,
  );
}

export function getMyCollection() {
  return apiRequest(`/api/v1/users/me/collection`);
}

export function getMotifsByUrn(urnNameOrSlug) {
  const encoded = encodeURIComponent(urnNameOrSlug);
  return apiRequest(`/motifs/${encoded}`);
}

export function unlockProgress({ motifId, meshName, tapPosition }) {
  return apiRequest(`/progress/unlock`, {
    method: "POST",
    body: {
      motif_id: motifId,
      mesh_name: meshName,
      tap_position: tapPosition,
    },
  });
}

export function getUrns() {
  return apiRequest(`/api/v1/urns`);
}

export function getDashboardSummary() {
  return apiRequest(`/api/v1/dashboard/summary`);
}

export function getUrnDetail(urnSlug) {
  const encoded = encodeURIComponent(urnSlug);
  return apiRequest(`/api/v1/urns/${encoded}`);
}

export function getUrnProgress({ urnSlug }) {
  const encoded = encodeURIComponent(urnSlug);
  return apiRequest(`/api/v1/urns/${encoded}/progress`);
}

export function getMotifDetail(motifId) {
  const encoded = encodeURIComponent(motifId);
  return apiRequest(`/api/v1/motifs/${encoded}`);
}

export function completeLesson({ motifId }) {
  const encoded = encodeURIComponent(motifId);
  return apiRequest(`/api/v1/motifs/${encoded}/complete-lesson`, {
    method: "POST",
  });
}

export function getMotifQuiz({ motifId }) {
  const encoded = encodeURIComponent(motifId);
  return apiRequest(`/api/v1/motifs/${encoded}/quiz`);
}

export function submitQuiz({ motifId, answers, timeTakenSeconds }) {
  return apiRequest(`/api/v1/quizzes/submit`, {
    method: "POST",
    body: {
      motif_id: motifId,
      answers,
      time_taken_seconds: timeTakenSeconds,
    },
  });
}

const URN_EXAM_PASS_PERCENT = 80;

function getUrnExamAssetPath(urnSlug) {
  const safeSlug = String(urnSlug || "")
    .trim()
    .toLowerCase();
  if (!safeSlug) return "";

  const fileSlug = safeSlug.replace(/-/g, "_");
  return `/urn-exams/${fileSlug}_exam.json`;
}

async function getUrnExamFromStatic(urnSlug) {
  const assetPath = getUrnExamAssetPath(urnSlug);
  if (!assetPath) throw new Error("Urn slug is required");

  const res = await fetch(assetPath, { cache: "no-store" });
  if (!res.ok) {
    throw new Error("Không tìm thấy đề kiểm tra cho đỉnh này.");
  }

  const raw = await res.json();
  const questions = Array.isArray(raw) ? raw : raw?.questions;
  if (!Array.isArray(questions) || !questions.length) {
    throw new Error("Đề kiểm tra không hợp lệ.");
  }

  return {
    urn_slug: urnSlug,
    pass_percent: URN_EXAM_PASS_PERCENT,
    questions: questions.map((q, idx) => ({
      id: q?.id ?? `local-${idx + 1}`,
      question_type: q?.question_type ?? "multiple_choice",
      question_text: q?.question_text ?? "",
      options: Array.isArray(q?.options) ? q.options : null,
      correct_answer: q?.correct_answer ?? null,
      explanation: q?.explanation ?? null,
      difficulty: Math.max(1, Number(q?.difficulty ?? 1) || 1),
    })),
  };
}

export async function getUrnExam({ urnSlug }) {
  const encoded = encodeURIComponent(urnSlug);
  try {
    return await apiRequest(`/api/v1/urns/${encoded}/exam`);
  } catch (err) {
    if (
      err instanceof ApiError &&
      err.status &&
      err.status !== 404 &&
      err.status !== 405
    )
      throw err;
    return getUrnExamFromStatic(urnSlug);
  }
}

export async function submitUrnExam({ urnSlug, answers, timeTakenSeconds }) {
  const encoded = encodeURIComponent(urnSlug);

  // Convert answers object to array format expected by backend
  const answersArray = Object.entries(answers).map(([question_id, answer]) => ({
    question_id,
    answer: String(answer || ""),
  }));

  try {
    return await apiRequest(`/api/v1/urns/${encoded}/exam/submit`, {
      method: "POST",
      body: {
        answers: answersArray,
        time_taken_seconds: timeTakenSeconds,
      },
    });
  } catch (err) {
    if (
      err instanceof ApiError &&
      err.status &&
      err.status !== 404 &&
      err.status !== 405
    )
      throw err;

    const exam = await getUrnExamFromStatic(urnSlug);
    const questionList = Array.isArray(exam?.questions) ? exam.questions : [];
    if (!questionList.length) throw new Error("Đề kiểm tra không hợp lệ.");

    const answerMap = {};
    if (Array.isArray(answers)) {
      for (const a of answers) {
        if (!a) continue;
        const questionId = a.question_id ?? a.questionId ?? a.id;
        if (!questionId) continue;
        answerMap[String(questionId)] = String(a.answer ?? "");
      }
    } else if (answers && typeof answers === "object") {
      for (const [questionId, answer] of Object.entries(answers)) {
        answerMap[String(questionId)] = String(answer ?? "");
      }
    }

    const results = questionList.map((q) => {
      const questionId = String(q.id);
      const submitted = (answerMap[questionId] ?? "").trim();
      const expected = String(q.correct_answer ?? "").trim();
      const correct = Boolean(expected) && submitted === expected;
      return {
        question_id: questionId,
        correct,
        correct_answer: expected,
        user_answer: submitted || null,
        explanation: q.explanation ?? null,
      };
    });

    const score = results.reduce((sum, r) => sum + (r.correct ? 1 : 0), 0);
    const maxScore = results.length;
    const percentage = maxScore > 0 ? Math.round((score / maxScore) * 100) : 0;
    const passed = percentage >= (exam?.pass_percent ?? URN_EXAM_PASS_PERCENT);

    return {
      urn_slug: urnSlug,
      score,
      max_score: maxScore,
      percentage,
      passed,
      pass_percent: exam?.pass_percent ?? URN_EXAM_PASS_PERCENT,
      time_taken_seconds: timeTakenSeconds ?? null,
      certificate: null,
      results,
    };
  }
}

export function getLatestUrnExamAttempt({ urnSlug }) {
  const encoded = encodeURIComponent(urnSlug);
  return apiRequest(`/api/v1/urns/${encoded}/exam/attempts/latest`);
}

export function getCertificate({ code }) {
  const encoded = encodeURIComponent(code);
  return apiRequest(`/api/v1/certificates/${encoded}`);
}

function normalizeLeaderboardPayload(payload, scope = "global") {
  if (Array.isArray(payload)) {
    return {
      scope,
      entries: payload,
      user_rank: null,
      user_entry: null,
      total_users: payload.length,
    };
  }

  if (payload && typeof payload === "object") {
    const entries = Array.isArray(payload.entries) ? payload.entries : [];
    return {
      scope: payload.scope || scope,
      entries,
      user_rank:
        typeof payload.user_rank === "number" ? payload.user_rank : null,
      user_entry:
        payload.user_entry && typeof payload.user_entry === "object"
          ? payload.user_entry
          : null,
      total_users:
        typeof payload.total_users === "number"
          ? payload.total_users
          : entries.length,
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
} = {}) {
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

export async function getLeaderboard({ limit = 50 } = {}) {
  const payload = await getLeaderboardData({ limit });
  return payload.entries;
}

export function getMyBadges() {
  return apiRequest(`/api/v1/users/me/badges`);
}

export function getAllBadges() {
  return apiRequest(`/api/v1/badges`);
}

export function getMyStreak() {
  return apiRequest(`/api/v1/users/me/streak`);
}

export function getMilestones() {
  return apiRequest(`/api/v1/milestones`);
}

export function getPendingMilestones() {
  return apiRequest(`/api/v1/milestones/pending-celebration`);
}

export function celebrateMilestone({ milestoneId }) {
  const encoded = encodeURIComponent(milestoneId);
  return apiRequest(`/api/v1/milestones/${encoded}/celebrate`, {
    method: "POST",
  });
}

export function getUserPublicProfile({ userId }) {
  const encoded = encodeURIComponent(userId);
  return apiRequest(`/api/v1/users/${encoded}/public`);
}

export function getUserPublicProfileByUsername({ usernameOrId }) {
  const encoded = encodeURIComponent(usernameOrId);
  return apiRequest(`/api/v1/u/${encoded}`);
}

export function setStartingPath({ urnId, urnSlug }) {
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
let analyticsQueue = [];
let analyticsFlushTimer = null;
let analyticsFlushPromise = null;

function scheduleAnalyticsFlush() {
  if (typeof window === "undefined") return;
  if (analyticsFlushTimer) return;

  analyticsFlushTimer = window.setTimeout(() => {
    analyticsFlushTimer = null;
    flushAnalyticsQueue().catch(() => null);
  }, ANALYTICS_FLUSH_DELAY_MS);
}

async function flushAnalyticsQueue({ keepalive = false } = {}) {
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

export function logAnalyticsEvents({ events, keepalive } = {}) {
  if (!events?.length) {
    return Promise.resolve({ success: true, count: 0 });
  }
  return apiRequest(`/api/v1/analytics/events`, {
    method: "POST",
    body: { events },
    keepalive,
  });
}

export function logAnalyticsEvent({ name, payload, path }) {
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

export async function updateProfile(data) {
  return apiRequest(`/api/v1/users/me`, {
    method: "PATCH",
    body: data,
  }).then((res) =>
    res?.user ? { ...res, user: normalizeUser(res.user) } : res,
  );
}

export async function uploadAvatar(file) {
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

export async function changePassword(data) {
  return apiRequest(`/api/v1/users/me/change-password`, {
    method: "POST",
    body: data,
  });
}

export function getQuests() {
  return apiRequest(`/api/v1/quests`);
}

export function getQuestDetail({ questSlug }) {
  const encoded = encodeURIComponent(questSlug);
  return apiRequest(`/api/v1/quests/${encoded}`);
}

export function startQuest({ questSlug }) {
  const encoded = encodeURIComponent(questSlug);
  return apiRequest(`/api/v1/quests/${encoded}/start`, { method: "POST" });
}

export function getQuestSummary() {
  return apiRequest(`/api/v1/users/me/quest-summary`);
}

// =============================================================================
// XP BOOST API
// =============================================================================

export function getXpBoostStatus() {
  return apiRequest(`/api/v1/users/me/xp-boost`);
}

export function activateXpBoost({ durationMinutes = 15 } = {}) {
  return apiRequest(`/api/v1/users/me/xp-boost/activate`, {
    method: "POST",
    body: { duration_minutes: durationMinutes },
  });
}

// =============================================================================
// CLASS/CLASSROOM API
// =============================================================================

function normalizeClassListPayload(payload) {
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.classes)) return payload.classes;
  if (Array.isArray(payload?.classrooms)) return payload.classrooms;
  return [];
}

export async function getClasses() {
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

export async function getEnrolledClassrooms() {
  const payload = await apiRequest(`/api/v1/classrooms/enrolled`);
  return normalizeClassListPayload(payload);
}

export function createClass({ name, description }) {
  return apiRequest(`/api/v1/classes`, {
    method: "POST",
    body: { name, description },
  });
}

export function getClassDetail({ classId }) {
  const encoded = encodeURIComponent(classId);
  return apiRequest(`/api/v1/classes/${encoded}`);
}

export function addClassMember({ classId, userId, email }) {
  const encoded = encodeURIComponent(classId);
  return apiRequest(`/api/v1/classes/${encoded}/members`, {
    method: "POST",
    body: { user_id: userId, email },
  });
}

export function removeClassMember({ classId, userId }) {
  const encoded = encodeURIComponent(classId);
  const encodedUser = encodeURIComponent(userId);
  return apiRequest(`/api/v1/classes/${encoded}/members/${encodedUser}`, {
    method: "DELETE",
  });
}

export function assignQuestToClass({ classId, questId, dueAt }) {
  const encoded = encodeURIComponent(classId);
  return apiRequest(`/api/v1/classes/${encoded}/assignments`, {
    method: "POST",
    body: { quest_id: questId, due_at: dueAt },
  });
}

export function listLiveSessions({ classroomId, limit = 20 }) {
  const encoded = encodeURIComponent(classroomId);
  const query = new URLSearchParams({ limit: String(limit) }).toString();
  return apiRequest(`/api/v1/classrooms/${encoded}/live-sessions?${query}`);
}

export function createLiveSession({ classroomId, title, startsAt, sessionMetadata }) {
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

export function getLiveSessionDetail({ sessionId }) {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}`);
}

export function issueLiveSessionToken({ sessionId }) {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/token`, {
    method: "POST",
  });
}

export function joinLiveSession({ sessionId }) {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/join`, {
    method: "POST",
  });
}

export function leaveLiveSession({ sessionId, keepalive = false }) {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/leave`, {
    method: "POST",
    keepalive,
  });
}

export function listLiveSessionParticipants({ sessionId, includeInactive = false }) {
  const encoded = encodeURIComponent(sessionId);
  const query = new URLSearchParams({
    include_inactive: includeInactive ? "true" : "false",
  }).toString();
  return apiRequest(`/api/v1/live-sessions/${encoded}/participants?${query}`);
}

export function listLiveSessionEvents({ sessionId, limit = 50, since = null }) {
  const encoded = encodeURIComponent(sessionId);
  const params = new URLSearchParams({ limit: String(limit) });
  if (since) params.set("since", String(since));
  return apiRequest(`/api/v1/live-sessions/${encoded}/events?${params.toString()}`);
}

export function createLiveSessionEvent({ sessionId, eventType, payload = null }) {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/events`, {
    method: "POST",
    body: {
      event_type: eventType,
      payload: payload || {},
    },
  });
}

export function updateLiveParticipantRole({ sessionId, participantId, role }) {
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

export function hostMuteAllLiveParticipants({ sessionId, includeCohosts = false }) {
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
}) {
  const encoded = encodeURIComponent(sessionId);
  const body = {};
  if (typeof lockRoom === "boolean") body.lock_room = lockRoom;
  if (typeof aiEnabled === "boolean") body.ai_enabled = aiEnabled;
  if (typeof gradeLevel === "string" && gradeLevel.trim()) body.grade_level = gradeLevel.trim();
  if (typeof aiCostCeilingUsd === "number" && Number.isFinite(aiCostCeilingUsd)) {
    body.ai_cost_ceiling_usd = aiCostCeilingUsd;
  }
  return apiRequest(`/api/v1/live-sessions/${encoded}/host/settings`, {
    method: "POST",
    body,
  });
}

export function hostRemoveLiveParticipant({ sessionId, participantId }) {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/host/remove-participant`, {
    method: "POST",
    body: { participant_id: participantId },
  });
}

export function askLiveAiTeacher({ sessionId, message, mode, history, gradeLevel }) {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/ai-teacher/reply`, {
    method: "POST",
    body: {
      message,
      mode,
      history,
      grade_level: gradeLevel,
    },
  });
}

export function transcribeLiveAiTeacherVoice({ sessionId, file }) {
  const encoded = encodeURIComponent(sessionId);
  const formData = new FormData();
  formData.append("file", file);
  return apiRequestFormData(`/api/v1/live-sessions/${encoded}/ai-teacher/stt`, {
    method: "POST",
    body: formData,
  });
}

export function synthesizeLiveAiTeacherVoice({ sessionId, text, voice, signal }) {
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

export function ensureLiveAiTeacherPresence({ sessionId }) {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/ai-teacher/presence`, {
    method: "POST",
  });
}

export function endLiveSession({ sessionId }) {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/end`, {
    method: "POST",
  });
}

export function getLiveSessionDashboard({ sessionId }) {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/dashboard`);
}

export function getLiveSessionObservability({ sessionId }) {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/observability`);
}

export function exportLiveSessionTranscriptsJson({ sessionId }) {
  const encoded = encodeURIComponent(sessionId);
  return apiRequest(`/api/v1/live-sessions/${encoded}/transcripts/export.json`);
}

export function exportLiveSessionTranscriptsCsv({ sessionId }) {
  const encoded = encodeURIComponent(sessionId);
  return apiRequestBinary(`/api/v1/live-sessions/${encoded}/transcripts/export.csv`, {
    method: "GET",
  });
}

export function getAdminLessons({ motifId } = {}) {
  const qs = motifId
    ? `?${new URLSearchParams({ motif_id: String(motifId) }).toString()}`
    : "";
  return apiRequest(`/api/v1/admin/lessons${qs}`);
}

export function createAdminLesson(payload) {
  return apiRequest(`/api/v1/admin/lessons`, {
    method: "POST",
    body: payload,
  });
}

export function updateAdminLesson({ lessonId, ...payload }) {
  const encoded = encodeURIComponent(lessonId);
  return apiRequest(`/api/v1/admin/lessons/${encoded}`, {
    method: "PATCH",
    body: payload,
  });
}

export function getAdminQuizQuestions({ motifId } = {}) {
  const qs = motifId
    ? `?${new URLSearchParams({ motif_id: String(motifId) }).toString()}`
    : "";
  return apiRequest(`/api/v1/admin/quiz-questions${qs}`);
}

export function createAdminQuizQuestion(payload) {
  return apiRequest(`/api/v1/admin/quiz-questions`, {
    method: "POST",
    body: payload,
  });
}

export function updateAdminQuizQuestion({ questionId, ...payload }) {
  const encoded = encodeURIComponent(questionId);
  return apiRequest(`/api/v1/admin/quiz-questions/${encoded}`, {
    method: "PATCH",
    body: payload,
  });
}

export function getRagDocuments() {
  return apiRequest(`/api/v1/admin/rag/documents`);
}

export function createRagDocument(payload) {
  return apiRequest(`/api/v1/admin/rag/documents`, {
    method: "POST",
    body: payload,
  });
}

export function uploadRagDocument({ file, title }) {
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

export function updateRagDocument({ docId, ...payload }) {
  const encoded = encodeURIComponent(docId);
  return apiRequest(`/api/v1/admin/rag/documents/${encoded}`, {
    method: "PATCH",
    body: payload,
  });
}

export function deleteRagDocument({ docId }) {
  const encoded = encodeURIComponent(docId);
  return apiRequest(`/api/v1/admin/rag/documents/${encoded}`, {
    method: "DELETE",
  });
}

export function getRagSettings() {
  return apiRequest(`/api/v1/admin/rag/settings`);
}

export function updateRagSettings(payload) {
  return apiRequest(`/api/v1/admin/rag/settings`, {
    method: "PUT",
    body: payload,
  });
}

export function rebuildRagEmbeddings() {
  return apiRequest(`/api/v1/admin/rag/embeddings/rebuild`, {
    method: "POST",
  });
}

export function getRagHealth() {
  return apiRequest(`/api/v1/admin/rag/health`);
}

export function getRecommendations() {
  return apiRequest(`/api/v1/users/me/recommendations`);
}

export function refreshRecommendations({ useLlm = false } = {}) {
  return apiRequest(`/api/v1/users/me/recommendations/refresh`, {
    method: "POST",
    body: { use_llm: useLlm },
  });
}

export function getAiJobs() {
  return apiRequest(`/api/v1/users/me/ai-jobs`);
}

export function retryAiJob({ jobId }) {
  const encoded = encodeURIComponent(jobId);
  return apiRequest(`/api/v1/users/me/ai-jobs/${encoded}/retry`, {
    method: "POST",
  });
}

export function createContentFlag({ contentType, contentId, reason }) {
  return apiRequest(`/api/v1/content/flags`, {
    method: "POST",
    body: {
      content_type: contentType,
      content_id: contentId,
      reason,
    },
  });
}

export function aiTutor({ message, history = [], context, level } = {}) {
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
} = {}) {
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

    const handleSseLine = (line) => {
      if (!line.startsWith("data: ")) return;
      try {
        const data = JSON.parse(line.slice(6));
        if (data.type === "chunk") {
          const chunk = typeof data.content === "string" ? data.content : "";
          if (chunk) onChunk?.(chunk);
        } else if (data.type === "done") {
          onDone?.(
            data.full_response ?? data.answer ?? "",
            Array.isArray(data.citations) ? data.citations : [],
          );
        } else if (data.type === "error") {
          onError?.(data.error ?? data.message ?? "AI stream error");
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
      buffer = lines.pop();

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

export function aiQa({ question, context, limit = 6 } = {}) {
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
} = {}) {
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

    const handleSseLine = (line) => {
      if (!line.startsWith("data: ")) return;
      try {
        const data = JSON.parse(line.slice(6));
        if (data.type === "chunk") {
          const chunk = typeof data.content === "string" ? data.content : "";
          if (chunk) onChunk?.(chunk);
        } else if (data.type === "done") {
          onDone?.(
            data.full_response ?? data.answer ?? "",
            Array.isArray(data.citations) ? data.citations : [],
          );
        } else if (data.type === "error") {
          onError?.(data.error ?? data.message ?? "AI stream error");
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
      buffer = lines.pop();

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

export function aiSummary({ motifId, urnSlug, level } = {}) {
  return apiRequest(`/api/v1/ai/summary`, {
    method: "POST",
    body: { motif_id: motifId, urn_slug: urnSlug, level },
  });
}

export function aiFlashcards({ topic, motifId, count = 8, level } = {}) {
  return apiRequest(`/api/v1/ai/flashcards`, {
    method: "POST",
    body: { topic, motif_id: motifId, count, level },
  });
}

export function aiExplain({ text, level }) {
  return apiRequest(`/api/v1/ai/explain`, {
    method: "POST",
    body: { text, level },
  });
}

export function aiCoach({ goal, availabilityMinutesPerDay, daysPerWeek } = {}) {
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
} = {}) {
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

export function aiReviewPlan() {
  return apiRequest(`/api/v1/ai/review-plan`);
}

export function aiDiagnostic({ urnId, urnSlug, count = 6, level } = {}) {
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

export function aiGenerateLesson(payload) {
  return apiRequest(`/api/v1/ai/lessons/generate`, {
    method: "POST",
    body: payload,
  });
}

export function aiGenerateQuiz(payload) {
  return apiRequest(`/api/v1/ai/quizzes/generate`, {
    method: "POST",
    body: payload,
  });
}

export function getQuizHint(questionId, hintType, quizId) {
  return apiRequest(`/api/v1/quiz/questions/${questionId}/hint`, {
    method: "POST",
    body: { hint_type: hintType, quiz_id: quizId },
  });
}

// Daily Goal Functions
const DAILY_GOAL_STORAGE_KEY = "luuniensuki-daily-goal-storage";
const DAILY_GOAL_LEVELS = {
  CASUAL: 10,
  REGULAR: 20,
  SERIOUS: 30,
  INTENSE: 50,
  INSANE: 100,
};

function readDailyGoalStoreSnapshot() {
  if (typeof window === "undefined") return null;

  try {
    const raw = window.localStorage.getItem(DAILY_GOAL_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    const state = parsed?.state;
    if (!state || typeof state !== "object") return null;
    return state;
  } catch {
    return null;
  }
}

function buildLocalDailyGoalResponse() {
  const state = readDailyGoalStoreSnapshot();
  const level = String(state?.goalLevel || "REGULAR").toUpperCase();
  const normalizedLevel = DAILY_GOAL_LEVELS[level] ? level : "REGULAR";
  const updatedAt = state?.lastUpdated || new Date().toISOString();

  return {
    goal_level: normalizedLevel,
    xp_target: DAILY_GOAL_LEVELS[normalizedLevel],
    updated_at: updatedAt,
    source: "local",
  };
}

export async function getDailyGoal() {
  try {
    return await apiRequest("/api/v1/daily-goal/settings");
  } catch {
    return buildLocalDailyGoalResponse();
  }
}

export async function updateDailyGoal(goalLevelOrXpTarget) {
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

// Daily Missions Functions
export async function getDailyMissions() {
  return apiRequest("/api/v1/daily-missions");
}

export async function updateMissionProgress(missionId, increment = 1) {
  return apiRequest(`/api/v1/daily-missions/${missionId}/progress`, {
    method: "POST",
    body: { increment },
  });
}

export async function getDailyMissionHistory(days = 30) {
  return apiRequest(`/api/v1/daily-missions/history?days=${days}`);
}

// =============================================================================
// Social / Friends Functions
// =============================================================================

export async function getFriends() {
  return apiRequest("/api/v1/social/friends");
}

export async function getFriendRequests(status) {
  const query = status ? `?status=${status}` : "";
  return apiRequest(`/api/v1/social/friend-requests${query}`);
}

export async function sendFriendRequest(toUserId) {
  return apiRequest("/api/v1/social/friend-requests", {
    method: "POST",
    body: { to_user_id: toUserId },
  });
}

export async function acceptFriendRequest(requestId) {
  return apiRequest(`/api/v1/social/friend-requests/${requestId}/accept`, {
    method: "POST",
  });
}

export async function rejectFriendRequest(requestId) {
  return apiRequest(`/api/v1/social/friend-requests/${requestId}/reject`, {
    method: "POST",
  });
}

export async function removeFriend(friendId) {
  return apiRequest(`/api/v1/social/follow/${friendId}`, {
    method: "DELETE",
  });
}

export async function followUser(userId) {
  return apiRequest(`/api/v1/social/follow/${userId}`, {
    method: "POST",
  });
}

export async function unfollowUser(userId) {
  return apiRequest(`/api/v1/social/follow/${userId}`, {
    method: "DELETE",
  });
}

export async function getFollowing(page = 1, pageSize = 20) {
  return apiRequest(
    `/api/v1/social/following?page=${page}&page_size=${pageSize}`,
  );
}

export async function getFollowers(page = 1, pageSize = 20) {
  return apiRequest(
    `/api/v1/social/followers?page=${page}&page_size=${pageSize}`,
  );
}

export async function searchUsers(query) {
  const encodedQuery = encodeURIComponent(query);
  return apiRequest(`/api/v1/social/search?q=${encodedQuery}`);
}

export async function sendPeerFeedback({ toUserId, templateKey, shareId } = {}) {
  return apiRequest(`/api/v1/social/peer-feedback`, {
    method: "POST",
    body: {
      to_user_id: toUserId,
      template_key: templateKey,
      share_id: shareId,
    },
  });
}

export async function getActivityFeed({ page = 1, pageSize = 20 } = {}) {
  return apiRequest(`/api/v1/social/feed?page=${page}&page_size=${pageSize}`);
}

export async function createShare({
  shareType,
  contentId,
  caption,
  visibility = "public",
}) {
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

export async function getMyShares({ page = 1, pageSize = 20 } = {}) {
  return apiRequest(
    `/api/v1/social/shares/mine?page=${page}&page_size=${pageSize}`,
  );
}

export async function getShareById({ shareId }) {
  const encoded = encodeURIComponent(shareId);
  return apiRequest(`/api/v1/social/shares/${encoded}`);
}

export async function deleteShare({ shareId }) {
  const encoded = encodeURIComponent(shareId);
  return apiRequest(`/api/v1/social/shares/${encoded}`, {
    method: "DELETE",
  });
}

export async function getUserActivity({ userId, page = 1, pageSize = 20 } = {}) {
  const encoded = encodeURIComponent(userId);
  return apiRequest(
    `/api/v1/users/${encoded}/activity?page=${page}&page_size=${pageSize}`,
  );
}

// =============================================================================
// Spaced Repetition / Practice Functions
// =============================================================================

export async function getDueReviewCards(limit = 20) {
  return apiRequest(`/api/v1/review/due?limit=${limit}`);
}

export async function submitReviewResult(cardId, quality) {
  return apiRequest(`/api/v1/review/${cardId}`, {
    method: "POST",
    body: { quality },
  });
}

export async function getReviewStats() {
  return apiRequest("/api/v1/review/stats");
}

export async function addCardToReviewDeck(motifId) {
  return apiRequest("/api/v1/review/cards", {
    method: "POST",
    body: { motif_id: motifId },
  });
}

// =============================================================================
// Gems / Currency Functions
// =============================================================================

export async function getGems() {
  return apiRequest("/api/v1/gems");
}

export async function spendGems(amount, reason) {
  return apiRequest("/api/v1/gems/spend", {
    method: "POST",
    body: { amount, reason },
  });
}

export async function getGemTransactions(limit = 20) {
  return apiRequest(`/api/v1/gems/transactions?limit=${limit}`);
}
