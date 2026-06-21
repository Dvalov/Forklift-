import ForkliftStatusPanel from '@/components/ForkliftStatus/ForkliftStatusPanel'
import TaskListPanel from '@/components/TaskList/TaskListPanel'

function App() {
  return (
    <div className="flex h-screen bg-surface text-gray-100 overflow-hidden">
      {/* Left panel — Tasks (60%) */}
      <aside className="w-3/5 bg-panel flex flex-col border-r border-gray-800 overflow-y-auto">
        <header className="px-6 py-4 border-b border-gray-800">
          <h1 className="text-lg font-semibold text-gray-100">Tasks</h1>
        </header>
        <div className="flex-1 overflow-y-auto">
          <TaskListPanel />
        </div>
      </aside>

      {/* Right panel — Forklift Status (40%) */}
      <main className="w-2/5 bg-panel flex flex-col overflow-y-auto">
        <header className="px-6 py-4 border-b border-gray-800">
          <h1 className="text-lg font-semibold text-gray-100">Forklift Status</h1>
        </header>
        <div className="flex-1">
          <ForkliftStatusPanel />
        </div>
      </main>
    </div>
  )
}

export default App
