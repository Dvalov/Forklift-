import { useRef, useState, useEffect } from 'react'
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

function cellToPixel(cellX: number, cellY: number) {
  return { px: (cellX + 0.5) * CELL_SIZE, py: (cellY + 0.5) * CELL_SIZE }
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

  const derivedCols = allCells.length > 0
    ? Math.max(...allCells.map(c => c.x)) + 1
    : (gridCols ?? 10)
  const derivedRows = allCells.length > 0
    ? Math.max(...allCells.map(c => c.z)) + 1
    : (gridRows ?? 8)

  // Group cells by (x, z); a position is occupied if ANY y-level has available=false
  const cellMap = new Map<string, boolean>()
  for (const cell of allCells) {
    const key = `${cell.x}:${cell.z}`
    const existing = cellMap.get(key)
    // available=true only if ALL y-levels are true; false overrides true
    cellMap.set(key, existing === false ? false : cell.available)
  }

  const svgWidth = derivedCols * CELL_SIZE
  const svgHeight = derivedRows * CELL_SIZE
  const fl = cellToPixel(forkliftCell.x, forkliftCell.y)
  const tgt = cellToPixel(targetCell.x, targetCell.y)

  // Animated forklift position — follows waypoints between polled positions
  const animFlRef = useRef({ px: fl.px, py: fl.py })
  const [animFl, setAnimFl] = useState({ px: fl.px, py: fl.py })
  const rafRef = useRef<number | null>(null)

  useEffect(() => {
    const from = animFlRef.current
    const to = { px: fl.px, py: fl.py }
    if (from.px === to.px && from.py === to.py) return
    if (rafRef.current !== null) cancelAnimationFrame(rafRef.current)

    const dx = to.px - from.px
    const dy = to.py - from.py
    const dur = (Math.hypot(dx, dy) / CELL_SIZE) * 1000
    if (dur <= 0) { animFlRef.current = to; setAnimFl(to); return }
    const t0 = performance.now()
    const src = { ...from }
    const tick = (now: number) => {
      const t = Math.min((now - t0) / dur, 1)
      const cur = { px: src.px + dx * t, py: src.py + dy * t }
      animFlRef.current = cur
      setAnimFl({ ...cur })
      rafRef.current = t < 1 ? requestAnimationFrame(tick) : null
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => { if (rafRef.current !== null) cancelAnimationFrame(rafRef.current) }
  }, [fl.px, fl.py]) // eslint-disable-line react-hooks/exhaustive-deps

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

      {/* SVG fills all remaining space */}
      <div className="flex-1 min-h-0 relative">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
          preserveAspectRatio="xMidYMid meet"
        >
          <rect x="0" y="0" width={svgWidth} height={svgHeight} fill="rgba(0,0,0,0.3)" />

          {/* Cell background layer */}
          {(() => {
            const rects: JSX.Element[] = []
            cellMap.forEach((available, key) => {
              const [cx, cz] = key.split(':').map(Number)
              const isForklift = cx === forkliftCell.x && cz === forkliftCell.y
              const isTarget   = cx === targetCell.x   && cz === targetCell.y
              let fill: string
              let stroke: string = 'none'
              let strokeWidth: string = '0'
              if (isForklift) {
                fill = 'rgba(0,255,255,0.12)'
                stroke = '#00ffff'
                strokeWidth = '1'
              } else if (isTarget) {
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
                  x={cx * CELL_SIZE}
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

          {/* Waypoint highlight layer — rounds float coords to cell grid, deduplicates */}
          {(() => {
            if (!activeTask?.path_waypoints?.length) return null
            const seen = new Set<string>()
            return activeTask.path_waypoints.map((wp) => {
              const cx = Math.round(wp.x)
              const cz = Math.round(wp.z)
              const key = `${cx}:${cz}`
              if (seen.has(key)) return null
              seen.add(key)
              if ((cx === forkliftCell.x && cz === forkliftCell.y) ||
                  (cx === targetCell.x   && cz === targetCell.y)) return null
              return (
                <rect
                  key={`wp-${key}`}
                  x={cx * CELL_SIZE}
                  y={cz * CELL_SIZE}
                  width={CELL_SIZE}
                  height={CELL_SIZE}
                  fill="rgba(58,185,80,0.2)"
                  stroke="#3fb950"
                  strokeWidth="1"
                />
              )
            })
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

          {/* Target label */}
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
