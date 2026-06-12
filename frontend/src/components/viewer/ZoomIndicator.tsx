'use client'
import { useEffect, useState, useRef } from 'react'
import type { Camera, Vector3 } from 'three'

/**
 * Minimal shape of the three.js OrbitControls instance this component reads.
 * The full type lives in `three-stdlib`; we only need the camera, target and
 * the change-event subscription surface here.
 */
interface OrbitControlsLike {
  object: Camera
  target: Vector3
  addEventListener: (type: string, listener: () => void) => void
  removeEventListener: (type: string, listener: () => void) => void
}

interface ZoomIndicatorProps {
  controlsRef: React.RefObject<OrbitControlsLike | null>
}

export default function ZoomIndicator({ controlsRef }: ZoomIndicatorProps) {
  const [zoomLevel, setZoomLevel] = useState(100)
  const [visible, setVisible] = useState(false)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!controlsRef?.current) return

    const controls = controlsRef.current
    const camera = controls.object

    const handleChange = () => {
      // Calculate zoom percentage based on camera distance
      const distance = camera.position.distanceTo(controls.target)
      const initialDistance = 3.6
      const zoom = Math.round((initialDistance / distance) * 100)
      
      setZoomLevel(Math.max(10, Math.min(500, zoom)))
      setVisible(true)

      // Hide after 1.5 seconds
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
      timeoutRef.current = setTimeout(() => {
        setVisible(false)
      }, 1500)
    }

    controls.addEventListener('change', handleChange)
    return () => {
      controls.removeEventListener('change', handleChange)
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [controlsRef])

  if (!visible) return null

  return (
    <div className="absolute top-4 right-4 z-20 bg-black/70 backdrop-blur-md text-white px-3 py-1.5 rounded-lg text-sm font-medium shadow-lg transition-opacity duration-300">
      {zoomLevel}%
    </div>
  )
}

