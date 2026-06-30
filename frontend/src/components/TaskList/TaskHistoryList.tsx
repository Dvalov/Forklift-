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
        <div className="h-8 animate-pulse rounded mb-2" style={{ background: 'rgba(0,255,255,0.05)' }} />
        <div className="h-8 animate-pulse rounded mb-2" style={{ background: 'rgba(0,255,255,0.05)' }} />
        <div className="h-8 animate-pulse rounded mb-2" style={{ background: 'rgba(0,255,255,0.05)' }} />
      </>
    )
  } else if (isError && !data) {
    content = (
      <p className="text-sm" style={{ color: '#ff3366' }}>
        Не удалось загрузить историю. Проверьте соединение.
      </p>
    )
  } else if (isError && data) {
    content = (
      <ul role="list" className="divide-y divide-[rgba(0,255,255,0.05)]">
        {historyTasks.map(t => (
          <TaskRow key={t.id} task={t} />
        ))}
      </ul>
    )
  } else if (data && historyTasks.length === 0) {
    content = (
      <div className="py-2">
        <p className="text-sm" style={{ color: '#8ab4f8' }}>История пуста</p>
        <p className="text-xs" style={{ color: '#6a8aaa' }}>Завершённые задачи появятся здесь</p>
      </div>
    )
  } else {
    content = (
      <ul role="list" className="divide-y divide-[rgba(0,255,255,0.05)]">
        {historyTasks.map(t => (
          <TaskRow key={t.id} task={t} />
        ))}
      </ul>
    )
  }

  return (
    <div
      className="rounded-2xl p-4"
      style={{
        background: 'rgba(0,0,0,0.4)',
        backdropFilter: 'blur(5px)',
        WebkitBackdropFilter: 'blur(5px)',
        border: '1px solid rgba(0,255,255,0.1)',
      }}
    >
      <section>
        <h2
          className="mb-3"
          style={{
            borderLeft: '3px solid #00ffff',
            paddingLeft: '12px',
            color: '#8ab4f8',
            fontSize: '16px',
            fontWeight: 600,
            lineHeight: 1.2,
          }}
        >
          История
        </h2>
        <div
          className="flex items-center w-full pb-1 mb-1 text-xs"
          style={{ borderBottom: '1px solid rgba(0,255,255,0.1)', color: '#6a8aaa' }}
        >
          <span className="w-28 flex-shrink-0">Статус</span>
          <span className="flex-1">Ячейка</span>
          <span className="w-20 flex-shrink-0 text-right">Дата</span>
          <span className="w-14 flex-shrink-0" />
        </div>
        {content}
      </section>
    </div>
  )
}
