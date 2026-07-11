import { useForkliftQuery } from '@/components/ForkliftStatus/useForkliftQuery'
import { useTasksQuery } from '@/components/TaskList/useTasksQuery'

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

  const forkliftCell = data
    ? { x: Math.round(data.position_x), y: Math.round(data.position_z) }
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

  const svgWidth = gridCols * CELL_SIZE
  const svgHeight = gridRows * CELL_SIZE
  const fl = cellToPixel(forkliftCell.x, forkliftCell.y)
  const tgt = cellToPixel(targetCell.x, targetCell.y)

  const waypointPoints = activeTask?.path_waypoints?.map(wp =>
    cellToPixel(wp.x, wp.z)
  ) ?? []

  const waypointPointsStr = waypointPoints.map(p => `${p.px},${p.py}`).join(' ')

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

          {Array.from({ length: gridCols + 1 }, (_, i) => (
            <line key={`v${i}`} x1={i * CELL_SIZE} y1={0} x2={i * CELL_SIZE} y2={svgHeight} stroke="rgba(0,255,255,0.15)" strokeWidth="0.5" />
          ))}
          {Array.from({ length: gridRows + 1 }, (_, i) => (
            <line key={`h${i}`} x1={0} y1={i * CELL_SIZE} x2={svgWidth} y2={i * CELL_SIZE} stroke="rgba(0,255,255,0.15)" strokeWidth="0.5" />
          ))}

          {/* Route */}
          {waypointPoints.length >= 2 ? (
            <polyline
              points={waypointPointsStr}
              fill="none"
              stroke="#3fb950"
              strokeWidth="1.5"
              strokeDasharray="4 2"
            />
          ) : (
            <line x1={fl.px} y1={fl.py} x2={tgt.px} y2={tgt.py} stroke="#3fb950" strokeWidth="1.5" strokeDasharray="4 2" />
          )}

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
          <polygon
            points={`${fl.px},${fl.py - 8} ${fl.px - 6},${fl.py + 5} ${fl.px + 6},${fl.py + 5}`}
            fill="#00ffff"
            transform={`rotate(${forkliftDirection}, ${fl.px}, ${fl.py})`}
          />
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
              X:{position.x} Z:{position.z}
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
