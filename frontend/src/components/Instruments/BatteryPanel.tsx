import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

interface BatteryPanelProps {
  level: number
  voltage: number
  current: number
  remaining: string
}

function indicatorClass(level: number): string {
  if (level >= 40) return '[&>div]:bg-cyan'
  if (level >= 20) return '[&>div]:bg-accent-warn'
  return '[&>div]:bg-accent-err'
}

function labelColor(level: number): string {
  if (level >= 40) return '#00ffff'
  if (level >= 20) return '#ffaa00'
  return '#ff3366'
}

export default function BatteryPanel({ level, voltage, current, remaining }: BatteryPanelProps) {
  return (
    <div
      className="rounded-2xl p-3 flex-shrink-0"
      style={{
        background: 'rgba(0,0,0,0.4)',
        backdropFilter: 'blur(5px)',
        WebkitBackdropFilter: 'blur(5px)',
        border: '1px solid rgba(0,255,255,0.1)',
      }}
    >
      <div className="flex items-center justify-between mb-2">
        <h3 style={{ borderLeft: '3px solid #00ffff', paddingLeft: '10px', color: '#8ab4f8', fontSize: '14px', fontWeight: 600 }}>
          Батарея
        </h3>
        <span style={{ color: labelColor(level), fontFamily: "'Courier New', monospace", fontWeight: 700, fontSize: '16px' }}>
          {level}%
        </span>
      </div>

      <Progress value={level} className={cn('mb-2', indicatorClass(level))} />

      <div className="flex justify-between">
        <div>
          <p style={{ color: '#6a8aaa', fontSize: '10px' }}>Напряжение</p>
          <p style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '13px' }}>{voltage.toFixed(1)} В</p>
        </div>
        <div>
          <p style={{ color: '#6a8aaa', fontSize: '10px' }}>Остаток</p>
          <p style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '13px' }}>{remaining}</p>
        </div>
        <div>
          <p style={{ color: '#6a8aaa', fontSize: '10px' }}>Ток</p>
          <p style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '13px' }}>{current.toFixed(1)} А</p>
        </div>
      </div>
    </div>
  )
}
