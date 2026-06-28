import { useTasksQuery } from './useTasksQuery'
import TaskRow from './TaskRow'

export default function TaskHistoryList() {
  const { data, isLoading, isError } = useTasksQuery()

  const historyTasks = (data ?? [])
    .filter(t => ['completed', 'failed', 'cancelled'].includes(t.status))
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at))
    .slice(0, 10)

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
    content = <p className="text-danger text-sm">Could not load history</p>
  } else if (isError && data) {
    content = (
      <ul role="list" className="divide-y divide-gray-800">
        {historyTasks.map(t => (
          <TaskRow key={t.id} task={t} />
        ))}
      </ul>
    )
  } else if (data && historyTasks.length === 0) {
    content = <p className="text-sm text-gray-400 py-2">No completed tasks yet</p>
  } else {
    content = (
      <ul role="list" className="divide-y divide-gray-800">
        {historyTasks.map(t => (
          <TaskRow key={t.id} task={t} />
        ))}
      </ul>
    )
  }

  return (
    <section>
      <h2 className="text-xs font-normal text-gray-400 uppercase tracking-wide mb-2">History</h2>
      <div className="flex items-center w-full pb-1 border-b border-gray-800 mb-1 text-xs text-gray-500">
        <span className="w-28 flex-shrink-0">Status</span>
        <span className="flex-1">Cell</span>
        <span className="w-20 flex-shrink-0 text-right">Date</span>
        <span className="w-14 flex-shrink-0" />
      </div>
      {content}
    </section>
  )
}
