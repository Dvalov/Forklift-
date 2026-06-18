import { useForkliftQuery } from './useForkliftQuery'
import StatusBadge from './StatusBadge'
import BatteryBar from './BatteryBar'
import PositionDisplay from './PositionDisplay'
import UptimeCounter from './UptimeCounter'
import StalenessIndicator from './StalenessIndicator'

export default function ForkliftStatusPanel() {
  const { data, isLoading, isError, lastSuccessAt } = useForkliftQuery()

  if (isLoading && !data) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
        Loading…
      </div>
    )
  }

  if (isError && !data) {
    return (
      <div className="text-danger text-sm px-6 py-4">
        Unable to connect to forklift service
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-4 px-6 py-4">
      <div className="flex items-center gap-3">
        <h2 className="text-xl font-bold text-gray-100">{data.name}</h2>
        <StatusBadge status={data.status} />
      </div>

      <StalenessIndicator lastSuccessAt={lastSuccessAt} />

      <div>
        <p className="text-xs text-gray-400 mb-1">Battery</p>
        <BatteryBar level={Math.round(data.charge_level)} />
      </div>

      <div>
        <p className="text-xs text-gray-400 mb-2">Position</p>
        <PositionDisplay x={data.position_x} y={data.position_y} z={data.position_z} />
      </div>

      <div>
        <p className="text-xs text-gray-400 mb-1">Uptime</p>
        <UptimeCounter status={data.status} />
      </div>
    </div>
  )
}
