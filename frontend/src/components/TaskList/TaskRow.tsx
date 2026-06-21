import type { Task } from '@/types/api'
import { Button } from '@/components/ui/button'
import TaskStatusDot from './TaskStatusDot'
import { useCancelTask } from './useCancelTask'

interface TaskRowProps {
  task: Task
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
        <TaskStatusDot status={task.status} />
        <span className="flex-1 text-sm font-semibold text-gray-100">{cellAddress}</span>
        <span className="ml-auto text-xs text-gray-400">{date}</span>
        {task.status === 'pending' && (
          <Button
            variant="destructive"
            size="sm"
            className="ml-2"
            aria-label={`Cancel task ${task.id}`}
            disabled={cancelMutation.isPending}
            onClick={() => cancelMutation.mutate(task.id)}
          >
            {cancelMutation.isPending ? '…' : 'Cancel Task'}
          </Button>
        )}
      </div>
      {cancelMutation.isError && (
        <p className="text-xs text-danger pl-6">Cancel failed — try again</p>
      )}
    </li>
  )
}
