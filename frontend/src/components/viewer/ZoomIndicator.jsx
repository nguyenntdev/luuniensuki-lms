'use client'
import { useEffect, useState, useRef } from 'react'

export default function ZoomIndicator({ controlsRef }) {
  const [zoomLevel, setZoomLevel] = useState(100)
  const [visible, setVisible] = useState(false)
  const timeoutRef = useRef(null)

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

