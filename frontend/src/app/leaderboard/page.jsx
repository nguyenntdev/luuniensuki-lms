"use client";

import { useEffect, useState } from "react";

import { getClasses, getEnrolledClassrooms, getLeaderboardData } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import Skeleton from "@/components/Skeleton";
import RankBadge from "@/components/leaderboard/RankBadge";
import UserRankCard from "@/components/leaderboard/UserRankCard";

const SCOPE_OPTIONS = [
  { value: "global", label: "Toàn hệ thống" },
  { value: "friends", label: "Bạn bè" },
  { value: "class", label: "Lớp học" },
];

const ORDER_OPTIONS = [
  { value: "xp", label: "Theo XP" },
  { value: "streak", label: "Theo streak" },
];

export default function LeaderboardPage() {
  const user = useAuthStore((state) => state.user);
  const currentUserId = user?.id;
  const isStaff = ["teacher", "admin", "super_admin"].includes(user?.role);

  const [scope, setScope] = useState("global");
  const [orderBy, setOrderBy] = useState("xp");
  const [classes, setClasses] = useState([]);
  const [selectedClassId, setSelectedClassId] = useState("");
  const [entries, setEntries] = useState([]);
  const [userEntry, setUserEntry] = useState(null);
  const [userRank, setUserRank] = useState(null);
  const [totalUsers, setTotalUsers] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function loadClasses() {
      try {
        const classRows = isStaff
          ? await getClasses()
          : await getEnrolledClassrooms();
        if (cancelled) return;
        const normalized = Array.isArray(classRows) ? classRows : [];
        setClasses(normalized);

        if (!selectedClassId && normalized.length) {
          setSelectedClassId(normalized[0].id);
        }
      } catch {
        if (!cancelled) setClasses([]);
      }
    }

    loadClasses();
    return () => {
      cancelled = true;
    };
  }, [isStaff, selectedClassId]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      if (scope === "class" && !selectedClassId) {
        setEntries([]);
        setUserEntry(null);
        setUserRank(null);
        setTotalUsers(0);
        setLoading(false);
        setError(null);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const res = await getLeaderboardData({
          limit: 50,
          scope,
          orderBy,
          classroomId: selectedClassId || undefined,
        });
        if (cancelled) return;

        const normalizedEntries = Array.isArray(res?.entries) ? res.entries : [];
        const currentUserEntry =
          (res?.user_entry && typeof res.user_entry === "object"
            ? res.user_entry
            : null) ||
          (currentUserId
            ? normalizedEntries.find((entry) => entry.user_id === currentUserId) || null
            : null);

        setEntries(normalizedEntries);
        setUserEntry(currentUserEntry);
        setUserRank(typeof res?.user_rank === "number" ? res.user_rank : null);
        setTotalUsers(
          typeof res?.total_users === "number" ? res.total_users : normalizedEntries.length,
        );
      } catch (err) {
        if (!cancelled) {
          setEntries([]);
          setUserEntry(null);
          setUserRank(null);
          setTotalUsers(0);
          setError(err instanceof Error ? err.message : String(err));
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [scope, orderBy, selectedClassId, currentUserId]);

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-display font-semibold text-foreground">Bảng Xếp Hạng</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Cạnh tranh lành mạnh theo XP và streak.
          </p>
        </div>
        <div className="text-right text-xs text-muted-foreground">
          <p>Tổng người tham gia: {totalUsers}</p>
          {userRank ? <p>Hạng của bạn: #{userRank}</p> : null}
        </div>
      </div>

      {error ? <div className="mt-6 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</div> : null}

      <div className="mt-6 grid gap-3 rounded-2xl border border-border bg-card p-4 md:grid-cols-[1fr_auto_auto]">
        <div className="flex flex-wrap gap-2">
          {SCOPE_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setScope(option.value)}
              className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                scope === option.value
                  ? "border-primary bg-primary/10 text-primary"
                  : "border-border text-muted-foreground hover:text-foreground"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>

        <select
          value={orderBy}
          onChange={(event) => setOrderBy(event.target.value)}
          className="rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground"
        >
          {ORDER_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        {scope === "class" ? (
          <select
            value={selectedClassId}
            onChange={(event) => setSelectedClassId(event.target.value)}
            className="rounded-lg border border-border bg-background px-3 py-2 text-xs text-foreground"
          >
            {!classes.length ? <option value="">Chưa có lớp học</option> : null}
            {classes.map((classroom) => (
              <option key={classroom.id} value={classroom.id}>
                {classroom.name}
              </option>
            ))}
          </select>
        ) : (
          <div />
        )}
      </div>

      {!loading && userEntry && <UserRankCard userEntry={userEntry} />}

      <div className="mt-8 overflow-hidden rounded-2xl border border-border bg-card">
        <table className="w-full text-left text-sm">
          <thead className="bg-muted text-xs text-muted-foreground">
            <tr>
              <th className="px-4 py-3">Hạng</th>
              <th className="px-4 py-3">Nhà Khám Phá</th>
              <th className="px-4 py-3">Danh Hiệu</th>
              <th className="px-4 py-3 text-right">XP</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [...Array(10)].map((_, i) => (
                <tr key={i} className="border-t border-border">
                  <td className="px-4 py-3">
                    <Skeleton className="h-4 w-6" />
                  </td>
                  <td className="px-4 py-3">
                    <Skeleton className="h-4 w-32" />
                  </td>
                  <td className="px-4 py-3">
                    <Skeleton className="h-4 w-24" />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Skeleton className="ml-auto h-4 w-12" />
                  </td>
                </tr>
              ))
            ) : (
              <>
                {entries.map((e) => {
                  const isCurrentUser = currentUserId && e.user_id === currentUserId;
                  return (
                    <tr
                      key={e.user_id}
                      className={`border-t border-border transition-colors ${
                        isCurrentUser
                          ? "bg-primary/10 font-medium"
                          : "hover:bg-muted/50"
                      }`}
                    >
                      <td className="px-4 py-3">
                        <RankBadge rank={e.rank} />
                      </td>
                      <td className="px-4 py-3 font-medium text-foreground">
                        {e.display_name}
                        {isCurrentUser && (
                          <span className="ml-2 text-xs font-semibold text-primary">(Bạn)</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">{e.title}</td>
                      <td className="px-4 py-3 text-right font-display tabular-nums font-semibold text-primary">
                        {e.total_xp}
                      </td>
                    </tr>
                  );
                })}
                {entries.length === 0 ? (
                  <tr>
                    <td className="px-4 py-6 text-center text-sm text-muted-foreground" colSpan={4}>
                      Chưa có dữ liệu.
                    </td>
                  </tr>
                ) : null}
              </>
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}
