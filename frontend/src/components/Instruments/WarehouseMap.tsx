interface WarehouseMapProps {
  forkliftCell: { x: number; y: number }
  targetCell: { x: number; y: number }
  forkliftDirection: number
  gridCols?: number
  gridRows?: number
}

const CELL_SIZE = 20

function cellToPixel(cellX: number, cellY: number) {
  return { px: (cellX + 0.5) * CELL_SIZE, py: (cellY + 0.5) * CELL_SIZE }
}

export default function WarehouseMap({
  forkliftCell,
  targetCell,
  forkliftDirection,
  gridCols = 10,
  gridRows = 8,
}: WarehouseMapProps) {
  const cols = gridCols
  const rows = gridRows
  const svgWidth = cols * CELL_SIZE
  const svgHeight = rows * CELL_SIZE
  const fl = cellToPixel(forkliftCell.x, forkliftCell.y)
  const tgt = cellToPixel(targetCell.x, targetCell.y)

  return (
    <div
      className="rounded-2xl p-4"
      style={{ background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(5px)', WebkitBackdropFilter: 'blur(5px)', border: '1px solid rgba(0,255,255,0.1)' }}
    >
      <h3 style={{ borderLeft: '3px solid #00ffff', paddingLeft: '12px', color: '#8ab4f8', fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>
        Карта склада
      </h3>
      <svg
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        style={{ width: '100%', height: 'auto', display: 'block' }}
      >
        {/* Background */}
        <rect x="0" y="0" width={svgWidth} height={svgHeight} fill="rgba(0,0,0,0.3)" />

        {/* Vertical grid lines */}
        {Array.from({ length: cols + 1 }, (_, i) => (
          <line
            key={`v${i}`}
            x1={i * CELL_SIZE} y1={0}
            x2={i * CELL_SIZE} y2={svgHeight}
            stroke="rgba(0,255,255,0.15)" strokeWidth="0.5"
          />
        ))}

        {/* Horizontal grid lines */}
        {Array.from({ length: rows + 1 }, (_, i) => (
          <line
            key={`h${i}`}
            x1={0} y1={i * CELL_SIZE}
            x2={svgWidth} y2={i * CELL_SIZE}
            stroke="rgba(0,255,255,0.15)" strokeWidth="0.5"
          />
        ))}

        {/* Route line */}
        <line
          x1={fl.px} y1={fl.py}
          x2={tgt.px} y2={tgt.py}
          stroke="#00ffff" strokeWidth="1.5" strokeDasharray="4 2"
        />

        {/* Target icon */}
        <circle cx={tgt.px} cy={tgt.py} r="5" fill="none" stroke="#ffaa00" strokeWidth="1.5" />
        <circle cx={tgt.px} cy={tgt.py} r="2" fill="#ffaa00" />

        {/* Forklift polygon — USE SVG transform ATTRIBUTE, not CSS */}
        <polygon
          points={`${fl.px},${fl.py - 8} ${fl.px - 6},${fl.py + 5} ${fl.px + 6},${fl.py + 5}`}
          fill="#00ffff"
          transform={`rotate(${forkliftDirection}, ${fl.px}, ${fl.py})`}
        />
      </svg>
    </div>
  )
}
