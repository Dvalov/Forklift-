import { useTasksQuery } from './useTasksQuery'
import TaskRow from './TaskRow'

export default function ActiveTaskList() {
  const { data, isLoading, isError } = useTasksQuery()

  const activeTasks = (data ?? [])
    .filter(t => t.status === 'pending' || t.status === 'in_progress')
    .sort((a, b) => a.created_at.localeCompare(b.created_at))
    .slice(0, 5)

  let content: React.ReactNode

  if (isLoading && !data) {
    content = (
      <>
        <div className="h-8 bg-gray-800 animate-pulse rounded mb-2" />
        <div className="h-8 bg-gray-800 animate-pulse rounded mb-2" />
        <div className="h-8 bg-gray-800 animate-pulse rounded mb-2" />
      </>
    )
  } else if (isError && !data) {
    content = <p className="text-danger text-sm">Could not load tasks — retrying</p>
  } else if (isError && data) {
    content = (
      <>
        <p className="text-warning text-xs mb-2">Task data may be outdated</p>
        <ul role="list" className="divide-y divide-gray-800">
          {activeTasks.map(t => (
            <TaskRow key={t.id} task={t} />
          ))}
        </ul>
      </>
    )
  } else if (data && activeTasks.length === 0) {
    content = (
      <div className="py-2">
        <p className="text-sm text-gray-400">No active tasks</p>
        <p className="text-xs text-gray-500">Tasks assigned to this forklift will appear here</p>
      </div>
    )
  } else {
    content = (
      <ul role="list" className="divide-y divide-gray-800">
        {activeTasks.map(t => (
          <TaskRow key={t.id} task={t} />
        ))}
      </ul>
    )
  }

  return (
    <section>
      <h2 className="text-xs font-normal text-gray-400 uppercase tracking-wide mb-2">Active</h2>
      {content}
    </section>
  )
}
