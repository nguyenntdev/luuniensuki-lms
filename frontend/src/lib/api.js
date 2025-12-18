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

  const username = user.username ?? fallbackUsername ?? deriveUsernameFromEmail(user.email) ?? null;
  return { ...user, username };
}

export async function apiRequest(path, { method = "GET", body, token } = {}) {
  const headers = {};
  if (body) headers["content-type"] = "application/json";
  if (token) headers["authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });

  if (!res.ok) {
    let errorMessage = `HTTP ${res.status} ${res.statusText}`;
    let errorData;
    try {
      errorData = await res.json();
      if (errorData?.error?.message) {
        errorMessage = errorData.error.message;
      } else if (errorData?.detail) {
        errorMessage = typeof errorData.detail === "string" ? errorData.detail : JSON.stringify(errorData.detail);
      }
    } catch {
      const text = await res.text().catch(() => "");
      if (text) errorMessage = `${errorMessage}: ${text}`;
    }
    throw new ApiError(errorMessage, { status: res.status, data: errorData });
  }

  return res.json();
}

export function register({ email, password, displayName }) {
  return apiRequest(`/api/v1/auth/register`, {
    method: "POST",
    body: { email, password, display_name: displayName },
  }).then((res) => (res?.user ? { ...res, user: normalizeUser(res.user) } : res));
}

export function login({ email, password }) {
  return apiRequest(`/api/v1/auth/login`, {
    method: "POST",
    body: { email, password },
  }).then((res) => (res?.user ? { ...res, user: normalizeUser(res.user) } : res));
}

export function getMe({ token }) {
  return apiRequest(`/api/v1/auth/me`, { token }).then((res) => (res?.user ? { ...res, user: normalizeUser(res.user) } : res));
}

export function getMyCollection({ token }) {
  return apiRequest(`/api/v1/users/me/collection`, { token });
}

export function getMotifsByUrn(urnNameOrSlug) {
  const encoded = encodeURIComponent(urnNameOrSlug);
  return apiRequest(`/motifs/${encoded}`);
}

export function unlockProgress({ token, motifId, meshName, tapPosition }) {
  return apiRequest(`/progress/unlock`, {
    method: "POST",
    token,
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

export function getUrnDetail(urnSlug) {
  const encoded = encodeURIComponent(urnSlug);
  return apiRequest(`/api/v1/urns/${encoded}`);
}

export function getMotifDetail(motifId) {
  const encoded = encodeURIComponent(motifId);
  return apiRequest(`/api/v1/motifs/${encoded}`);
}

export function completeLesson({ token, motifId }) {
  const encoded = encodeURIComponent(motifId);
  return apiRequest(`/api/v1/motifs/${encoded}/complete-lesson`, { method: "POST", token });
}

export function getMotifQuiz({ token, motifId }) {
  const encoded = encodeURIComponent(motifId);
  return apiRequest(`/api/v1/motifs/${encoded}/quiz`, { token });
}

export function submitQuiz({ token, motifId, answers, timeTakenSeconds }) {
  return apiRequest(`/api/v1/quizzes/submit`, {
    method: "POST",
    token,
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

export async function getUrnExam({ token, urnSlug }) {
  const encoded = encodeURIComponent(urnSlug);
  try {
    return await apiRequest(`/api/v1/urns/${encoded}/exam`, { token });
  } catch (err) {
    if (err instanceof ApiError && err.status && err.status !== 404 && err.status !== 405) throw err;
    return getUrnExamFromStatic(urnSlug);
  }
}

export async function submitUrnExam({ token, urnSlug, answers, timeTakenSeconds }) {
  const encoded = encodeURIComponent(urnSlug);

  // Convert answers object to array format expected by backend
  const answersArray = Object.entries(answers).map(([question_id, answer]) => ({
    question_id,
    answer: String(answer || ""),
  }));

  try {
    return await apiRequest(`/api/v1/urns/${encoded}/exam/submit`, {
      method: "POST",
      token,
      body: {
        answers: answersArray,
        time_taken_seconds: timeTakenSeconds,
      },
    });
  } catch (err) {
    if (err instanceof ApiError && err.status && err.status !== 404 && err.status !== 405) throw err;

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
      results,
    };
  }
}

export function getLeaderboard({ limit = 50 } = {}) {
  const qs = new URLSearchParams({ limit: String(limit) }).toString();
  return apiRequest(`/api/v1/leaderboard?${qs}`);
}

export function getMyBadges({ token }) {
  return apiRequest(`/api/v1/users/me/badges`, { token });
}

export function getAllBadges() {
  return apiRequest(`/api/v1/badges`);
}

export function getMyStreak({ token }) {
  return apiRequest(`/api/v1/users/me/streak`, { token });
}

export function getUserPublicProfile(userId) {
  const encoded = encodeURIComponent(userId);
  return apiRequest(`/api/v1/users/${encoded}/public`);
}

export function getUserPublicProfileByUsername(usernameOrId) {
  const encoded = encodeURIComponent(usernameOrId);
  return apiRequest(`/api/v1/u/${encoded}`);
}

const API_BASE = `${API_BASE_URL.replace(/\/$/, "")}/api/v1`;

function getToken() {
  if (typeof window === "undefined") return "";
  try {
    const raw = window.localStorage.getItem("luuniensuki-auth");
    if (!raw) return "";
    const parsed = JSON.parse(raw);
    return parsed?.state?.accessToken || "";
  } catch {
    return "";
  }
}

export async function updateProfile(data) {
  const res = await fetch(`${API_BASE}/users/me`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Update failed");
  const json = await res.json();
  return json?.user ? { ...json, user: normalizeUser(json.user) } : json;
}

export async function uploadAvatar(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/users/me/avatar`, {
    method: "POST",
    headers: { Authorization: `Bearer ${getToken()}` },
    body: formData,
  });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function changePassword(data) {
  const res = await fetch(`${API_BASE}/users/me/change-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${getToken()}` },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Change password failed");
  return res.json();
}
