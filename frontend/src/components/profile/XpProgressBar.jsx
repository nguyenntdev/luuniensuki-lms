'use client'

export default function XpProgressBar({ stats = {} }) {
  const { total_xp = 0, rank = {}, xp_to_next_rank = 0, next_rank = null } = stats
  
  const currentRankXp = rank?.min_xp || 0
  const nextRankXp = next_rank?.min_xp || (currentRankXp + xp_to_next_rank)
  const progressInRank = total_xp - currentRankXp
  const xpNeededForRank = nextRankXp - currentRankXp
  const progressPercent = xpNeededForRank > 0 
    ? Math.min(100, Math.max(0, (progressInRank / xpNeededForRank) * 100)) 
    : 100
  
  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-lg font-display font-semibold text-foreground">
            {rank?.title || 'Học viên'}
          </h3>
          <p className="text-sm text-muted-foreground mt-1">
            Cấp độ hiện tại
          </p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-display font-bold text-primary">{total_xp}</p>
          <p className="text-xs text-muted-foreground">XP</p>
        </div>
      </div>
      
      <div className="space-y-2">
        <div className="h-3 w-full overflow-hidden rounded-full bg-secondary/50">
          <div
            className="h-full bg-gradient-to-r from-primary to-amber-400 transition-all duration-700 ease-out shadow-[0_0_10px_rgba(var(--primary),0.5)]"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">
            {progressInRank} / {xpNeededForRank} XP
          </span>
          <span className="font-medium text-foreground">
            {Math.round(progressPercent)}%
          </span>
        </div>
      </div>
      
      {next_rank && (
        <div className="mt-4 pt-4 border-t border-border">
          <p className="text-xs text-muted-foreground">
            Cần thêm <span className="font-bold text-primary">{xp_to_next_rank} XP</span> để đạt{' '}
            <span className="font-semibold text-foreground">{next_rank.title}</span>
          </p>
        </div>
      )}
    </div>
  )
}

