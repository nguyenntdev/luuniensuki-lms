'use client'
import { RotateCcw } from 'lucide-react'

interface CameraResetButtonProps {
  onClick?: React.MouseEventHandler<HTMLButtonElement>
  className?: string
}

export default function CameraResetButton({ onClick, className = '' }: CameraResetButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`p-2 bg-white/80 backdrop-blur rounded-full shadow-lg hover:bg-white transition-colors ${className}`}
      title="Đặt lại góc nhìn"
    >
      <RotateCcw className="w-5 h-5" />
    </button>
  )
}

