'use client';

import { useEffect, useState } from 'react';
import { Map } from 'lucide-react';
import { getDashboardSummary } from '@/lib/api';

const MASTERY_LEVELS = [
  { min: 0, max: 0, label: 'Mới', color: 'text-gray-400', strokeColor: '#9ca3af', bgColor: 'bg-gray-400' },
  { min: 1, max: 32, label: 'Cơ bản', color: 'text-blue-500', strokeColor: '#3b82f6', bgColor: 'bg-blue-500' },
  { min: 33, max: 65, label: 'Trung cấp', color: 'text-yellow-500', strokeColor: '#eab308', bgColor: 'bg-yellow-500' },
  { min: 66, max: 89, label: 'Nâng cao', color: 'text-green-500', strokeColor: '#22c55e', bgColor: 'bg-green-500' },
  { min: 90, max: 100, label: 'Thành thạo', color: 'text-amber-500', strokeColor: '#f59e0b', bgColor: 'bg-amber-500' },
];

export default function KnowledgeMasteryCard() {
  const [urns, setUrns] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    let cancelled = false;
    
    async function fetchData() {
      try {
        setLoading(true);
        const data = await getDashboardSummary();
        if (!cancelled && data?.urns) {
          setUrns(data.urns);
        }
      } catch (err) {
        console.error('Failed to load dashboard summary:', err);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    
    fetchData();
    
    return () => {
      cancelled = true;
    };
  }, []);
  
  const getMasteryLevel = (percent) => {
    return MASTERY_LEVELS.find(l => percent >= l.min && percent <= l.max) || MASTERY_LEVELS[0];
  };
  
  if (loading) {
    return (
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-4">
          <Map className="w-5 h-5 text-primary" />
          <h3 className="text-lg font-display font-semibold text-foreground">
            Bản đồ tri thức
          </h3>
        </div>
        <div className="flex items-center justify-center py-12">
          <p className="text-sm text-muted-foreground">Đang tải...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
      <div className="flex items-center gap-2 mb-4">
        <Map className="w-5 h-5 text-primary" />
        <h3 className="text-lg font-display font-semibold text-foreground">
          Bản đồ tri thức
        </h3>
      </div>
      
      <div className="grid grid-cols-3 gap-4 mb-6">
        {urns.map(urn => {
          const urnProgress = urn.progress_percent || 0;
          const level = getMasteryLevel(urnProgress);
          const circumference = 2 * Math.PI * 28;
          const strokeDashoffset = circumference - (urnProgress / 100) * circumference;
          
          return (
            <div key={urn.id} className="flex flex-col items-center gap-2">
              <div className="relative w-20 h-20">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 64 64">
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="4"
                    className="text-border"
                  />
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    fill="none"
                    stroke={level.strokeColor}
                    strokeWidth="4"
                    strokeDasharray={circumference}
                    strokeDashoffset={strokeDashoffset}
                    strokeLinecap="round"
                    className="transition-all duration-500"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className={`text-sm font-bold ${level.color}`}>
                    {urnProgress}%
                  </span>
                </div>
              </div>
              <span className="text-xs text-center text-foreground font-medium line-clamp-2">
                {urn.name}
              </span>
              <span className={`text-xs ${level.color} font-medium`}>
                {level.label}
              </span>
            </div>
          );
        })}
      </div>
      
      <div className="pt-4 border-t border-border">
        <div className="flex flex-wrap gap-3 justify-center">
          {MASTERY_LEVELS.slice(1).map(level => (
            <div key={level.label} className="flex items-center gap-1.5">
              <div className={`w-3 h-3 rounded-full ${level.bgColor}`} />
              <span className="text-xs text-muted-foreground">{level.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

