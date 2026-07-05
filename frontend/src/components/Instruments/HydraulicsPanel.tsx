interface HydraulicsPanelProps {
  pressure: number
  oilTemp: number
  forkHeight: number
  tilt: number
  pumpRpm: number
  valvesOk: boolean
  oilLevel: number
  status: string
}

export default function HydraulicsPanel({ pressure, oilTemp, forkHeight, tilt, pumpRpm, valvesOk, oilLevel, status }: HydraulicsPanelProps) {
  return (
    <div
      className="rounded-2xl p-2"
      style={{
        background: 'rgba(0,0,0,0.4)',
        backdropFilter: 'blur(5px)',
        WebkitBackdropFilter: 'blur(5px)',
        border: '1px solid rgba(0,255,255,0.1)',
      }}
    >
      <div className="flex items-center justify-between mb-1">
        <h3 style={{ borderLeft: '3px solid #00ffff', paddingLeft: '10px', color: '#8ab4f8', fontSize: '13px', fontWeight: 600 }}>
          Гидравлика
        </h3>
        <div className="flex items-center gap-1">
          <span style={{ width: 7, height: 7, borderRadius: '50%', backgroundColor: '#3fb950', display: 'inline-block' }} />
          <span style={{ color: '#3fb950', fontSize: '11px', fontWeight: 600 }}>{status}</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-x-3 gap-y-1 mb-1">
        <div>
          <p style={{ color: '#6a8aaa', fontSize: '11px' }}>Давление</p>
          <p style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{pressure} бар</p>
        </div>
        <div>
          <p style={{ color: '#6a8aaa', fontSize: '11px' }}>Темп. масла</p>
          <p style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{oilTemp} °C</p>
        </div>
        <div>
          <p style={{ color: '#6a8aaa', fontSize: '11px' }}>Высота вил</p>
          <p style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{forkHeight.toFixed(1)} м</p>
        </div>
        <div>
          <p style={{ color: '#6a8aaa', fontSize: '11px' }}>Наклон</p>
          <p style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{tilt > 0 ? '+' : ''}{tilt}°</p>
        </div>
      </div>

      <div
        className="flex justify-between pt-2"
        style={{ borderTop: '1px solid rgba(0,255,255,0.08)', fontSize: '11px' }}
      >
        <span>
          <span style={{ color: '#6a8aaa' }}>Насос: </span>
          <span style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600 }}>{pumpRpm} об/мин</span>
        </span>
        <span>
          <span style={{ color: '#6a8aaa' }}>Клапаны: </span>
          <span style={{ color: valvesOk ? '#3fb950' : '#ff3366', fontWeight: 600 }}>{valvesOk ? 'ОК' : 'ОШИБКА'}</span>
        </span>
        <span>
          <span style={{ color: '#6a8aaa' }}>Масло: </span>
          <span style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600 }}>{oilLevel}%</span>
        </span>
      </div>
    </div>
  )
}
