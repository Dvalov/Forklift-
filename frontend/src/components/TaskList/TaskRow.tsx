import type { Task } from '@/types/api'
import { X } from 'lucide-react'
import TaskStatusDot from './TaskStatusDot'
import { useCancelTask } from './useCancelTask'
import { useDeleteTask } from './useDeleteTask'

interface TaskRowProps {
  task: Task
}

const STATUS_LABEL: Record<Task['status'], string> = {
  pending:     'Pending',
  in_progress: 'In Progress',
  completed:   'Completed',
  failed:      'Failed',
  cancelled:   'Cancelled',
}

export default function TaskRow({ task }: TaskRowProps) {
  const cancelMutation = useCancelTask()
  const deleteMutation = useDeleteTask()

  const isPending = cancelMutation.isPending || deleteMutation.isPending

  function handleX() {
    if (task.status === 'pending') cancelMutation.mutate(task.id)
    else if (task.status === 'cancelled') deleteMutation.mutate(task.id)
  }

  const showX = task.status === 'pending' || task.status === 'cancelled'
  const isError = cancelMutation.isError || deleteMutation.isError
  const errorText = task.status === 'pending' ? 'Cancel failed' : 'Delete failed'

  const cellAddress = `${task.dest_cell_x} · ${task.dest_cell_y} · ${task.dest_cell_z}`
  const date = new Date(task.created_at).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  })

  return (
    <li>
      <div className="flex items-center w-full py-2">
        <div className="flex items-center w-28 flex-shrink-0">
          <TaskStatusDot status={task.status} />
          <span className="text-xs text-gray-300">{STATUS_LABEL[task.status]}</span>
        </div>
        <span className="flex-1 text-sm font-semibold text-gray-100">{cellAddress}</span>
        <span className="w-20 flex-shrink-0 text-right text-xs text-gray-400">{date}</span>
        <div className="w-8 flex-shrink-0 flex justify-end">
          {showX && (
            <button
              aria-label={task.status === 'pending' ? `Cancel task ${task.id}` : `Delete task ${task.id}`}
              disabled={isPending}
              onClick={handleX}
              className="p-1 rounded text-danger hover:bg-danger/20 disabled:opacity-40 transition-colors"
            >
              {isPending ? '…' : <X size={16} />}
            </button>
          )}
        </div>
      </div>
      {isError && (
        <p className="text-xs text-danger pl-6">{errorText} — try again</p>
      )}
    </li>
  )
}
