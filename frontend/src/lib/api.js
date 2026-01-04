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

    return res.json();
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
    const answersArray = Object.entries(answers).map(
        ([question_id, answer]) => ({
            question_id,
            answer: String(answer || ""),
        }),
    );

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
        const questionList = Array.isArray(exam?.questions)
            ? exam.questions
            : [];
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
        const percentage =
            maxScore > 0 ? Math.round((score / maxScore) * 100) : 0;
        const passed =
            percentage >= (exam?.pass_percent ?? URN_EXAM_PASS_PERCENT);

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

export function getLeaderboard({ limit = 50 } = {}) {
    const qs = new URLSearchParams({ limit: String(limit) }).toString();
    return apiRequest(`/api/v1/leaderboard?${qs}`);
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

export function getClasses() {
    return apiRequest(`/api/v1/classes`);
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
