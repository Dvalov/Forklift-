import { useRef, useState, useEffect, type ReactElement } from 'react'
import { useForkliftQuery } from '@/components/ForkliftStatus/useForkliftQuery'
import { useTasksQuery } from '@/components/TaskList/useTasksQuery'
import { useAllCellsQuery } from './useAllCellsQuery'

interface WarehouseMapProps {
  forkliftCell: { x: number; y: number }
  targetCell: { x: number; y: number }
  forkliftDirection: number
  gridCols?: number
  gridRows?: number
  position?: { x: number; z: number }
  targetLabel?: string
  obstacle?: string | null
  angle?: number
}

const CELL_SIZE = 20

// Map logical cell x to display x with aisles: cell 1→1, 2→3, 3→5, …
const cellDispX = (x: number) => 2 * x - 1

// For logical cell coords (shelf addresses: dest_cell_x)
function cellToPixel(cellX: number, cellY: number) {
  return { px: (cellDispX(cellX) + 0.5) * CELL_SIZE, py: (cellY + 0.5) * CELL_SIZE }
}

// For display coords (forklift.cell_x, path_waypoints — A* grid space)
function dispToPixel(dispX: number, dispZ: number) {
  return { px: (dispX + 0.5) * CELL_SIZE, py: (dispZ + 0.5) * CELL_SIZE }
}

export default function WarehouseMap({
  forkliftCell: fallbackCell,
  targetCell: fallbackTargetCell,
  forkliftDirection,
  gridCols = 10,
  gridRows = 8,
  position: fallbackPosition,
  targetLabel: fallbackTargetLabel,
  obstacle,
  angle,
}: WarehouseMapProps) {
  const { data } = useForkliftQuery()
  const { data: tasks } = useTasksQuery()
  const allCells = useAllCellsQuery()

  const forkliftCell = data
    ? { x: data.cell_x, y: data.cell_z }
    : fallbackCell

  const position = data
    ? { x: data.position_x, z: data.position_z }
    : fallbackPosition

  const activeTask = tasks?.find(t => t.status === 'in_progress') ?? null
  const targetCell = activeTask
    ? { x: activeTask.dest_cell_x, y: activeTask.dest_cell_z }
    : fallbackTargetCell
  const targetLabel = activeTask
    ? `ячейка ${activeTask.dest_cell_x} · ${activeTask.dest_cell_y} · ${activeTask.dest_cell_z}`
    : fallbackTargetLabel

  const maxCellX = allCells.length > 0
    ? Math.max(...allCells.map(c => c.x))
    : (gridCols ?? 10)
  const derivedCols = 2 * maxCellX
  const derivedRows = allCells.length > 0
    ? Math.max(...allCells.map(c => c.z)) + 1
    : (gridRows ?? 8)

  // Group cells by (x, z); occupied if ANY y-level has available=false
  const cellMap = new Map<string, boolean>()
  for (const cell of allCells) {
    const key = `${cell.x}:${cell.z}`
    const existing = cellMap.get(key)
    cellMap.set(key, existing === false ? false : cell.available)
  }

  const svgWidth  = derivedCols * CELL_SIZE
  const svgHeight = derivedRows * CELL_SIZE
  const fl  = dispToPixel(forkliftCell.x, forkliftCell.y)
  const tgt = cellToPixel(targetCell.x, targetCell.y)

  // Smooth rAF animation between server-reported positions
  const animFlRef = useRef({ px: fl.px, py: fl.py })
  const [animFl, setAnimFl] = useState({ px: fl.px, py: fl.py })
  const rafRef = useRef<number | null>(null)
  const hasRealData = useRef(data !== undefined)

  useEffect(() => {
    const from = animFlRef.current
    const to = { px: fl.px, py: fl.py }

    const firstData = !hasRealData.current && data !== undefined
    if (data !== undefined) hasRealData.current = true

    if (from.px === to.px && from.py === to.py) return
    if (rafRef.current !== null) cancelAnimationFrame(rafRef.current)

    if (firstData) {
      animFlRef.current = to
      setAnimFl(to)
      return
    }

    const dx = to.px - from.px
    const dy = to.py - from.py
    const dur = (Math.hypot(dx, dy) / CELL_SIZE) * 750
    if (dur <= 0) { animFlRef.current = to; setAnimFl(to); return }
    const t0 = performance.now()
    const src = { ...from }
    const tick = (now: number) => {
      const t = Math.min((now - t0) / dur, 1)
      const cur = { px: src.px + dx * t, py: src.py + dy * t }
      animFlRef.current = cur
      setAnimFl({ ...cur })
      if (t >= 1) rafRef.current = null
      else rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => { if (rafRef.current !== null) cancelAnimationFrame(rafRef.current) }
  }, [fl.px, fl.py]) // eslint-disable-line react-hooks/exhaustive-deps

  // Remaining waypoints straight from server (display coords)
  const waypoints = (activeTask?.path_waypoints ?? []).map(wp => ({
    x: Math.round(wp.x),
    y: Math.round(wp.z),
  }))

  return (
    <div
      className="rounded-2xl p-3 flex flex-col"
      style={{
        height: '100%',
        minHeight: '320px',
        background: 'rgba(0,0,0,0.4)',
        backdropFilter: 'blur(5px)',
        WebkitBackdropFilter: 'blur(5px)',
        border: '1px solid rgba(0,255,255,0.1)',
      }}
    >
      <div className="flex items-center justify-between mb-2 flex-shrink-0">
        <h3 style={{ borderLeft: '3px solid #00ffff', paddingLeft: '10px', color: '#8ab4f8', fontSize: '14px', fontWeight: 600 }}>
          Карта склада (вид сверху)
        </h3>
        <div className="flex items-center gap-1">
          <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: '#3fb950', display: 'inline-block' }} />
          <span style={{ color: '#6a8aaa', fontSize: '11px' }}>Зелёный маршрут</span>
        </div>
      </div>

      <div className="flex-1 min-h-0 relative">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
          preserveAspectRatio="xMidYMid meet"
        >
          <rect x="0" y="0" width={svgWidth} height={svgHeight} fill="rgba(0,0,0,0.3)" />

          {/* Cell background layer */}
          {(() => {
            const rects: ReactElement[] = []
            cellMap.forEach((available, key) => {
              const [cx, cz] = key.split(':').map(Number)
              const isTarget = cx === targetCell.x && cz === targetCell.y
              let fill: string
              let stroke = 'none'
              let strokeWidth = '0'
              if (isTarget) {
                fill = 'rgba(255,170,0,0.14)'
                stroke = '#ffaa00'
                strokeWidth = '1'
              } else if (!available) {
                fill = 'rgba(255,170,0,0.18)'
              } else {
                fill = 'rgba(0,255,255,0.04)'
              }
              rects.push(
                <rect
                  key={key}
                  x={cellDispX(cx) * CELL_SIZE}
                  y={cz * CELL_SIZE}
                  width={CELL_SIZE}
                  height={CELL_SIZE}
                  fill={fill}
                  stroke={stroke}
                  strokeWidth={strokeWidth}
                />
              )
            })
            return rects
          })()}

          {/* Waypoint highlight layer — server path_waypoints (display coords) */}
          {(() => {
            const seen = new Set<string>()
            const rects: ReactElement[] = []

            // Forklift current position (server)
            const flKey = `${forkliftCell.x}:${forkliftCell.y}`
            seen.add(flKey)
            rects.push(
              <rect key={`fl-${flKey}`}
                x={forkliftCell.x * CELL_SIZE} y={forkliftCell.y * CELL_SIZE}
                width={CELL_SIZE} height={CELL_SIZE}
                fill="rgba(58,185,80,0.2)" stroke="#3fb950" strokeWidth="1" />
            )

            for (const { x: cx, y: cz } of waypoints) {
              const key = `${cx}:${cz}`
              if (seen.has(key) || (cx === targetCell.x && cz === targetCell.y)) continue
              seen.add(key)
              rects.push(
                <rect key={`wp-${key}`}
                  x={cx * CELL_SIZE} y={cz * CELL_SIZE}
                  width={CELL_SIZE} height={CELL_SIZE}
                  fill="rgba(58,185,80,0.2)" stroke="#3fb950" strokeWidth="1" />
              )
            }

            return rects.length ? rects : null
          })()}

          {Array.from({ length: derivedCols + 1 }, (_, i) => (
            <line key={`v${i}`} x1={i * CELL_SIZE} y1={0} x2={i * CELL_SIZE} y2={svgHeight} stroke="rgba(0,255,255,0.15)" strokeWidth="0.5" />
          ))}
          {Array.from({ length: derivedRows + 1 }, (_, i) => (
            <line key={`h${i}`} x1={0} y1={i * CELL_SIZE} x2={svgWidth} y2={i * CELL_SIZE} stroke="rgba(0,255,255,0.15)" strokeWidth="0.5" />
          ))}

          {/* Target */}
          <circle cx={tgt.px} cy={tgt.py} r="5" fill="none" stroke="#ffaa00" strokeWidth="1.5" />
          <circle cx={tgt.px} cy={tgt.py} r="2" fill="#ffaa00" />
          {targetLabel && (
            <text x={tgt.px + 7} y={tgt.py - 4} fill="#ffaa00" fontSize="8" fontWeight="600">
              {targetLabel}
            </text>
          )}

          {/* Forklift */}
          <g transform={`translate(${animFl.px}, ${animFl.py})`}>
            <polygon
              points="0,-8 -6,5 6,5"
              fill="#00ffff"
              transform={`rotate(${forkliftDirection})`}
            />
          </g>
        </svg>
      </div>

      {/* Position info row */}
      <div
        className="grid grid-cols-4 gap-1 mt-2 pt-2 flex-shrink-0"
        style={{ borderTop: '1px solid rgba(0,255,255,0.1)' }}
      >
        {position && (
          <div>
            <p style={{ color: '#6a8aaa', fontSize: '10px', marginBottom: '2px' }}>Позиция</p>
            <p style={{ color: '#e0f0ff', fontSize: '11px', fontFamily: "'Courier New', monospace", fontWeight: 600 }}>
              X:{Number(position.x).toFixed(2)} Z:{Number(position.z).toFixed(2)}
            </p>
          </div>
        )}
        {targetLabel && (
          <div>
            <p style={{ color: '#6a8aaa', fontSize: '10px', marginBottom: '2px' }}>Цель</p>
            <p style={{ color: '#ffaa00', fontSize: '11px', fontWeight: 600 }}>{targetLabel}</p>
          </div>
        )}
        {obstacle !== undefined && (
          <div>
            <p style={{ color: '#6a8aaa', fontSize: '10px', marginBottom: '2px' }}>Препятствие</p>
            <p style={{ color: obstacle ? '#ff3366' : '#3fb950', fontSize: '11px', fontWeight: 600 }}>
              {obstacle ?? 'нет'}
            </p>
          </div>
        )}
        {angle !== undefined && (
          <div>
            <p style={{ color: '#6a8aaa', fontSize: '10px', marginBottom: '2px' }}>Угол</p>
            <p style={{ color: '#e0f0ff', fontSize: '11px', fontFamily: "'Courier New', monospace", fontWeight: 600 }}>
              {angle}°
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
