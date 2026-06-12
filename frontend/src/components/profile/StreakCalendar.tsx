'use client'
import { Check, Flame } from 'lucide-react'

interface Streak {
  current_streak?: number
  last_active_at?: string | null
}

interface StreakCalendarProps {
  streak?: Streak | null
  loading?: boolean
}

interface StreakDay {
  dayName: string
  date: number
  isCompleted: boolean
  isToday: boolean
  dateObj: Date
}

export default function StreakCalendar({ streak = {}, loading = false }: StreakCalendarProps) {
  const { current_streak = 0, last_active_at = null } = streak || {}

  const days = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']
  const today = new Date()

  const getStreakDays = (): StreakDay[] => {
    const streakDays: StreakDay[] = []
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today)
      date.setDate(date.getDate() - i)

      const isCompleted = current_streak > 0 && i < current_streak
      const isToday = i === 0

      streakDays.push({
        dayName: days[date.getDay()],
        date: date.getDate(),
        isCompleted,
        isToday,
        dateObj: date
      })
    }
    return streakDays
  }

  // Show loading skeleton
  if (loading) {
    return (
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm animate-pulse">
        <div className="flex items-center justify-between mb-6">
          <div className="h-6 w-32 bg-muted rounded" />
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-muted rounded" />
            <div className="h-8 w-8 bg-muted rounded" />
          </div>
        </div>
        <div className="grid grid-cols-7 gap-2">
          {Array.from({ length: 7 }).map((_, i) => (
            <div key={i} className="flex flex-col items-center gap-2">
              <div className="h-3 w-6 bg-muted rounded" />
              <div className="w-10 h-10 rounded-full bg-muted" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  const streakDays = getStreakDays()

  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-display font-semibold text-foreground">Chuỗi học tập</h3>
        <div className="flex items-center gap-2">
          <Flame className="w-5 h-5 text-orange-500" />
          <span className="text-2xl font-display font-bold text-primary">{current_streak}</span>
        </div>
      </div>
      
      <div className="grid grid-cols-7 gap-2">
        {streakDays.map((day, i) => (
          <div key={i} className="flex flex-col items-center gap-2">
            <p className="text-xs text-muted-foreground font-medium">{day.dayName}</p>
            <div className={`
              w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300
              ${day.isCompleted
                ? 'bg-primary text-primary-foreground shadow-[0_0_12px_rgba(var(--primary),0.4)]'
                : 'bg-transparent border border-border/40'
              }
              ${day.isToday ? 'ring-2 ring-primary ring-offset-2 ring-offset-background' : ''}
            `}>
              {day.isCompleted ? (
                <Check className="w-5 h-5" />
              ) : (
                <span className="text-xs text-muted-foreground font-medium">{day.date}</span>
              )}
            </div>
          </div>
        ))}
      </div>
      
      {last_active_at && (
        <p className="mt-4 text-xs text-muted-foreground text-center">
          Hoạt động gần nhất: {new Date(last_active_at).toLocaleDateString('vi-VN')}
        </p>
      )}
    </div>
  )
}

