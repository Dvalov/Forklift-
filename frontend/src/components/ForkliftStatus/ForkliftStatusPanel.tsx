import { useForkliftQuery } from './useForkliftQuery'
import StatusBadge from './StatusBadge'
import BatteryBar from './BatteryBar'
import PositionDisplay from './PositionDisplay'
import StalenessIndicator from './StalenessIndicator'

export default function ForkliftStatusPanel() {
  const { data, isLoading, isError, lastSuccessAt } = useForkliftQuery()

  if (isLoading && !data) {
    return (
      <div
        className="flex items-center justify-center h-32 text-sm"
        style={{ color: '#8ab4f8' }}
      >
        Загрузка…
      </div>
    )
  }

  if (isError && !data) {
    return (
      <div className="text-accent-err text-sm px-6 py-4">
        Не удалось подключиться к сервису погрузчика
      </div>
    )
  }

  if (!data) return null

  return (
    <div
      className="rounded-2xl p-4 space-y-4"
      style={{
        background: 'rgba(0,0,0,0.4)',
        backdropFilter: 'blur(5px)',
        WebkitBackdropFilter: 'blur(5px)',
        border: '1px solid rgba(0,255,255,0.1)',
      }}
    >
      <div className="flex items-center gap-3">
        <h2 className="text-base font-semibold" style={{ color: '#e0f0ff' }}>{data.name}</h2>
        <StatusBadge status={data.status} />
      </div>

      <StalenessIndicator lastSuccessAt={lastSuccessAt} />

      <div>
        <p className="mb-1" style={{ color: '#6a8aaa', fontSize: '12px' }}>Заряд батареи</p>
        <BatteryBar level={Math.round(data.charge_level)} />
      </div>

      <div>
        <p className="mb-2" style={{ color: '#6a8aaa', fontSize: '12px' }}>Позиция</p>
        <PositionDisplay x={data.position_x} y={data.position_y} z={data.position_z} />
      </div>

    </div>
  )
}
