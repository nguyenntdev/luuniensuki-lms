# 06_Auth_System.md

Authentication + user dashboard integration for **FastAPI (JWT)** and **Next.js (Zustand)**.

## Backend (FastAPI)

### `backend/requirements.txt` (add JWT + hashing)

```txt
fastapi>=0.110,<1.0
uvicorn[standard]>=0.29,<1.0

SQLAlchemy>=2.0,<3.0
psycopg[binary]>=3.1,<4.0

pydantic>=2.6,<3.0
pydantic-settings>=2.2,<3.0
python-dotenv>=1.0,<2.0

python-jose[cryptography]>=3.3,<4.0
bcrypt>=5.0,<6.0
email-validator>=2.1,<3.0

gunicorn>=21.2,<23.0
```

### `docker-compose.yml` (JWT env vars)

```yaml
  api:
    environment:
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:-dev-insecure-change-me}
      JWT_ALGORITHM: ${JWT_ALGORITHM:-HS256}
      ACCESS_TOKEN_EXPIRE_MINUTES: ${ACCESS_TOKEN_EXPIRE_MINUTES:-60}
      REFRESH_TOKEN_EXPIRE_DAYS: ${REFRESH_TOKEN_EXPIRE_DAYS:-30}
```

### `backend/security.py` (password hashing + JWT creation)

```py
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
from jose import jwt

MAX_BCRYPT_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > MAX_BCRYPT_PASSWORD_BYTES:
        raise ValueError("Password too long")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > MAX_BCRYPT_PASSWORD_BYTES:
        return False
    return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))


def create_jwt_token(
    *,
    subject: str,
    secret_key: str,
    algorithm: str,
    expires_delta: timedelta,
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire_at = now + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire_at.timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, secret_key, algorithm=algorithm)
```

### `backend/main.py` (auth endpoints + `get_current_user` + protected progress + dashboard data)

#### 1) Settings (JWT + rank thresholds)

```py
DISCOVERY_XP = 25
XP_RANKS = [
    {"level": 1, "name": "Lính Mới", "xp": 0},
    {"level": 2, "name": "Thư Sinh", "xp": 500},
    {"level": 3, "name": "Tú Tài", "xp": 1500},
    {"level": 4, "name": "Cử Nhân", "xp": 3500},
    {"level": 5, "name": "Tiến Sĩ", "xp": 7000},
    {"level": 6, "name": "Thám Hoa", "xp": 12000},
    {"level": 7, "name": "Bảng Nhãn", "xp": 20000},
    {"level": 8, "name": "Trạng Nguyên", "xp": 35000},
    {"level": 9, "name": "Hàn Lâm", "xp": 55000},
    {"level": 10, "name": "Sử Quan", "xp": 80000},
]

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/luuniensuki"
    log_level: str = "info"
    interaction_tolerance_multiplier: float = 1.25

    jwt_secret_key: str = "dev-insecure-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
```

#### 2) Dependency: `get_current_user` (JWT Bearer)

```py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        subject = payload.get("sub")
        token_type = payload.get("type")
        if not subject or token_type != "access":
            raise credentials_exception
        user_id = UUID(subject)
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user
```

#### 3) Auth APIs (Register / Login / Me)

```py
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    role: str
    total_xp: int


class AuthRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    display_name: str = Field(min_length=1, max_length=100)


class AuthLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class AuthResponse(BaseModel):
    user: UserOut
    access_token: str
    refresh_token: str


@app.post("/api/v1/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: AuthRegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    existing = db.execute(select(User).where(User.email == str(payload.email))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=str(payload.email),
        password_hash="",
        display_name=payload.display_name,
    )
    try:
        user.password_hash = hash_password(payload.password)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password too long")
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    db.refresh(user)

    access_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims={"type": "access"},
    )
    refresh_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        extra_claims={"type": "refresh"},
    )

    return AuthResponse(
        user=UserOut(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            role=user.role.value,
            total_xp=user.total_xp,
        ),
        access_token=access_token,
        refresh_token=refresh_token,
    )

@app.post("/api/v1/auth/login", response_model=AuthResponse)
def login(payload: AuthLoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.execute(select(User).where(User.email == str(payload.email))).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        extra_claims={"type": "access"},
    )
    refresh_token = create_jwt_token(
        subject=str(user.id),
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
        extra_claims={"type": "refresh"},
    )

    return AuthResponse(
        user=UserOut(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            role=user.role.value,
            total_xp=user.total_xp,
        ),
        access_token=access_token,
        refresh_token=refresh_token,
    )

class RankOut(BaseModel):
    level: int
    name: str
    xp: int


class UserStatsOut(BaseModel):
    total_xp: int
    rank: RankOut
    xp_to_next_rank: int
    next_rank: Optional[RankOut] = None


class AuthMeResponse(BaseModel):
    user: UserOut
    stats: UserStatsOut

@app.get("/api/v1/auth/me", response_model=AuthMeResponse)
def me(current_user: User = Depends(get_current_user)) -> AuthMeResponse:
    current_rank, next_rank, xp_to_next = _compute_rank(current_user.total_xp)
    return AuthMeResponse(
        user=UserOut(
            id=current_user.id,
            email=current_user.email,
            display_name=current_user.display_name,
            avatar_url=current_user.avatar_url,
            role=current_user.role.value,
            total_xp=current_user.total_xp,
        ),
        stats=UserStatsOut(
            total_xp=current_user.total_xp,
            rank=RankOut(**current_rank),
            xp_to_next_rank=xp_to_next,
            next_rank=(RankOut(**next_rank) if next_rank else None),
        ),
    )
```

#### 4) Protect gameplay progress: `POST /progress/unlock`

Key change: **no `user_id` in body**; user comes from JWT.

```py
class ProgressUnlockRequest(BaseModel):
    motif_id: Optional[UUID] = None
    mesh_name: Optional[str] = None
    tap_position: Optional[TapPosition] = None

    @model_validator(mode="after")
    def _validate_reference(self) -> "ProgressUnlockRequest":
        if self.motif_id is None and not self.mesh_name:
            raise ValueError("Either motif_id or mesh_name is required.")
        return self

@app.post("/progress/unlock", response_model=ProgressUnlockResponse)
def unlock_progress(
    payload: ProgressUnlockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProgressUnlockResponse:
    user = current_user

    if payload.motif_id is not None:
        motif = db.get(Motif, payload.motif_id)
    else:
        motif = db.execute(select(Motif).where(Motif.mesh_name == payload.mesh_name)).scalar_one_or_none()

    if motif is None:
        raise HTTPException(status_code=404, detail="Motif not found")

    if payload.mesh_name is not None and motif.mesh_name != payload.mesh_name:
        raise HTTPException(status_code=400, detail="mesh_name does not match motif")

    if payload.tap_position is not None and motif.bounding_radius > 0:
        dx = payload.tap_position.x - motif.pos_x
        dy = payload.tap_position.y - motif.pos_y
        dz = payload.tap_position.z - motif.pos_z
        distance = math.sqrt(dx * dx + dy * dy + dz * dz)
        allowed = motif.bounding_radius * settings.interaction_tolerance_multiplier
        if distance > allowed:
            raise HTTPException(status_code=400, detail="Tap position outside bounding radius")

    now = datetime.now(timezone.utc)

    progress = db.execute(
        select(UserProgress).where(UserProgress.user_id == user.id, UserProgress.motif_id == motif.id)
    ).scalar_one_or_none()

    xp_awarded = 0
    if progress is None:
        progress = UserProgress(
            user_id=user.id,
            motif_id=motif.id,
            status=UnlockStatus.discovered,
            discovered_at=now,
            xp_earned=DISCOVERY_XP,
        )
        db.add(progress)
        user.total_xp += DISCOVERY_XP
        xp_awarded = DISCOVERY_XP
    else:
        if progress.status == UnlockStatus.hidden:
            progress.status = UnlockStatus.discovered
            progress.discovered_at = progress.discovered_at or now

        if progress.xp_earned < DISCOVERY_XP:
            delta = DISCOVERY_XP - progress.xp_earned
            progress.xp_earned = DISCOVERY_XP
            user.total_xp += delta
            xp_awarded = delta

    user.last_active_at = now

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        progress = db.execute(
            select(UserProgress).where(UserProgress.user_id == user.id, UserProgress.motif_id == motif.id)
        ).scalar_one()
        if progress.status == UnlockStatus.hidden:
            progress.status = UnlockStatus.discovered
            progress.discovered_at = progress.discovered_at or now
        if progress.xp_earned < DISCOVERY_XP:
            delta = DISCOVERY_XP - progress.xp_earned
            progress.xp_earned = DISCOVERY_XP
            user.total_xp += delta
            xp_awarded = max(xp_awarded, delta)
        user.last_active_at = now
        db.commit()

    return ProgressUnlockResponse(
        user_id=user.id,
        motif_id=motif.id,
        status=progress.status.value,
        discovered_at=progress.discovered_at,
        xp_awarded=xp_awarded,
        total_xp=user.total_xp,
    )
```

#### 5) Dashboard Data: `GET /api/v1/users/me/collection`

Returns **all motifs** + user’s status (`hidden|discovered|learned|mastered`) and a quest progress summary.

```py
class CollectionItemOut(BaseModel):
    motif_id: UUID
    mesh_name: str
    name: str
    name_en: Optional[str] = None
    category: str
    rarity: str
    thumbnail_url: Optional[str] = None
    status: str


class QuestProgressOut(BaseModel):
    quest_name: str
    total: int
    discovered: int
    progress_percent: float


class CollectionStatsOut(BaseModel):
    total: int
    discovered: int
    learned: int
    mastered: int
    quest: QuestProgressOut


class UserCollectionResponse(BaseModel):
    items: list[CollectionItemOut]
    stats: CollectionStatsOut


@app.get("/api/v1/users/me/collection", response_model=UserCollectionResponse)
def get_my_collection(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserCollectionResponse:

    motifs = db.execute(
        select(Motif)
        .where(Motif.is_active.is_(True))
        .order_by(Motif.display_order.nulls_last(), Motif.name)
    ).scalars().all()
    progress_entries = db.execute(select(UserProgress).where(UserProgress.user_id == current_user.id)).scalars().all()
    progress_by_motif_id = {p.motif_id: p for p in progress_entries}

    discovered = learned = mastered = 0
    quest_total = quest_discovered = 0
    items: list[CollectionItemOut] = []

    for motif in motifs:
        progress = progress_by_motif_id.get(motif.id)
        status_value = progress.status.value if progress else UnlockStatus.hidden.value

        if status_value == UnlockStatus.discovered.value:
            discovered += 1
        elif status_value == UnlockStatus.learned.value:
            learned += 1
        elif status_value == UnlockStatus.mastered.value:
            mastered += 1

        if motif.category == MotifCategory.thao_moc:
            quest_total += 1
            if status_value != UnlockStatus.hidden.value:
                quest_discovered += 1

        items.append(
            CollectionItemOut(
                motif_id=motif.id,
                mesh_name=motif.mesh_name,
                name=motif.name,
                name_en=motif.name_en,
                category=motif.category.value,
                rarity=motif.rarity.value,
                thumbnail_url=motif.thumbnail_url,
                status=status_value,
            )
        )

    total = len(motifs)
    progress_percent = (quest_discovered / quest_total * 100.0) if quest_total > 0 else 0.0

    return UserCollectionResponse(
        items=items,
        stats=CollectionStatsOut(
            total=total,
            discovered=discovered,
            learned=learned,
            mastered=mastered,
            quest=QuestProgressOut(
                quest_name="Ngự Uyển Ký Sự (The Royal Gardens)",
                total=quest_total,
                discovered=quest_discovered,
                progress_percent=progress_percent,
            ),
        ),
    )
```

---

## Frontend (Next.js)

These are drop-in client components/stores (App Router friendly). They assume:

- `NEXT_PUBLIC_API_BASE_URL` can point to the FastAPI host for local dev (e.g. `http://localhost:8000`). In production behind Nginx, prefer same-origin (leave unset so it uses `""`).
- JWT is stored client-side (Zustand persist) and sent as `Authorization: Bearer <token>`.

### `frontend/src/lib/api.js`

```js
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
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`);
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
```

### `frontend/src/stores/authStore.js`

```js
"use client";

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import { getMe, login, register } from "@/lib/api";

export const useAuthStore = create(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,
      stats: null,
      loading: false,
      error: null,

      isAuthenticated: () => Boolean(get().accessToken),

      logout: () => set({ accessToken: null, refreshToken: null, user: null, stats: null, error: null }),

      register: async ({ email, password, displayName }) => {
        set({ loading: true, error: null });
        try {
          const res = await register({ email, password, displayName });
          set({
            accessToken: res.access_token,
            refreshToken: res.refresh_token,
            user: res.user,
            loading: false,
          });
          await get().fetchMe();
          return res;
        } catch (err) {
          set({ loading: false, error: err instanceof Error ? err.message : String(err) });
          throw err;
        }
      },

      login: async ({ email, password }) => {
        set({ loading: true, error: null });
        try {
          const res = await login({ email, password });
          set({
            accessToken: res.access_token,
            refreshToken: res.refresh_token,
            user: res.user,
            loading: false,
          });
          await get().fetchMe();
          return res;
        } catch (err) {
          set({ loading: false, error: err instanceof Error ? err.message : String(err) });
          throw err;
        }
      },

      fetchMe: async () => {
        const token = get().accessToken;
        if (!token) return null;

        try {
          const res = await getMe({ token });
          set({ user: res.user, stats: res.stats });
          return res;
        } catch (err) {
          set({ error: err instanceof Error ? err.message : String(err) });
          return null;
        }
      },
    }),
    {
      name: "luuniensuki-auth",
      version: 1,
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
);
```

### `frontend/src/components/LoginPage.js`

```jsx
"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { useAuthStore } from "@/stores/authStore";

export default function LoginPage() {
  const router = useRouter();
  const authLogin = useAuthStore((s) => s.login);
  const authRegister = useAuthStore((s) => s.register);
  const loading = useAuthStore((s) => s.loading);
  const error = useAuthStore((s) => s.error);

  const [mode, setMode] = useState("login"); // "login" | "register"
  const isRegister = mode === "register";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");

  const submitLabel = useMemo(() => (isRegister ? "Create account" : "Sign in"), [isRegister]);

  async function onSubmit(e) {
    e.preventDefault();
    if (loading) return;

    if (isRegister) {
      await authRegister({ email, password, displayName });
    } else {
      await authLogin({ email, password });
    }

    router.push("/dashboard");
  }

  return (
    <div className="min-h-dvh bg-gray-950 text-white">
      <div className="mx-auto flex min-h-dvh max-w-md flex-col justify-center px-6 py-10">
        <h1 className="text-2xl font-semibold">Lưu Niên Sử Kí</h1>
        <p className="mt-1 text-sm text-gray-300">Sign in to save progress and build your collection.</p>

        <div className="mt-6 flex rounded-lg bg-white/5 p-1">
          <button
            type="button"
            onClick={() => setMode("login")}
            className={[
              "flex-1 rounded-md px-3 py-2 text-sm",
              !isRegister ? "bg-white/10" : "text-gray-300 hover:bg-white/5",
            ].join(" ")}
          >
            Login
          </button>
          <button
            type="button"
            onClick={() => setMode("register")}
            className={[
              "flex-1 rounded-md px-3 py-2 text-sm",
              isRegister ? "bg-white/10" : "text-gray-300 hover:bg-white/5",
            ].join(" ")}
          >
            Register
          </button>
        </div>

        <form onSubmit={onSubmit} className="mt-6 space-y-4 rounded-xl bg-white/5 p-6">
          {isRegister ? (
            <label className="block">
              <span className="text-xs text-gray-300">Display name</span>
              <input
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="mt-1 w-full rounded-lg bg-black/40 px-3 py-2 text-sm outline-none ring-1 ring-white/10 focus:ring-2 focus:ring-indigo-400"
                placeholder="Sử Quan Tập Sự"
                required
              />
            </label>
          ) : null}

          <label className="block">
            <span className="text-xs text-gray-300">Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-lg bg-black/40 px-3 py-2 text-sm outline-none ring-1 ring-white/10 focus:ring-2 focus:ring-indigo-400"
              placeholder="you@example.com"
              required
            />
          </label>

          <label className="block">
            <span className="text-xs text-gray-300">Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-lg bg-black/40 px-3 py-2 text-sm outline-none ring-1 ring-white/10 focus:ring-2 focus:ring-indigo-400"
              placeholder="••••••••"
              minLength={isRegister ? 8 : 1}
              required
            />
            {isRegister ? <p className="mt-2 text-xs text-gray-400">Minimum 8 characters.</p> : null}
          </label>

          {error ? <div className="rounded-lg bg-red-500/15 px-3 py-2 text-sm text-red-200">{error}</div> : null}

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-lg bg-indigo-500 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-400 disabled:opacity-60"
          >
            {loading ? "Please wait…" : submitLabel}
          </button>
        </form>
      </div>
    </div>
  );
}
```

### `frontend/src/components/UserProfile.js` (Dashboard)

Shows:

- Rank (e.g. **Sử Quan**)
- Collection Grid (unlocked vs locked)
- Quest progress bar (Royal Gardens / category `thao_moc`)

```jsx
"use client";

import { useEffect, useMemo, useState } from "react";

import { getMyCollection } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

function ProgressBar({ value }) {
  const clamped = Math.max(0, Math.min(100, value || 0));
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
      <div className="h-full bg-emerald-500" style={{ width: `${clamped}%` }} />
    </div>
  );
}

export default function UserProfile() {
  const token = useAuthStore((s) => s.accessToken);
  const user = useAuthStore((s) => s.user);
  const stats = useAuthStore((s) => s.stats);
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const logout = useAuthStore((s) => s.logout);

  const [collection, setCollection] = useState(null);
  const [loadingCollection, setLoadingCollection] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (token) fetchMe();
  }, [token, fetchMe]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (!token) return;
      setLoadingCollection(true);
      setError(null);
      try {
        const res = await getMyCollection({ token });
        if (!cancelled) setCollection(res);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      } finally {
        if (!cancelled) setLoadingCollection(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [token]);

  const gridItems = useMemo(() => collection?.items || [], [collection]);
  const quest = collection?.stats?.quest;
  const unlockedCount = useMemo(() => {
    const s = collection?.stats;
    if (!s) return 0;
    return (s.discovered || 0) + (s.learned || 0) + (s.mastered || 0);
  }, [collection]);

  if (!token) return null;

  return (
    <div className="mx-auto max-w-5xl p-6">
      <div className="flex flex-col gap-6">
        <div className="rounded-xl border bg-white p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">Welcome, {user?.display_name || "Explorer"}</h1>
              <p className="mt-1 text-sm text-gray-600">{user?.email}</p>
            </div>
            <button onClick={logout} className="rounded-lg border px-3 py-2 text-sm text-gray-700 hover:bg-gray-50">
              Logout
            </button>
          </div>

          <div className="mt-5 grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg bg-gray-50 p-4">
              <div className="text-xs text-gray-500">Rank</div>
              <div className="mt-1 text-lg font-semibold text-gray-900">{stats?.rank?.name || "—"}</div>
              <div className="mt-2 text-xs text-gray-600">
                XP: {stats?.total_xp ?? 0} · To next: {stats?.xp_to_next_rank ?? 0}
              </div>
            </div>

            <div className="rounded-lg bg-gray-50 p-4">
              <div className="text-xs text-gray-500">Quest</div>
              <div className="mt-1 text-sm font-medium text-gray-900">{quest?.quest_name || "—"}</div>
              <div className="mt-3">
                <ProgressBar value={quest?.progress_percent || 0} />
              </div>
              <div className="mt-2 text-xs text-gray-600">
                {quest?.discovered ?? 0}/{quest?.total ?? 0} discovered · {Math.round(quest?.progress_percent || 0)}%
              </div>
            </div>

            <div className="rounded-lg bg-gray-50 p-4">
              <div className="text-xs text-gray-500">Collection</div>
              <div className="mt-1 text-lg font-semibold text-gray-900">{unlockedCount}</div>
              <div className="mt-2 text-xs text-gray-600">Unlocked (total: {collection?.stats?.total ?? 0})</div>
            </div>
          </div>

          {error ? <div className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</div> : null}
        </div>

        <div className="rounded-xl border bg-white p-6">
          <div className="flex items-baseline justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Collection Grid</h2>
            {loadingCollection ? <span className="text-xs text-gray-500">Loading…</span> : null}
          </div>

          <div className="mt-4 grid grid-cols-4 gap-3 sm:grid-cols-6 md:grid-cols-8">
            {gridItems.map((item) => {
              const unlocked = item.status !== "hidden";
              return (
                <div
                  key={item.motif_id}
                  title={`${item.name} (${item.status})`}
                  className={[
                    "group relative aspect-square overflow-hidden rounded-lg border",
                    unlocked ? "bg-white" : "bg-gray-100",
                  ].join(" ")}
                >
                  {item.thumbnail_url ? (
                    <img
                      src={item.thumbnail_url}
                      alt={item.name}
                      className={["h-full w-full object-cover", unlocked ? "" : "opacity-30 grayscale"].join(" ")}
                    />
                  ) : (
                    <div
                      className={[
                        "flex h-full w-full items-center justify-center text-xs font-medium",
                        unlocked ? "text-gray-800" : "text-gray-400",
                      ].join(" ")}
                    >
                      {unlocked ? "✓" : "?"}
                    </div>
                  )}

                  <div className="pointer-events-none absolute inset-x-0 bottom-0 bg-black/60 px-2 py-1 text-[10px] text-white opacity-0 transition group-hover:opacity-100">
                    <div className="truncate">{item.name}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## 3D Viewer Integration (Required change)

Since `/progress/unlock` is now protected, update the “click-to-learn” unlock call:

```js
import { unlockProgress } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";

const token = useAuthStore.getState().accessToken;
await unlockProgress({
  token,
  motifId: motif.id,
  meshName,
  tapPosition: { x: e.point.x, y: e.point.y, z: e.point.z },
});
```

No more `user_id` in the request body.
