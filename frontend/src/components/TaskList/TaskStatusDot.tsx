import type { Task } from '@/types/api'

interface TaskStatusDotProps {
  status: Task['status']
}

const dotColorMap: Record<Task['status'], { backgroundColor: string }> = {
  pending:     { backgroundColor: '#8ab4f8' },
  in_progress: { backgroundColor: '#00ffff' },
  completed:   { backgroundColor: '#6a8aaa' },
  cancelled:   { backgroundColor: '#6a8aaa' },
  failed:      { backgroundColor: '#ff3366' },
}

export default function TaskStatusDot({ status }: TaskStatusDotProps) {
  return (
    <span
      aria-hidden="true"
      className="flex-shrink-0 self-center w-2 h-2 rounded-full mr-2"
      style={dotColorMap[status]}
    />
  )
}
