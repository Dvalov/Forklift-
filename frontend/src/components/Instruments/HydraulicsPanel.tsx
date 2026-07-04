interface HydraulicsPanelProps {
  pressure: number
  oilTemp: number
  forkHeight: number
  tilt: number
}

export default function HydraulicsPanel({ pressure, oilTemp, forkHeight, tilt }: HydraulicsPanelProps) {
  return (
    <div
      className="rounded-2xl p-4"
      style={{ background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(5px)', WebkitBackdropFilter: 'blur(5px)', border: '1px solid rgba(0,255,255,0.1)' }}
    >
      <h3 style={{ borderLeft: '3px solid #00ffff', paddingLeft: '12px', color: '#8ab4f8', fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>
        Гидравлика
      </h3>
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col">
          <span style={{ color: '#6a8aaa', fontSize: '12px' }}>Давление</span>
          <span style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{pressure} бар</span>
        </div>
        <div className="flex flex-col">
          <span style={{ color: '#6a8aaa', fontSize: '12px' }}>Масло</span>
          <span style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{oilTemp} °C</span>
        </div>
        <div className="flex flex-col">
          <span style={{ color: '#6a8aaa', fontSize: '12px' }}>Высота вил</span>
          <span style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{forkHeight.toFixed(1)} м</span>
        </div>
        <div className="flex flex-col">
          <span style={{ color: '#6a8aaa', fontSize: '12px' }}>Наклон</span>
          <span style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{tilt} °</span>
        </div>
      </div>
    </div>
  )
}
