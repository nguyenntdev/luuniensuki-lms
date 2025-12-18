"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import UserProfile from "@/components/UserProfile";
import { ApiError, apiRequest, getUserPublicProfileByUsername } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "";

function getErrorMessage(err) {
  return err instanceof Error ? err.message : String(err);
}

async function getErrorMessageFromResponse(res) {
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
  return errorMessage;
}

function getUserInitials({ display_name: displayName, email } = {}) {
  const base = String(displayName || email || "").trim();
  if (!base) return "U";
  const parts = base.split(/\s+/).filter(Boolean);
  const first = parts[0]?.[0] || "U";
  const second = parts.length > 1 ? parts[parts.length - 1]?.[0] : "";
  return `${first}${second}`.toUpperCase();
}

function validateUsername(username) {
  const trimmed = String(username || "").trim();
  if (!trimmed) return null;
  if (trimmed.length < 3) return "Username cần ít nhất 3 ký tự.";
  if (trimmed.length > 30) return "Username tối đa 30 ký tự.";
  if (!/^[a-z][a-z0-9_]*$/.test(trimmed)) {
    return "Chỉ dùng chữ thường (a-z), số (0-9) và dấu gạch dưới (_), bắt đầu bằng chữ.";
  }
  return null;
}

export default function Page() {
  const token = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);

  const [isEditing, setIsEditing] = useState(false);
  const [displayName, setDisplayName] = useState("");
  const [username, setUsername] = useState("");
  const [bio, setBio] = useState("");
  const [avatarPreview, setAvatarPreview] = useState("");
  const [saving, setSaving] = useState(false);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [usernameStatus, setUsernameStatus] = useState(null); // checking | available | taken | current | unknown

  const fileInputRef = useRef(null);
  const avatarObjectUrlRef = useRef(null);

  useEffect(() => {
    return () => {
      if (avatarObjectUrlRef.current) URL.revokeObjectURL(avatarObjectUrlRef.current);
    };
  }, []);

  useEffect(() => {
    if (!user) return;
    if (!isEditing) {
      setDisplayName(user.display_name || "");
      setUsername(user.username || "");
      setBio(user.bio || "");
      setAvatarPreview(user.avatar_url || "");
      setUsernameStatus(null);
    }
  }, [user, isEditing]);

  useEffect(() => {
    if (!isEditing) return;
    if (!user) return;

    const trimmed = username.trim();
    const currentUsername = String(user.username || "").trim();
    const validationError = validateUsername(trimmed);

    if (!trimmed) {
      setUsernameStatus(null);
      return;
    }

    if (validationError) {
      setUsernameStatus(null);
      return;
    }

    if (trimmed === currentUsername) {
      setUsernameStatus("current");
      return;
    }

    let cancelled = false;
    setUsernameStatus("checking");
    const timer = setTimeout(async () => {
      try {
        await getUserPublicProfileByUsername(trimmed);
        if (!cancelled) setUsernameStatus("taken");
      } catch (err) {
        if (cancelled) return;
        if (err instanceof ApiError) {
          if (err.status === 404) setUsernameStatus("available");
          else if (err.status === 403) setUsernameStatus("taken");
          else setUsernameStatus("unknown");
          return;
        }
        setUsernameStatus("unknown");
      }
    }, 450);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [isEditing, user, username]);

  const initials = getUserInitials(user || {});
  const hasAvatar = Boolean(avatarPreview || user?.avatar_url);
  const avatarSrc = avatarPreview || user?.avatar_url || "";

  async function handleSave() {
    if (!token) return;

    setSaving(true);
    setError(null);
    setSuccess(null);

    const trimmedUsername = username.trim();
    const currentUsername = String(user?.username || "").trim();
    const usernameValidationError = validateUsername(trimmedUsername);
    if (trimmedUsername && usernameValidationError) {
      setSaving(false);
      setError(usernameValidationError);
      return;
    }
    if (trimmedUsername && trimmedUsername !== currentUsername && usernameStatus === "taken") {
      setSaving(false);
      setError("Username này đã được sử dụng. Vui lòng chọn username khác.");
      return;
    }

    const payload = {
      display_name: displayName.trim(),
      bio,
    };
    if (trimmedUsername && trimmedUsername !== currentUsername) payload.username = trimmedUsername;

    try {
      const res = await apiRequest(`/api/v1/users/me`, {
        method: "PATCH",
        token,
        body: payload,
      });

      const updatedUser = res?.user || {};
      useAuthStore.setState((state) => ({
        user: {
          ...(state.user || {}),
          ...updatedUser,
          display_name: updatedUser.display_name ?? payload.display_name,
          username: updatedUser.username ?? payload.username ?? state.user?.username,
          bio: payload.bio,
        },
      }));

      setIsEditing(false);
      setSuccess("Đã lưu thay đổi hồ sơ.");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  function handleCancel() {
    setIsEditing(false);
    setError(null);
    setSuccess(null);
    setDisplayName(user?.display_name || "");
    setUsername(user?.username || "");
    setBio(user?.bio || "");
    setAvatarPreview(user?.avatar_url || "");
  }

  async function uploadAvatar(file) {
    if (!token) return;

    setError(null);
    setSuccess(null);
    setUploadingAvatar(true);

    if (avatarObjectUrlRef.current) {
      URL.revokeObjectURL(avatarObjectUrlRef.current);
      avatarObjectUrlRef.current = null;
    }

    const objectUrl = URL.createObjectURL(file);
    avatarObjectUrlRef.current = objectUrl;
    setAvatarPreview(objectUrl);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE_URL}/api/v1/users/me/avatar`, {
        method: "POST",
        headers: {
          authorization: `Bearer ${token}`,
        },
        body: formData,
        cache: "no-store",
      });

      if (!res.ok) throw new Error(await getErrorMessageFromResponse(res));
      const data = await res.json();

      useAuthStore.setState((state) => ({
        user: {
          ...(state.user || {}),
          avatar_url: data?.avatar_url,
        },
      }));

      if (avatarObjectUrlRef.current) {
        URL.revokeObjectURL(avatarObjectUrlRef.current);
        avatarObjectUrlRef.current = null;
      }

      setAvatarPreview(data?.avatar_url || "");
      setSuccess("Đã cập nhật ảnh đại diện.");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setUploadingAvatar(false);
    }
  }

  async function handleAvatarFileChange(e) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    await uploadAvatar(file);
  }

  if (!token) {
    return (
      <main className="mx-auto max-w-5xl px-6 py-10">
        <div className="rounded-xl border bg-card p-6">
          <h1 className="text-xl font-display font-semibold">Hồ sơ cá nhân</h1>
          <p className="mt-2 text-sm text-muted-foreground">Vui lòng đăng nhập để chỉnh sửa hồ sơ của bạn.</p>
          <div className="mt-4">
            <Link href="/login" className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">
              Đăng Nhập
            </Link>
          </div>
        </div>
      </main>
    );
  }

  return (
    <>
      <main className="mx-auto max-w-6xl p-6">
        <div className="rounded-xl border bg-card p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-display font-bold text-foreground">Hồ sơ cá nhân</h1>
              <p className="mt-1 text-sm text-muted-foreground">Cập nhật tên hiển thị, giới thiệu và ảnh đại diện.</p>
            </div>

            {!isEditing ? (
              <button
                type="button"
                onClick={() => {
                  setError(null);
                  setSuccess(null);
                  setIsEditing(true);
                }}
                className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
              >
                Chỉnh sửa
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleCancel}
                  disabled={saving || uploadingAvatar}
                  className="rounded-lg border border-border bg-background px-4 py-2 text-sm font-medium text-foreground hover:bg-muted disabled:opacity-60"
                >
                  Hủy
                </button>
                <button
                  type="button"
                  onClick={handleSave}
                  disabled={saving || uploadingAvatar}
                  className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
                >
                  {saving ? "Đang lưu..." : "Lưu"}
                </button>
              </div>
            )}
          </div>

          {!user ? (
            <div className="mt-6 text-sm text-muted-foreground">Đang tải hồ sơ...</div>
          ) : (
            <div className="mt-6 grid gap-6 sm:grid-cols-[160px_1fr]">
              <div>
                <div className="flex items-center gap-4">
                  <div className="h-16 w-16 overflow-hidden rounded-full border border-border bg-muted flex items-center justify-center">
                    {hasAvatar ? (
                      <img src={avatarSrc} alt="Ảnh đại diện" className="h-full w-full object-cover" />
                    ) : (
                      <span className="text-sm font-semibold text-primary">{initials}</span>
                    )}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-foreground truncate">{user.email}</div>
                    <div className="text-xs text-muted-foreground">ID: {user.id}</div>
                  </div>
                </div>

                {isEditing ? (
                  <div className="mt-4">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/png,image/jpeg,image/webp"
                      className="hidden"
                      onChange={handleAvatarFileChange}
                      disabled={uploadingAvatar}
                    />
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploadingAvatar}
                      className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm font-medium text-foreground hover:bg-muted disabled:opacity-60"
                    >
                      {uploadingAvatar ? "Đang tải ảnh..." : "Tải ảnh đại diện"}
                    </button>
                    <p className="mt-2 text-xs text-muted-foreground">Hỗ trợ PNG/JPG/WebP.</p>
                  </div>
                ) : null}
              </div>

              <div className="grid gap-4">
                <div>
                  <label className="block text-xs font-medium text-muted-foreground">Tên người dùng (username)</label>
                  {isEditing ? (
                    <>
                      <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="mt-1 block w-full rounded-md border-input bg-background shadow-sm focus:border-primary focus:ring-primary sm:text-sm text-foreground"
                        placeholder="vd: nguyen_van_a"
                      />
                      {(() => {
                        const trimmed = username.trim();
                        const validationError = validateUsername(trimmed);
                        if (trimmed && validationError) {
                          return <p className="mt-1 text-xs text-destructive">{validationError}</p>;
                        }
                        if (!trimmed) {
                          return (
                            <p className="mt-1 text-xs text-muted-foreground">
                              Chỉ dùng chữ thường (a-z), số (0-9) và dấu gạch dưới (_).
                            </p>
                          );
                        }
                        if (usernameStatus === "checking") {
                          return <p className="mt-1 text-xs text-muted-foreground">Đang kiểm tra khả dụng...</p>;
                        }
                        if (usernameStatus === "available") {
                          return <p className="mt-1 text-xs text-success">Username có thể sử dụng.</p>;
                        }
                        if (usernameStatus === "taken") {
                          return <p className="mt-1 text-xs text-destructive">Username đã được sử dụng.</p>;
                        }
                        if (usernameStatus === "current") {
                          return <p className="mt-1 text-xs text-success">Đây là username hiện tại của bạn.</p>;
                        }
                        if (usernameStatus === "unknown") {
                          return (
                            <p className="mt-1 text-xs text-muted-foreground">
                              Không thể kiểm tra username lúc này. Bạn vẫn có thể lưu và thử lại sau.
                            </p>
                          );
                        }
                        return null;
                      })()}
                    </>
                  ) : (
                    <div className="mt-1 text-sm text-muted-foreground">{user.username ? `@${user.username}` : "—"}</div>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-muted-foreground">Tên hiển thị</label>
                  {isEditing ? (
                    <input
                      type="text"
                      value={displayName}
                      onChange={(e) => setDisplayName(e.target.value)}
                      className="mt-1 block w-full rounded-md border-input bg-background shadow-sm focus:border-primary focus:ring-primary sm:text-sm text-foreground"
                      placeholder="Nhập tên hiển thị..."
                    />
                  ) : (
                    <div className="mt-1 text-sm text-foreground">{user.display_name || "—"}</div>
                  )}
                </div>

                <div>
                  <label className="block text-xs font-medium text-muted-foreground">Giới thiệu</label>
                  {isEditing ? (
                    <textarea
                      rows={4}
                      value={bio}
                      onChange={(e) => setBio(e.target.value)}
                      className="mt-1 block w-full resize-y rounded-md border-input bg-background shadow-sm focus:border-primary focus:ring-primary sm:text-sm text-foreground"
                      placeholder="Viết vài dòng về bạn..."
                    />
                  ) : (
                    <div className="mt-1 whitespace-pre-wrap text-sm text-muted-foreground">
                      {user.bio ? user.bio : "Chưa có giới thiệu."}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {error ? (
            <div className="mt-4 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          ) : null}
          {success ? (
            <div className="mt-4 rounded-lg border border-success/30 bg-success/10 p-3 text-sm text-success">
              {success}
            </div>
          ) : null}
        </div>
      </main>

      <UserProfile />
    </>
  );
}
