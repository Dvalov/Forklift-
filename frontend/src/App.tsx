import { useState } from 'react'
import ForkliftStatusPanel from '@/components/ForkliftStatus/ForkliftStatusPanel'
import TaskListPanel from '@/components/TaskList/TaskListPanel'
import TaskCreationForm from '@/components/TaskCreation/TaskCreationForm'
import InstrumentPanel from '@/components/Instruments/InstrumentPanel'

function App() {
  const [activeTab, setActiveTab] = useState<'tasks' | 'instruments'>('tasks')

  return (
    <div
      className="flex flex-col h-screen overflow-hidden"
      style={{ background: 'linear-gradient(135deg, #0a0e1a 0%, #141b2d 50%, #0d1525 100%)' }}
    >
      {/* Tab content area */}
      <div className="flex-1 overflow-y-auto">
        {/* Задачи tab */}
        <div className={activeTab === 'tasks' ? 'block' : 'hidden'}>
          <div className="flex flex-col gap-4 p-4">
            <ForkliftStatusPanel />
            <TaskCreationForm />
            <TaskListPanel />
          </div>
        </div>

        {/* Приборы tab */}
        <div className={activeTab === 'instruments' ? 'block' : 'hidden'}>
          <InstrumentPanel />
        </div>
      </div>

      {/* Tab bar */}
      <nav
        className="h-14 flex w-full"
        style={{ borderTop: '1px solid rgba(0,255,255,0.2)', background: 'rgba(0,0,0,0.4)' }}
      >
        <button
          className="flex-1 flex items-center justify-center text-sm transition-colors"
          style={
            activeTab === 'tasks'
              ? { borderTop: '2px solid #00ffff', color: '#8ab4f8', fontWeight: 600, background: 'rgba(18,28,46,0.85)' }
              : { color: '#6a8aaa', fontWeight: 400 }
          }
          onClick={() => setActiveTab('tasks')}
        >
          Задачи
        </button>
        <button
          className="flex-1 flex items-center justify-center text-sm transition-colors"
          style={
            activeTab === 'instruments'
              ? { borderTop: '2px solid #00ffff', color: '#8ab4f8', fontWeight: 600, background: 'rgba(18,28,46,0.85)' }
              : { color: '#6a8aaa', fontWeight: 400 }
          }
          onClick={() => setActiveTab('instruments')}
        >
          Приборы
        </button>
      </nav>
    </div>
  )
}

export default App
