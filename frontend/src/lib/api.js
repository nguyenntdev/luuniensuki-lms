const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "";

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
    try {
      const data = await res.json();
      if (data?.error?.message) {
        errorMessage = data.error.message;
      } else if (data?.detail) {
        errorMessage = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      const text = await res.text().catch(() => "");
      if (text) errorMessage = `${errorMessage}: ${text}`;
    }
    throw new Error(errorMessage);
  }

  return res.json();
}

export function register({ email, password, displayName }) {
  return apiRequest(`/api/v1/auth/register`, {
    method: "POST",
    body: { email, password, display_name: displayName },
  });
}

export function login({ email, password }) {
  return apiRequest(`/api/v1/auth/login`, {
    method: "POST",
    body: { email, password },
  });
}

export function getMe({ token }) {
  return apiRequest(`/api/v1/auth/me`, { token });
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
