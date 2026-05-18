'use client'
import { Target, CheckCircle2 } from 'lucide-react'

export default function DailyGoalProgress({ goal = null, progress = 0 }) {
  const defaultGoal = {
    target: 50,
    current: progress,
    description: 'Hoàn thành mục tiêu XP hàng ngày'
  }
  
  const goalData = goal || defaultGoal
  const { target = 50, current = 0, description = 'Mục tiêu hàng ngày' } = goalData
  const progressPercent = Math.min(100, Math.max(0, (current / target) * 100))
  const isCompleted = current >= target
  
  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${isCompleted ? 'bg-success/10' : 'bg-primary/10'}`}>
            {isCompleted ? (
              <CheckCircle2 className="w-5 h-5 text-success" />
            ) : (
              <Target className="w-5 h-5 text-primary" />
            )}
          </div>
          <div>
            <h3 className="text-lg font-display font-semibold text-foreground">
              Mục tiêu hôm nay
            </h3>
            <p className="text-xs text-muted-foreground mt-0.5">{description}</p>
          </div>
        </div>
      </div>
      
      <div className="space-y-3">
        <div className="flex items-end justify-between">
          <div>
            <p className="text-3xl font-display font-bold text-foreground">
              {current}
              <span className="text-lg text-muted-foreground font-normal ml-1">
                / {target}
              </span>
            </p>
            <p className="text-xs text-muted-foreground mt-1">XP đã đạt được</p>
          </div>
          <div className="text-right">
            <p className={`text-2xl font-bold ${isCompleted ? 'text-success' : 'text-primary'}`}>
              {Math.round(progressPercent)}%
            </p>
          </div>
        </div>
        
        <div className="h-3 w-full overflow-hidden rounded-full bg-secondary/50">
          <div
            className={`h-full transition-all duration-700 ease-out ${
              isCompleted 
                ? 'bg-gradient-to-r from-success to-emerald-400 shadow-[0_0_10px_rgba(var(--success),0.5)]' 
                : 'bg-gradient-to-r from-primary to-amber-400 shadow-[0_0_10px_rgba(var(--primary),0.5)]'
            }`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        
        {isCompleted ? (
          <div className="mt-4 rounded-lg bg-success/10 border border-success/20 p-3">
            <p className="text-sm text-success font-medium text-center">
              🎉 Chúc mừng! Bạn đã hoàn thành mục tiêu hôm nay!
            </p>
          </div>
        ) : (
          <p className="text-xs text-muted-foreground text-center mt-2">
            Còn {target - current} XP nữa để đạt mục tiêu
          </p>
        )}
      </div>
    </div>
  )
}

