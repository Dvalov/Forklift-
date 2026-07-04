import TopStatusBar from './TopStatusBar'
import BottomStatusBar from './BottomStatusBar'
import HydraulicsPanel from './HydraulicsPanel'
import SensorsPanel from './SensorsPanel'
import BatteryPanel from './BatteryPanel'
import SpeedometerGauge from './SpeedometerGauge'
import WarehouseMap from './WarehouseMap'

const MOCK = {
  speed: 1.4,
  maxSpeed: 5.0,
  direction: 'forward' as const,

  mode: 'Авто',
  connected: true,
  taskNumber: 'ЗД-0042',
  errorText: null as string | null,
  cargoWeight: 320,

  map: {
    forkliftCell: { x: 3, y: 4 },
    targetCell: { x: 8, y: 6 },
    forkliftDirection: 45,
    gridCols: 10,
    gridRows: 8,
  },

  hydraulics: { pressure: 180, oilTemp: 62, forkHeight: 1.8, tilt: 3 },
  sensors: { frontDist: 2.4, rearDist: 0.8, motorTemp: 74, steeringAngle: 12, forkLoad: 280 },
  battery: { level: 67, voltage: 48.2, current: 14.5 },
  status: { moving: true, cargo: true, navigation: true, diagnostics: false, stopValve: false },
}

export default function InstrumentPanel() {
  return (
    <div className="flex flex-col gap-4 p-4">
      <TopStatusBar
        mode={MOCK.mode}
        connected={MOCK.connected}
        taskNumber={MOCK.taskNumber}
        errorText={MOCK.errorText}
        cargoWeight={MOCK.cargoWeight}
      />

      <div className="grid grid-cols-2 gap-4">
        <SpeedometerGauge speed={MOCK.speed} maxSpeed={MOCK.maxSpeed} direction={MOCK.direction} />
        <WarehouseMap
          forkliftCell={MOCK.map.forkliftCell}
          targetCell={MOCK.map.targetCell}
          forkliftDirection={MOCK.map.forkliftDirection}
          gridCols={MOCK.map.gridCols}
          gridRows={MOCK.map.gridRows}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <HydraulicsPanel {...MOCK.hydraulics} />
        <SensorsPanel {...MOCK.sensors} />
      </div>

      <BatteryPanel {...MOCK.battery} />

      <BottomStatusBar {...MOCK.status} />
    </div>
  )
}
