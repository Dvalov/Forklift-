import React from 'react'
import ActiveTaskList from './ActiveTaskList'
import TaskHistoryList from './TaskHistoryList'

class TaskListErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true }
  }

  render() {
    if (this.state.hasError) {
      return (
        <p className="text-sm p-4" style={{ color: '#ff3366' }}>
          Панель задач недоступна
        </p>
      )
    }
    return this.props.children
  }
}

export default function TaskListPanel() {
  return (
    <TaskListErrorBoundary>
      <div className="flex flex-col gap-4">
        <ActiveTaskList />
        <TaskHistoryList />
      </div>
    </TaskListErrorBoundary>
  )
}
