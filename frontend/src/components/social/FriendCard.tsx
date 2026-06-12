"use client";

interface FeedbackTemplate {
  key: string;
  label: string;
}

const FEEDBACK_TEMPLATES: FeedbackTemplate[] = [
  { key: "great_progress", label: "Tiến bộ tốt" },
  { key: "keep_going", label: "Cố lên" },
  { key: "impressive_streak", label: "Giữ nhịp tốt" },
  { key: "quiz_champion", label: "Làm quiz tốt" },
];

export interface Friend {
  user_id: string | number;
  display_name: string;
  avatar_url?: string | null;
  total_xp?: number;
  bio?: string | null;
  is_online?: boolean;
  streak?: number;
}

interface FriendCardProps {
  friend: Friend;
  onRemove?: (friend: Friend) => void;
  onViewProfile?: (friend: Friend) => void;
  onSendFeedback?: (friend: Friend, templateKey: string) => void;
  sendingFeedbackKey?: string | null;
}

export default function FriendCard({
  friend,
  onRemove,
  onViewProfile,
  onSendFeedback,
  sendingFeedbackKey,
}: FriendCardProps) {
  const { user_id, display_name, avatar_url, total_xp, bio, is_online, streak } = friend;

  const getInitial = (name?: string | null) => {
    return name && name.length > 0 ? name[0].toUpperCase() : "?";
  };

  const handleRemove = () => {
    if (onRemove) {
      onRemove(friend);
    }
  };

  const handleViewProfile = () => {
    if (onViewProfile) {
      onViewProfile(friend);
    }
  };

  const handleSendFeedback = (templateKey: string) => {
    if (onSendFeedback) {
      onSendFeedback(friend, templateKey);
    }
  };

  return (
    <div className="rounded-lg border border-border bg-card p-4 shadow-sm transition-all hover:shadow-md">
      <div className="flex items-center gap-4">
        {/* Avatar */}
        <div className="relative">
          <div className="h-14 w-14 overflow-hidden rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-white font-bold text-xl border-2 border-white/20">
            {avatar_url ? (
              <img
                src={avatar_url}
                alt={display_name}
                className="h-full w-full object-cover"
              />
            ) : (
              getInitial(display_name)
            )}
          </div>
          {is_online && (
            <div className="absolute bottom-0 right-0 h-4 w-4 rounded-full border-2 border-card bg-green-500" />
          )}
        </div>

        {/* Friend Info */}
        <div className="flex-1">
          <h3 className="font-semibold text-foreground">{display_name}</h3>
          {bio && (
            <p className="text-sm text-muted-foreground line-clamp-1">{bio}</p>
          )}
          <div className="mt-1 flex items-center gap-2">
            <div className="flex items-center gap-1 rounded-full bg-amber-500/20 px-2 py-0.5 text-xs font-medium text-amber-600 dark:text-amber-400">
              <span>XP</span>
              <span>{total_xp || 0} XP</span>
            </div>
            {streak && streak > 0 && (
              <div className="flex items-center gap-1 rounded-full bg-orange-500/20 px-2 py-0.5 text-xs font-medium text-orange-600 dark:text-orange-400">
                <span>Nhịp</span>
                <span>{streak} ngày</span>
              </div>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {onViewProfile && (
            <button
              onClick={handleViewProfile}
              className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
            >
              Xem hồ sơ
            </button>
          )}
          {onRemove && (
            <button
              onClick={handleRemove}
              className="rounded-md border border-border bg-background px-3 py-1.5 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
              title="Xóa bạn học"
            >
              <svg
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="1.5"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          )}
        </div>
      </div>

      {onSendFeedback && (
        <div className="mt-3 border-t border-border pt-3">
          <p className="mb-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            Gửi động viên
          </p>
          <div className="flex flex-wrap gap-2">
            {FEEDBACK_TEMPLATES.map((template) => {
              const key = `${user_id}:${template.key}`;
              const isSending = sendingFeedbackKey === key;
              return (
                <button
                  key={template.key}
                  type="button"
                  onClick={() => handleSendFeedback(template.key)}
                  disabled={isSending}
                  className="rounded-full border border-border bg-background px-2.5 py-1 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground disabled:opacity-60"
                >
                  {isSending ? "Đang gửi..." : template.label}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
