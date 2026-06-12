'use client'
import Link from 'next/link'
import { Trophy, Medal, Target, Gift, type LucideIcon } from 'lucide-react'

interface GamificationHubProps {
  badges?: number
  rank?: number | string | null
}

interface GamificationItem {
  icon: LucideIcon
  label: string
  href: string
  value: string | number
  color: string
}

export default function GamificationHub({ badges = 0, rank = null }: GamificationHubProps) {
  const items: GamificationItem[] = [
    { 
      icon: Trophy, 
      label: 'Bảng xếp hạng', 
      href: '/leaderboard', 
      value: rank ? `#${rank}` : '—',
      color: 'text-yellow-500'
    },
    { 
      icon: Medal, 
      label: 'Huy hiệu', 
      href: '/achievements', 
      value: badges || 0,
      color: 'text-blue-500'
    },
    { 
      icon: Target, 
      label: 'Mục tiêu', 
      href: '/daily-goals', 
      value: 'Hôm nay',
      color: 'text-green-500'
    },
    { 
      icon: Gift, 
      label: 'Phần thưởng', 
      href: '/rewards', 
      value: 'Mới',
      color: 'text-purple-500'
    },
  ]
  
  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <h3 className="text-lg font-display font-semibold text-foreground mb-4">
        Trung tâm thành tích
      </h3>
      
      <div className="grid grid-cols-2 gap-3">
        {items.map(({ icon: Icon, label, href, value, color }) => (
          <Link 
            key={href} 
            href={href} 
            className="group relative overflow-hidden rounded-lg border border-border bg-secondary/30 p-4 hover:bg-secondary/50 hover:border-primary/30 transition-all duration-300 hover:shadow-[0_0_15px_rgba(var(--primary),0.1)]"
          >
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <Icon className={`w-6 h-6 ${color} group-hover:scale-110 transition-transform duration-300`} />
                <div className="text-xs text-muted-foreground group-hover:text-foreground transition-colors">
                  →
                </div>
              </div>
              <div>
                <p className="font-semibold text-sm text-foreground">{label}</p>
                <p className="text-sm text-muted-foreground mt-1">{value}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

