'use client'
import { useState, useEffect } from 'react'
import { MousePointer2, ZoomIn, RotateCcw } from 'lucide-react'

interface GestureHintsOverlayProps {
  onDismiss?: () => void
}

export default function GestureHintsOverlay({ onDismiss }: GestureHintsOverlayProps) {
  const [visible, setVisible] = useState(true)
  
  // Auto-dismiss after 4 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      setVisible(false)
      onDismiss?.()
    }, 4000)
    return () => clearTimeout(timer)
  }, [onDismiss])
  
  // Also dismiss on any interaction
  useEffect(() => {
    const handler = () => {
      setVisible(false)
      onDismiss?.()
    }
    window.addEventListener('mousedown', handler)
    window.addEventListener('touchstart', handler)
    return () => {
      window.removeEventListener('mousedown', handler)
      window.removeEventListener('touchstart', handler)
    }
  }, [onDismiss])
  
  if (!visible) return null
  
  return (
    <div className="absolute inset-0 z-10 pointer-events-none flex items-center justify-center bg-black/30">
      <div className="bg-white/90 backdrop-blur rounded-lg p-6 text-center max-w-xs">
        <div className="flex justify-center gap-8 mb-4">
          <div className="text-center">
            <MousePointer2 className="w-8 h-8 mx-auto mb-1 text-primary" />
            <p className="text-xs">Kéo để xoay</p>
          </div>
          <div className="text-center">
            <ZoomIn className="w-8 h-8 mx-auto mb-1 text-primary" />
            <p className="text-xs">Cuộn để thu/phóng</p>
          </div>
        </div>
        <p className="text-sm text-muted-foreground">Nhấp vào bất kỳ đâu để tiếp tục</p>
      </div>
    </div>
  )
}

