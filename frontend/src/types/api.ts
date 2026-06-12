/**
 * Typed API models for data exchanged with the backend.
 *
 * SOURCE OF TRUTH: the backend OpenAPI schema. This file is the regeneration
 * target of the `gen:api` script:
 *
 *     npm run gen:api      # emits this file from $OPENAPI_SCHEMA (or
 *                          # $NEXT_PUBLIC_API_BASE_URL/openapi.json)
 *
 * When a backend response/request shape changes, regenerate rather than editing
 * by hand. The core models below mirror the contract consumed by the
 * security-sensitive critical paths (the api client and the auth store); the
 * full generated surface replaces this file once codegen is run against the
 * committed schema.
 */

/** Standard error envelope returned by the backend (`{ error: { message } }`). */
export interface ApiErrorBody {
  error?: {
    message?: string;
    code?: string;
    [key: string]: unknown;
  };
  /** FastAPI-style validation detail (string or structured payload). */
  detail?: string | unknown;
  [key: string]: unknown;
}

/** Authenticated user as returned by the backend and normalized client-side. */
export interface User {
  id: string;
  email?: string | null;
  username?: string | null;
  display_name?: string | null;
  avatar_url?: string | null;
  role?: string | null;
  created_at?: string | null;
  [key: string]: unknown;
}

/** Aggregate gamification/progress stats attached to the current user. */
export interface UserStats {
  xp?: number;
  level?: number;
  streak?: number;
  gems?: number;
  hearts?: number;
  [key: string]: unknown;
}

/** Response shape for `GET /auth/me`. */
export interface AuthMeResponse {
  user: User | null;
  stats?: UserStats | null;
  [key: string]: unknown;
}

/** Response shape for login / register / refresh session endpoints. */
export interface AuthSessionResponse {
  user?: User | null;
  stats?: UserStats | null;
  access_token?: string;
  refresh_token?: string;
  [key: string]: unknown;
}

/** Request body for `POST /auth/register`. */
export interface RegisterRequest {
  email: string;
  password: string;
  display_name?: string;
}

/** Request body for `POST /auth/login`. */
export interface LoginRequest {
  email: string;
  password: string;
}

/** A single leaderboard row. */
export interface LeaderboardEntry {
  user_id?: string;
  username?: string | null;
  display_name?: string | null;
  rank?: number;
  xp?: number;
  [key: string]: unknown;
}

/** Normalized leaderboard payload returned by the api client. */
export interface LeaderboardResponse {
  scope: string;
  entries: LeaderboardEntry[];
  user_rank: number | null;
  user_entry: LeaderboardEntry | null;
  total_users: number;
}

/**
 * Catch-all for endpoints whose response shapes are not yet pinned to the
 * generated schema. Replaced by concrete generated interfaces once `gen:api`
 * runs against the committed OpenAPI document.
 */
export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue };
