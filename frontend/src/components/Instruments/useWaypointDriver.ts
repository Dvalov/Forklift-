import { useRef, useState, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { advanceTask } from '@/api/tasks'
import type { Task } from '@/types/api'
import { FORKLIFT_ID } from '@/config'

const CELL_SIZE = 20
const MS_PER_CELL = 1000

function toPixel(x: number, z: number) {
  return { px: (x + 0.5) * CELL_SIZE, py: (z + 0.5) * CELL_SIZE }
}

type Wp = { x: number; y: number }

export function useWaypointDriver(
  activeTask: Task | null,
  serverCell: { x: number; y: number },
): { px: number; py: number; pendingWaypoints: Wp[] } {
  const queueRef      = useRef<Wp[]>([])
  const posRef        = useRef(toPixel(serverCell.x, serverCell.y))
  const rafRef        = useRef<number | null>(null)
  const activeTaskRef = useRef(activeTask)
  const needsResync   = useRef(false)

  activeTaskRef.current = activeTask

  const [pos, setPos]                       = useState(posRef.current)
  const [pendingWaypoints, setPending]      = useState<Wp[]>([])

  const qc = useQueryClient()

  function cancelAnim() {
    if (rafRef.current !== null) {
      cancelAnimationFrame(rafRef.current)
      rafRef.current = null
    }
  }

  function arrive() {
    const task = activeTaskRef.current
    if (task) advanceTask(task.id)   // fire-and-forget

    queueRef.current = queueRef.current.slice(1)
    setPending([...queueRef.current])
    driveNext()
  }

  function driveNext() {
    if (queueRef.current.length === 0) return

    const target = queueRef.current[0]
    const from   = { ...posRef.current }
    const to     = toPixel(target.x, target.y)
    const dx     = to.px - from.px
    const dy     = to.py - from.py
    const dur    = (Math.hypot(dx, dy) / CELL_SIZE) * MS_PER_CELL

    if (dur <= 0) { arrive(); return }

    const t0   = performance.now()
    const tick = (now: number) => {
      const t   = Math.min((now - t0) / dur, 1)
      const cur = { px: from.px + dx * t, py: from.py + dy * t }
      posRef.current = cur
      setPos({ ...cur })
      if (t < 1) rafRef.current = requestAnimationFrame(tick)
      else { rafRef.current = null; arrive() }
    }
    rafRef.current = requestAnimationFrame(tick)
  }

  function initFrom(task: Task | null, cell: { x: number; y: number }) {
    cancelAnim()
    const wps = task
      ? (task.path_waypoints ?? []).map(wp => ({ x: Math.round(wp.x), y: Math.round(wp.z) }))
      : []
    queueRef.current = wps
    setPending(wps)
    const p = toPixel(cell.x, cell.y)
    posRef.current = p
    setPos(p)
    if (wps.length > 0) driveNext()
  }

  // Re-initialize when a new task starts (or task ends)
  useEffect(() => {
    initFrom(activeTask, serverCell)
  }, [activeTask?.id]) // eslint-disable-line

  // When idle, keep triangle synced to server position
  useEffect(() => {
    if (activeTask !== null) return
    const p = toPixel(serverCell.x, serverCell.y)
    posRef.current = p
    setPos(p)
  }, [serverCell.x, serverCell.y]) // eslint-disable-line

  // Re-sync from server after tab becomes visible again
  useEffect(() => {
    if (!needsResync.current) return
    needsResync.current = false
    initFrom(activeTask, serverCell)
  }, [serverCell.x, serverCell.y]) // eslint-disable-line — fires when forklift poll refreshes

  // Handle tab visibility
  useEffect(() => {
    const onVisibility = () => {
      if (document.visibilityState === 'visible') {
        needsResync.current = true
        qc.invalidateQueries({ queryKey: ['tasks',    FORKLIFT_ID] })
        qc.invalidateQueries({ queryKey: ['forklift', FORKLIFT_ID] })
      } else {
        cancelAnim()   // pause — backend takes over after 2 s
      }
    }
    document.addEventListener('visibilitychange', onVisibility)
    return () => document.removeEventListener('visibilitychange', onVisibility)
  }, [qc]) // eslint-disable-line

  return { px: pos.px, py: pos.py, pendingWaypoints }
}
