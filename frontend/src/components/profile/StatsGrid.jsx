'use client'
import { BookOpen, Brain, Trophy, Star } from 'lucide-react'

export default function StatsGrid({ stats = {}, collection = {} }) {
  const collectionStats = collection?.stats || {}
  
  const gridStats = [
    {
      icon: BookOpen,
      label: 'Đã khám phá',
      value: collectionStats.discovered || 0,
      total: collectionStats.total || 0,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10'
    },
    {
      icon: Brain,
      label: 'Đã học',
      value: collectionStats.learned || 0,
      total: collectionStats.total || 0,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10'
    },
    {
      icon: Star,
      label: 'Thành thạo',
      value: collectionStats.mastered || 0,
      total: collectionStats.total || 0,
      color: 'text-amber-500',
      bgColor: 'bg-amber-500/10'
    },
    {
      icon: Trophy,
      label: 'Tổng XP',
      value: stats.total_xp || 0,
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/10'
    }
  ]
  
  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <h3 className="text-lg font-display font-semibold text-foreground mb-4">
        Thống kê học tập
      </h3>
      
      <div className="grid grid-cols-2 gap-4">
        {gridStats.map(({ icon: Icon, label, value, total, color, bgColor }) => (
          <div 
            key={label} 
            className="relative overflow-hidden rounded-lg border border-border bg-secondary/30 p-4 hover:bg-secondary/50 transition-all duration-300"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <p className="text-xs text-muted-foreground font-medium mb-2">{label}</p>
                <p className="text-2xl font-display font-bold text-foreground">
                  {value.toLocaleString()}
                  {total > 0 && (
                    <span className="text-sm text-muted-foreground font-normal ml-1">
                      / {total}
                    </span>
                  )}
                </p>
                {total > 0 && (
                  <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                    <div
                      className={`h-full ${bgColor} ${color} transition-all duration-500`}
                      style={{ width: `${Math.min(100, (value / total) * 100)}%` }}
                    />
                  </div>
                )}
              </div>
              <div className={`p-2 rounded-lg ${bgColor}`}>
                <Icon className={`w-5 h-5 ${color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

