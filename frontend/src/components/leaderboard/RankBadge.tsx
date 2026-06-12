interface RankBadgeProps {
  rank: number;
}

export default function RankBadge({ rank }: RankBadgeProps) {
  if (rank === 1) {
    return (
      <div className="w-8 h-8 rounded-full bg-yellow-500 flex items-center justify-center shadow-md">
        🥇
      </div>
    );
  }
  
  if (rank === 2) {
    return (
      <div className="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center shadow-md">
        🥈
      </div>
    );
  }
  
  if (rank === 3) {
    return (
      <div className="w-8 h-8 rounded-full bg-amber-600 flex items-center justify-center shadow-md">
        🥉
      </div>
    );
  }
  
  return (
    <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-xs font-bold text-muted-foreground">
      {rank}
    </div>
  );
}

