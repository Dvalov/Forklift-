import type { Task } from '@/types/api'
import { X, RotateCcw } from 'lucide-react'
import TaskStatusDot from './TaskStatusDot'
import { useCancelTask } from './useCancelTask'
import { useDeleteTask } from './useDeleteTask'
import { useRestoreTask } from './useRestoreTask'

interface TaskRowProps {
  task: Task
}

const STATUS_LABEL: Record<Task['status'], string> = {
  pending:     'Ожидание',
  in_progress: 'В работе',
  completed:   'Выполнено',
  failed:      'Ошибка',
  cancelled:   'Отменена',
}

export default function TaskRow({ task }: TaskRowProps) {
  const cancelMutation = useCancelTask()
  const deleteMutation = useDeleteTask()
  const restoreMutation = useRestoreTask()

  const isBusy = cancelMutation.isPending || deleteMutation.isPending || restoreMutation.isPending

  function handleX() {
    if (task.status === 'pending') cancelMutation.mutate(task.id)
    else if (task.status === 'cancelled') deleteMutation.mutate(task.id)
  }

  const showX = task.status === 'pending' || task.status === 'cancelled'
  const showRestore = task.status === 'cancelled'
  const isError = cancelMutation.isError || deleteMutation.isError || restoreMutation.isError
  const errorText =
    restoreMutation.isError ? 'Восстановление не удалось' :
    task.status === 'pending' ? 'Отмена не удалась' : 'Удаление не удалось'

  const cellAddress = `${task.dest_cell_x} · ${task.dest_cell_y} · ${task.dest_cell_z}`
  const date = new Date(task.created_at).toLocaleDateString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
  })

  return (
    <li style={task.status === 'in_progress' ? { borderLeft: '3px solid #00ffff', paddingLeft: '4px' } : {}}>
      <div className="flex items-center w-full py-2">
        <div className="flex items-center w-28 flex-shrink-0">
          <TaskStatusDot status={task.status} />
          <span className="text-xs" style={{ color: '#8ab4f8' }}>{STATUS_LABEL[task.status]}</span>
        </div>
        <span className="flex-1" style={{ color: '#e0f0ff', fontSize: '14px', fontWeight: 600 }}>
          {cellAddress}
        </span>
        <span className="w-20 flex-shrink-0 text-right" style={{ color: '#6a8aaa', fontSize: '12px' }}>
          {date}
        </span>
        <div className="w-14 flex-shrink-0 flex items-center gap-1 justify-end">
          {showRestore && (
            <button
              aria-label={`Восстановить задачу ${task.id}`}
              disabled={isBusy}
              onClick={() => restoreMutation.mutate(task.id)}
              style={{ color: '#6a8aaa' }}
              className="p-1 rounded disabled:opacity-40 transition-colors hover:bg-[rgba(0,255,255,0.1)]"
            >
              {restoreMutation.isPending ? '…' : <RotateCcw size={14} />}
            </button>
          )}
          {showX && (
            <button
              aria-label={task.status === 'pending' ? `Отменить задачу ${task.id}` : `Удалить задачу ${task.id}`}
              disabled={isBusy}
              onClick={handleX}
              style={{ color: '#ff3366' }}
              className="p-1 rounded disabled:opacity-40 transition-colors hover:bg-[rgba(255,51,102,0.1)]"
            >
              {(cancelMutation.isPending || deleteMutation.isPending) ? '…' : <X size={16} />}
            </button>
          )}
        </div>
      </div>
      {isError && (
        <p className="text-xs pl-6" style={{ color: '#ff3366' }}>{errorText} — попробуйте снова</p>
      )}
    </li>
  )
}
