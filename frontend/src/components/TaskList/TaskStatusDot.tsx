import type { Task } from '@/types/api'

interface TaskStatusDotProps {
  status: Task['status']
}

const dotClass: Record<Task['status'], string> = {
  pending: 'bg-warning',
  in_progress: 'bg-accent',
  completed: 'bg-success',
  cancelled: 'bg-gray-600',
  failed: 'bg-danger',
}

export default function TaskStatusDot({ status }: TaskStatusDotProps) {
  return (
    <span
      aria-hidden="true"
      className={`flex-shrink-0 self-center w-2 h-2 rounded-full mr-2 ${dotClass[status]}`}
    />
  )
}
