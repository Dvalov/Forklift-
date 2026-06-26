import type { Task } from '@/types/api'
import { X } from 'lucide-react'
import TaskStatusDot from './TaskStatusDot'
import { useCancelTask } from './useCancelTask'

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
          {task.status === 'pending' && (
            <button
              aria-label={`Cancel task ${task.id}`}
              disabled={cancelMutation.isPending}
              onClick={() => cancelMutation.mutate(task.id)}
              className="p-1 rounded text-danger hover:bg-danger/20 disabled:opacity-40 transition-colors"
            >
              {cancelMutation.isPending ? '…' : <X size={16} />}
            </button>
          )}
        </div>
      </div>
      {cancelMutation.isError && (
        <p className="text-xs text-danger pl-6">Cancel failed — try again</p>
      )}
    </li>
  )
}
