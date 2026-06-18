import type { Forklift } from '@/types/api'

const statusStyles: Record<Forklift['status'], string> = {
  idle: 'text-gray-400 bg-gray-800',
  moving: 'text-blue-300 bg-blue-900',
  loading: 'text-warning bg-amber-900',
  error: 'text-danger bg-red-900 animate-pulse',
  stopped: 'text-red-800 bg-red-950',
}

export default function StatusBadge({ status }: { status: Forklift['status'] }) {
  return (
    <span className={`inline-block px-2 py-1 rounded text-sm font-medium ${statusStyles[status]}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  )
}
