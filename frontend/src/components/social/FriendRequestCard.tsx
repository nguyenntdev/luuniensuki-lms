"use client";

export interface FriendRequest {
  id: string | number;
  from_user_id: string | number;
  from_user_display_name: string;
  from_user_avatar_url?: string | null;
  created_at?: string | null;
}

interface FriendRequestCardProps {
  request: FriendRequest;
  onAccept?: (request: FriendRequest) => void;
  onReject?: (request: FriendRequest) => void;
}

export default function FriendRequestCard({ request, onAccept, onReject }: FriendRequestCardProps) {
  const {
    id,
    from_user_id,
    from_user_display_name,
    from_user_avatar_url,
    created_at,
  } = request;

  const getInitial = (name?: string | null) => {
    return name && name.length > 0 ? name[0].toUpperCase() : "?";
  };

  const getTimeAgo = () => {
    if (!created_at) return "";

    const now = new Date();
    const createdDate = new Date(created_at);
    const diffMs = now.getTime() - createdDate.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffDays > 0) return `${diffDays} ngày trước`;
    if (diffHours > 0) return `${diffHours} giờ trước`;
    if (diffMins > 0) return `${diffMins} phút trước`;
    return "Vừa xong";
  };

  const handleAccept = () => {
    if (onAccept) {
      onAccept(request);
    }
  };

  const handleReject = () => {
    if (onReject) {
      onReject(request);
    }
  };

  return (
    <div className="rounded-lg border border-border bg-card p-4 shadow-sm">
      <div className="flex items-center gap-4">
        {/* Avatar */}
        <div className="h-12 w-12 overflow-hidden rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-white font-bold text-lg border-2 border-white/20">
          {from_user_avatar_url ? (
            <img
              src={from_user_avatar_url}
              alt={from_user_display_name}
              className="h-full w-full object-cover"
            />
          ) : (
            getInitial(from_user_display_name)
          )}
        </div>

        {/* User Info */}
        <div className="flex-1">
          <h3 className="font-semibold text-foreground">
            {from_user_display_name}
          </h3>
          <p className="text-sm text-muted-foreground">{getTimeAgo()}</p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {onAccept && (
            <button
              onClick={handleAccept}
              className="rounded-full p-2 bg-green-500/20 text-green-600 dark:text-green-400 hover:bg-green-500/30 transition-colors border border-green-500/30"
              title="Chấp nhận"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="2"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M4.5 12.75l6 6 9-13.5"
                />
              </svg>
            </button>
          )}
          {onReject && (
            <button
              onClick={handleReject}
              className="rounded-full p-2 bg-red-500/20 text-red-600 dark:text-red-400 hover:bg-red-500/30 transition-colors border border-red-500/30"
              title="Từ chối"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth="2"
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
    </div>
  );
}
