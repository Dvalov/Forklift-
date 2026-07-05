import TopStatusBar from './TopStatusBar'
import BottomStatusBar from './BottomStatusBar'
import HydraulicsPanel from './HydraulicsPanel'
import SensorsPanel from './SensorsPanel'
import BatteryPanel from './BatteryPanel'
import SpeedometerGauge from './SpeedometerGauge'
import WarehouseMap from './WarehouseMap'

const MOCK = {
  speed: 1.89,
  maxSpeed: 3.0,
  direction: 'backward' as const,
  speedAlert: null as string | null,

  mode: 'Авто',
  signal: { type: '5G', strength: 97 },
  connected: true,
  taskNumber: '#4021',
  errorCount: 1,
  cargoWeight: 850,

  map: {
    forkliftCell: { x: 4, y: 7 },
    targetCell: { x: 7, y: 3 },
    forkliftDirection: 45,
    gridCols: 10,
    gridRows: 9,
    position: { x: 12.4, y: 8.7 },
    targetLabel: 'стеллаж B-7',
    obstacle: 'человек (2.3 м)',
    angle: 45,
  },

  hydraulics: {
    pressure: 146,
    oilTemp: 54,
    forkHeight: 1.5,
    tilt: 0,
    pumpRpm: 2800,
    valvesOk: true,
    oilLevel: 86,
    status: 'Работает',
  },
  sensors: {
    frontDist: 5.9,
    rearDist: 6.4,
    motorTemp: 42,
    controllerTemp: 38,
    steeringAngle: 12,
    forkLoad: 850,
  },
  battery: { level: 78, voltage: 86.4, current: 12.3, remaining: '4.2 ч' },
  eta: {
    seconds: 7,
    chargeWarning: 'до конца смены',
    speedWarning: 'снизить скорость в зоне стеллажа',
  },
  status: {
    moving: true,
    cargo: true,
    navigation: true,
    diagnostics: false,
    stopValve: false,
    navigationLabel: 'GPS + LiDAR',
    lastDiagnostics: '14:22',
  },
}

export default function InstrumentPanel() {
  return (
    <div
      className="flex flex-col gap-2 p-3"
      style={{ minHeight: '100%', boxSizing: 'border-box' }}
    >
      <TopStatusBar
        mode={MOCK.mode}
        signal={MOCK.signal}
        connected={MOCK.connected}
        taskNumber={MOCK.taskNumber}
        errorCount={MOCK.errorCount}
        cargoWeight={MOCK.cargoWeight}
      />

      <div className="grid grid-cols-3 gap-2" style={{ minHeight: 0 }}>
        {/* Left: Speedometer + Battery */}
        <div className="flex flex-col gap-2" style={{ minHeight: '320px' }}>
          <SpeedometerGauge
            speed={MOCK.speed}
            maxSpeed={MOCK.maxSpeed}
            direction={MOCK.direction}
            speedAlert={MOCK.speedAlert}
          />
          <BatteryPanel {...MOCK.battery} />
        </div>

        {/* Center: Map */}
        <WarehouseMap
          forkliftCell={MOCK.map.forkliftCell}
          targetCell={MOCK.map.targetCell}
          forkliftDirection={MOCK.map.forkliftDirection}
          gridCols={MOCK.map.gridCols}
          gridRows={MOCK.map.gridRows}
          position={MOCK.map.position}
          targetLabel={MOCK.map.targetLabel}
          obstacle={MOCK.map.obstacle}
          angle={MOCK.map.angle}
        />

        {/* Right: Hydraulics + Sensors + ETA */}
        <div className="flex flex-col gap-2">
          <HydraulicsPanel {...MOCK.hydraulics} />
          <SensorsPanel {...MOCK.sensors} />
          <div
            className="rounded-2xl p-2"
            style={{
              background: 'rgba(0,0,0,0.4)',
              backdropFilter: 'blur(5px)',
              WebkitBackdropFilter: 'blur(5px)',
              border: '1px solid rgba(0,255,255,0.1)',
            }}
          >
            <div className="flex items-center gap-2 mb-1">
              <span style={{ color: '#6a8aaa', fontSize: '12px' }}>⏱ До цели:</span>
              <span style={{ color: '#00ffff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '18px' }}>
                {MOCK.eta.seconds} с
              </span>
            </div>
            {MOCK.eta.chargeWarning && (
              <p className="text-xs mb-1" style={{ color: '#ffaa00' }}>
                🔋 Прогноз заряда: <strong>{MOCK.eta.chargeWarning}</strong>
              </p>
            )}
            {MOCK.eta.speedWarning && (
              <p className="text-xs" style={{ color: '#ffaa00' }}>
                🔀 Рекомендация: {MOCK.eta.speedWarning}
              </p>
            )}
          </div>
        </div>
      </div>

      <BottomStatusBar {...MOCK.status} />
    </div>
  )
}
