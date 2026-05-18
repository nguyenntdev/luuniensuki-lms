"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useFriendsStore } from "@/stores/friendsStore";
import { useAuthStore } from "@/stores/authStore";
import { searchUsers, sendPeerFeedback } from "@/lib/api";
import FriendCard from "@/components/social/FriendCard";
import FriendRequestCard from "@/components/social/FriendRequestCard";

const FEEDBACK_TEMPLATE_LABELS = {
  great_progress: "Tiến bộ tốt",
  keep_going: "Cố lên",
  impressive_streak: "Chuỗi học chất",
  quiz_champion: "Quiz giỏi",
};

export default function FriendsPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const {
    friends,
    requests,
    loading,
    error,
    fetchFriends,
    fetchRequests,
    acceptRequest,
    rejectRequest,
    removeFriend,
  } = useFriendsStore();

  const [activeTab, setActiveTab] = useState("friends");
  const [showRemoveDialog, setShowRemoveDialog] = useState(false);
  const [friendToRemove, setFriendToRemove] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [feedbackNotice, setFeedbackNotice] = useState(null);
  const [sendingFeedbackKey, setSendingFeedbackKey] = useState(null);

  useEffect(() => {
    if (user) {
      fetchFriends();
      fetchRequests();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  const handleAcceptRequest = async (request) => {
    try {
      await acceptRequest(request.id);
    } catch (err) {
      console.error("Failed to accept request:", err);
    }
  };

  const handleRejectRequest = async (request) => {
    try {
      await rejectRequest(request.id);
    } catch (err) {
      console.error("Failed to reject request:", err);
    }
  };

  const handleRemoveFriend = (friend) => {
    setFriendToRemove(friend);
    setShowRemoveDialog(true);
  };

  const confirmRemoveFriend = async () => {
    if (friendToRemove) {
      try {
        await removeFriend(friendToRemove.user_id);
        setShowRemoveDialog(false);
        setFriendToRemove(null);
      } catch (err) {
        console.error("Failed to remove friend:", err);
      }
    }
  };

  const handleViewProfile = (friend) => {
    router.push(`/u/${friend.user_id}`);
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const data = await searchUsers(searchQuery);
      setSearchResults(data.users || []);
    } catch (err) {
      console.error("Failed to search users:", err);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleSendRequest = async (userId) => {
    try {
      const { sendRequest } = useFriendsStore.getState();
      await sendRequest(userId);
      setSearchResults((prev) =>
        prev.map((u) =>
          u.id === userId ? { ...u, request_sent: true } : u
        )
      );
    } catch (err) {
      console.error("Failed to send request:", err);
    }
  };

  const handleSendPeerFeedback = async (friend, templateKey) => {
    const key = `${friend.user_id}:${templateKey}`;
    setSendingFeedbackKey(key);
    setFeedbackNotice(null);
    try {
      await sendPeerFeedback({
        toUserId: friend.user_id,
        templateKey,
      });
      const templateLabel = FEEDBACK_TEMPLATE_LABELS[templateKey] || "Peer feedback";
      setFeedbackNotice(
        `Đã gửi "${templateLabel}" cho ${friend.display_name || "bạn của bạn"}.`,
      );
    } catch (err) {
      setFeedbackNotice(
        err instanceof Error ? err.message : "Không gửi được peer feedback.",
      );
    } finally {
      setSendingFeedbackKey(null);
    }
  };

  const pendingCount = requests.filter((r) => r.status === "pending").length;

  return (
    <main className="site-shell">
      <div className="heritage-hero p-5 md:p-6">
        {/* Header */}
        <div className="relative">
          <h1 className="text-3xl font-bold text-foreground">Bạn học</h1>
          <p className="mt-2 text-muted-foreground">
            Kết nối người học cùng nhịp. Xem lời mời, tìm bạn mới, gửi động viên nhanh.
          </p>
        </div>
      </div>

        {/* Tabs */}
        <div className="my-5 rounded-lg border border-border bg-card p-2">
          <nav className="grid grid-cols-3 gap-2">
            <button
              onClick={() => setActiveTab("friends")}
              className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium transition-colors ${
                activeTab === "friends"
                  ? "border-primary bg-background text-primary"
                  : "border-transparent text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              Bạn bè ({friends.length})
            </button>
            <button
              onClick={() => setActiveTab("requests")}
              className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium transition-colors relative ${
                activeTab === "requests"
                  ? "border-primary bg-background text-primary"
                  : "border-transparent text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              Lời mời
              {pendingCount > 0 && (
                <span className="ml-2 inline-flex items-center justify-center rounded-full bg-red-500 px-2 py-0.5 text-xs font-bold text-white">
                  {pendingCount}
                </span>
              )}
            </button>
            <button
              onClick={() => setActiveTab("search")}
              className={`whitespace-nowrap border-b-2 px-1 py-4 text-sm font-medium transition-colors ${
                activeTab === "search"
                  ? "border-primary bg-background text-primary"
                  : "border-transparent text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              Tìm kiếm
            </button>
          </nav>
        </div>

        {/* Content */}
        <div className="heritage-surface p-4">
          <div className="relative">
          {loading && (
            <div className="flex justify-center py-12">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
            </div>
          )}

          {error && (
            <div className="rounded-lg border border-red-500/50 bg-red-500/10 p-4 text-red-600 dark:text-red-400">
              {error}
            </div>
          )}

          {feedbackNotice && (
            <div className="rounded-lg border border-primary/40 bg-primary/10 p-4 text-sm text-primary">
              {feedbackNotice}
            </div>
          )}

          {!loading && activeTab === "friends" && (
            <div className="space-y-4">
              {friends.length === 0 ? (
                <div className="rounded-lg border border-dashed border-border bg-muted/50 p-12 text-center">
                  <div className="mx-auto h-16 w-16 rounded-full bg-muted flex items-center justify-center mb-4">
                    <svg
                      className="h-8 w-8 text-muted-foreground"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth="1.5"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    Chưa có bạn học
                  </h3>
                  <p className="text-sm text-muted-foreground mb-4">
                    Tìm một người học cùng để giữ nhịp ôn tập.
                  </p>
                  <button
                    onClick={() => setActiveTab("search")}
                    className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
                  >
                    Tìm bạn học
                  </button>
                </div>
              ) : (
                friends.map((friend) => (
                  <FriendCard
                    key={friend.user_id}
                    friend={friend}
                    onRemove={handleRemoveFriend}
                    onViewProfile={handleViewProfile}
                    onSendFeedback={handleSendPeerFeedback}
                    sendingFeedbackKey={sendingFeedbackKey}
                  />
                ))
              )}
            </div>
          )}

          {!loading && activeTab === "requests" && (
            <div className="space-y-4">
              {requests.length === 0 ? (
                <div className="rounded-lg border border-dashed border-border bg-muted/50 p-12 text-center">
                  <div className="mx-auto h-16 w-16 rounded-full bg-muted flex items-center justify-center mb-4">
                    <svg
                      className="h-8 w-8 text-muted-foreground"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth="1.5"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"
                      />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    Chưa có lời mời
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Khi có lời mời mới, bạn sẽ thấy ở đây.
                  </p>
                </div>
              ) : (
                requests
                  .filter((r) => r.status === "pending")
                  .map((request) => (
                    <FriendRequestCard
                      key={request.id}
                      request={request}
                      onAccept={handleAcceptRequest}
                      onReject={handleRejectRequest}
                    />
                  ))
              )}
            </div>
          )}

          {!loading && activeTab === "search" && (
            <div className="space-y-4">
              <form onSubmit={handleSearch} className="mb-6">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Tìm theo tên hoặc email..."
                    className="flex-1 rounded-md border border-border bg-background px-4 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20"
                  />
                  <button
                    type="submit"
                    disabled={searching}
                    className="rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {searching ? "Đang tìm..." : "Tìm"}
                  </button>
                </div>
              </form>

              {searching && (
                <div className="flex justify-center py-12">
                  <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                </div>
              )}

              {!searching && searchResults.length === 0 && searchQuery && (
                <div className="rounded-lg border border-dashed border-border bg-muted/50 p-12 text-center">
                  <div className="mx-auto h-16 w-16 rounded-full bg-muted flex items-center justify-center mb-4">
                    <svg
                      className="h-8 w-8 text-muted-foreground"
                      fill="none"
                      viewBox="0 0 24 24"
                      strokeWidth="1.5"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"
                      />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    Không tìm thấy
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Thử tên hoặc email khác.
                  </p>
                </div>
              )}

              {!searching && searchResults.length > 0 && (
                <div className="space-y-3">
                  {searchResults.map((user) => (
                    <div
                      key={user.id}
                      className="rounded-lg border border-border bg-card p-4 shadow-sm"
                    >
                      <div className="flex items-center gap-4">
                        <div className="h-12 w-12 overflow-hidden rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-white font-bold text-lg border-2 border-white/20">
                          {user.avatar_url ? (
                            <img
                              src={user.avatar_url}
                              alt={user.display_name}
                              className="h-full w-full object-cover"
                            />
                          ) : (
                            (user.display_name || "?")[0].toUpperCase()
                          )}
                        </div>

                        <div className="flex-1">
                          <h3 className="font-semibold text-foreground">
                            {user.display_name}
                          </h3>
                          {user.bio && (
                            <p className="text-sm text-muted-foreground line-clamp-1">
                              {user.bio}
                            </p>
                          )}
                          <div className="mt-1 flex items-center gap-2">
                            <div className="flex items-center gap-1 rounded-full bg-amber-500/20 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400">
                              <span>XP</span>
                              <span>{user.total_xp || 0} XP</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          {user.is_friend ? (
                            <span className="rounded-md bg-green-500/20 px-3 py-1.5 text-sm font-medium text-green-600 dark:text-green-400">
                              Bạn học
                            </span>
                          ) : user.request_sent ? (
                            <span className="rounded-md bg-muted px-3 py-1.5 text-sm font-medium text-muted-foreground">
                              Đã gửi lời mời
                            </span>
                          ) : (
                            <button
                              onClick={() => handleSendRequest(user.id)}
                              className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
                            >
                              Kết bạn
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          </div>
        </div>

        {/* Remove Friend Dialog */}
        {showRemoveDialog && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="mx-4 w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-lg">
              <h3 className="text-lg font-semibold text-foreground mb-2">
                Xóa bạn học?
              </h3>
              <p className="text-sm text-muted-foreground mb-6">
                Bạn muốn xóa{" "}
                <span className="font-medium text-foreground">
                  {friendToRemove?.display_name}
                </span>{" "}
                khỏi danh sách bạn học?
              </p>
              <div className="flex justify-end gap-3">
                <button
                  onClick={() => {
                    setShowRemoveDialog(false);
                    setFriendToRemove(null);
                  }}
                  className="rounded-md border border-border bg-background px-4 py-2 text-sm font-medium text-foreground hover:bg-muted transition-colors"
                >
                  Hủy
                </button>
                <button
                  onClick={confirmRemoveFriend}
                  className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 transition-colors"
                >
                  Xóa
                </button>
              </div>
            </div>
          </div>
        )}
    </main>
  );
}
