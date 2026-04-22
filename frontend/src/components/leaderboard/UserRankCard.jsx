import RankBadge from "./RankBadge";

export default function UserRankCard({ userEntry }) {
  if (!userEntry) return null;

  return (
    <div className="mb-6 overflow-hidden rounded-2xl border-2 border-primary bg-gradient-to-r from-primary/10 to-primary/5 p-4 shadow-lg">
      <div className="flex items-center gap-4">
        <RankBadge rank={userEntry.rank} />
        
        <div className="flex-1">
          <p className="text-xs font-medium text-muted-foreground">Hạng của bạn</p>
          <p className="text-lg font-bold text-foreground">{userEntry.display_name}</p>
          <p className="text-sm text-muted-foreground">{userEntry.title || "Nhà khám phá"}</p>
        </div>
        
        <div className="text-right">
          <p className="text-xs font-medium text-muted-foreground">XP</p>
          <p className="text-2xl font-display font-bold text-primary">{userEntry.total_xp}</p>
        </div>
      </div>
    </div>
  );
}

