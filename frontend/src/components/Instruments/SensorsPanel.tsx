interface SensorsPanelProps {
  frontDist: number
  rearDist: number
  motorTemp: number
  steeringAngle: number
  forkLoad: number
}

export default function SensorsPanel({ frontDist, rearDist, motorTemp, steeringAngle, forkLoad }: SensorsPanelProps) {
  return (
    <div
      className="rounded-2xl p-4"
      style={{ background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(5px)', WebkitBackdropFilter: 'blur(5px)', border: '1px solid rgba(0,255,255,0.1)' }}
    >
      <h3 style={{ borderLeft: '3px solid #00ffff', paddingLeft: '12px', color: '#8ab4f8', fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>
        Датчики
      </h3>
      <div className="grid grid-cols-2 gap-4">
        <div className="flex flex-col">
          <span style={{ color: '#6a8aaa', fontSize: '12px' }}>Дальномер (пер.)</span>
          <span style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{frontDist.toFixed(1)} м</span>
        </div>
        <div className="flex flex-col">
          <span style={{ color: '#6a8aaa', fontSize: '12px' }}>Дальномер (зад.)</span>
          <span style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{rearDist.toFixed(1)} м</span>
        </div>
        <div className="flex flex-col">
          <span style={{ color: '#6a8aaa', fontSize: '12px' }}>Темп. двигателя</span>
          <span style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{motorTemp} °C</span>
        </div>
        <div className="flex flex-col">
          <span style={{ color: '#6a8aaa', fontSize: '12px' }}>Угол поворота</span>
          <span style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{steeringAngle} °</span>
        </div>
        <div className="flex flex-col">
          <span style={{ color: '#6a8aaa', fontSize: '12px' }}>Нагрузка на вилы</span>
          <span style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{forkLoad} кг</span>
        </div>
      </div>
    </div>
  )
}
