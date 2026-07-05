interface SensorsPanelProps {
  frontDist: number
  rearDist: number
  motorTemp: number
  controllerTemp: number
  steeringAngle: number
  forkLoad: number
}

export default function SensorsPanel({ frontDist, rearDist, motorTemp, controllerTemp, steeringAngle, forkLoad }: SensorsPanelProps) {
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
      <h3 style={{ borderLeft: '3px solid #00ffff', paddingLeft: '10px', color: '#8ab4f8', fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
        Сенсоры &amp; Параметры
      </h3>
      <div className="grid grid-cols-2 gap-x-3 gap-y-1">
        <div>
          <p style={{ color: '#6a8aaa', fontSize: '11px' }}>Дальномер (перед)</p>
          <p style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{frontDist.toFixed(1)} м</p>
        </div>
        <div>
          <p style={{ color: '#6a8aaa', fontSize: '11px' }}>Дальномер (зад)</p>
          <p style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{rearDist.toFixed(1)} м</p>
        </div>
        <div>
          <p style={{ color: '#6a8aaa', fontSize: '11px' }}>Темп. двигателя</p>
          <p style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{motorTemp} °C</p>
        </div>
        <div>
          <p style={{ color: '#6a8aaa', fontSize: '11px' }}>Темп. контроллера</p>
          <p style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{controllerTemp} °C</p>
        </div>
        <div>
          <p style={{ color: '#6a8aaa', fontSize: '11px' }}>Нагрузка на вилы</p>
          <p style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{forkLoad} кг</p>
        </div>
        <div>
          <p style={{ color: '#6a8aaa', fontSize: '11px' }}>Угол поворота</p>
          <p style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{steeringAngle}°</p>
        </div>
      </div>
    </div>
  )
}
