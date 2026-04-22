'use client'
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'

export default function ViewerControls({ onZoomIn, onZoomOut, onFitView, className = '' }) {
  return (
    <div className={`flex flex-col gap-2 ${className}`}>
      <button
        onClick={onZoomIn}
        className="p-2 bg-white/80 backdrop-blur rounded-full shadow-lg hover:bg-white transition-colors"
        title="Phóng to"
        aria-label="Phóng to"
      >
        <ZoomIn className="w-5 h-5" />
      </button>
      <button
        onClick={onZoomOut}
        className="p-2 bg-white/80 backdrop-blur rounded-full shadow-lg hover:bg-white transition-colors"
        title="Thu nhỏ"
        aria-label="Thu nhỏ"
      >
        <ZoomOut className="w-5 h-5" />
      </button>
      <button
        onClick={onFitView}
        className="p-2 bg-white/80 backdrop-blur rounded-full shadow-lg hover:bg-white transition-colors"
        title="Xem toàn cảnh"
        aria-label="Xem toàn cảnh"
      >
        <Maximize2 className="w-5 h-5" />
      </button>
    </div>
  )
}

