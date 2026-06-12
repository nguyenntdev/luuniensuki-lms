/**
 * Example: How to integrate viewer enhancements with UrnViewer
 * 
 * This file demonstrates:
 * 1. First-time gesture hints with localStorage tracking
 * 2. Zoom indicator display
 * 3. Camera reset button
 * 4. Viewer controls (zoom in/out, fit view)
 */

'use client'
import { useState, useEffect, useRef, useCallback, type ComponentProps } from 'react'
import type { Camera, Vector3 } from 'three'
import UrnViewer from '@/components/UrnViewer'
import {
  GestureHintsOverlay,
  ZoomIndicator,
  CameraResetButton,
  ViewerControls,
} from '@/components/viewer'

/**
 * Minimal shape of the three.js OrbitControls instance used here. The full
 * type lives in `three-stdlib`; this component only needs the camera (`object`),
 * the orbit `target` and `update()`.
 */
interface OrbitControlsLike {
  object: Camera
  target: Vector3
  update: () => void
}

const HINTS_STORAGE_KEY = '3d-viewer-hints-shown'

export default function EnhancedUrnViewer(props: Record<string, unknown>) {
  const [showHints, setShowHints] = useState(false)
  const controlsRef = useRef<OrbitControlsLike | null>(null)

  // Check if hints have been shown before
  useEffect(() => {
    const hasSeenHints = localStorage.getItem(HINTS_STORAGE_KEY)
    if (!hasSeenHints) {
      setShowHints(true)
    }
  }, [])

  const handleHintsDismiss = useCallback(() => {
    localStorage.setItem(HINTS_STORAGE_KEY, 'true')
    setShowHints(false)
  }, [])

  const handleZoomIn = useCallback(() => {
    if (!controlsRef.current) return
    const camera = controlsRef.current.object
    const target = controlsRef.current.target
    const direction = camera.position.clone().sub(target).normalize()
    camera.position.addScaledVector(direction, -0.5)
  }, [])

  const handleZoomOut = useCallback(() => {
    if (!controlsRef.current) return
    const camera = controlsRef.current.object
    const target = controlsRef.current.target
    const direction = camera.position.clone().sub(target).normalize()
    camera.position.addScaledVector(direction, 0.5)
  }, [])

  const handleFitView = useCallback(() => {
    if (!controlsRef.current) return
    const camera = controlsRef.current.object
    camera.position.set(0, 1.4, 3.6)
    controlsRef.current.target.set(0, 0, 0)
    controlsRef.current.update()
  }, [])

  const handleCameraReset = useCallback(() => {
    handleFitView()
  }, [handleFitView])

  return (
    <div className="relative h-full w-full">
      {/* Base 3D Viewer */}
      <UrnViewer {...(props as unknown as ComponentProps<typeof UrnViewer>)} />

      {/* First-time hints overlay */}
      {showHints && <GestureHintsOverlay onDismiss={handleHintsDismiss} />}

      {/* Zoom level indicator */}
      <ZoomIndicator
        controlsRef={
          controlsRef as ComponentProps<typeof ZoomIndicator>["controlsRef"]
        }
      />

      {/* Camera reset button - bottom right */}
      <div className="absolute bottom-4 right-4 z-20">
        <CameraResetButton onClick={handleCameraReset} />
      </div>

      {/* Viewer controls - bottom left */}
      <div className="absolute bottom-4 left-4 z-20">
        <ViewerControls
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
          onFitView={handleFitView}
        />
      </div>
    </div>
  )
}

