import type { Forklift } from '@/types/api'

type StatusStyle = { background: string; color: string }
type ForkliftStatus = Forklift['status'] | 'charging'

const statusStyleMap: Record<ForkliftStatus, StatusStyle> = {
  idle:     { background: '#6a8aaa', color: '#0a0e1a' },
  moving:   { background: '#8ab4f8', color: '#0a0e1a' },
  loading:  { background: '#ffaa00', color: '#0a0e1a' },
  error:    { background: '#ff3366', color: '#ffffff' },
  stopped:  { background: 'rgba(255,51,102,0.4)', color: '#ff3366' },
  charging: { background: '#a371f7', color: '#0a0e1a' },
}

const STATUS_LABEL: Record<ForkliftStatus, string> = {
  idle:     'Ожидание',
  moving:   'В движении',
  loading:  'Загрузка',
  error:    'Ошибка',
  stopped:  'Остановлен',
  charging: 'Зарядка',
}

export default function StatusBadge({ status }: { status: ForkliftStatus }) {
  return (
    <span
      className={`inline-block px-2 py-1 rounded text-sm font-medium${status === 'error' ? ' animate-pulse' : ''}`}
      style={statusStyleMap[status]}
    >
      {STATUS_LABEL[status]}
    </span>
  )
}
