import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

interface BatteryPanelProps {
  level: number
  voltage: number
  current: number
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

export default function BatteryPanel({ level, voltage, current }: BatteryPanelProps) {
  return (
    <div
      className="rounded-2xl p-4"
      style={{ background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(5px)', WebkitBackdropFilter: 'blur(5px)', border: '1px solid rgba(0,255,255,0.1)' }}
    >
      <h3 style={{ borderLeft: '3px solid #00ffff', paddingLeft: '12px', color: '#8ab4f8', fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>
        Батарея
      </h3>
      <div className="flex items-center gap-3 mb-3">
        <Progress value={level} className={cn('flex-1', indicatorClass(level))} />
        <span style={{ color: labelColor(level), fontSize: '14px', fontFamily: "'Courier New', monospace", fontWeight: 600, minWidth: '40px', textAlign: 'right' }}>
          {level}%
        </span>
      </div>
      <div className="flex justify-between">
        <div className="flex items-center gap-1">
          <span style={{ color: '#6a8aaa', fontSize: '12px' }}>Напряжение:</span>
          <span style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{voltage.toFixed(1)} В</span>
        </div>
        <div className="flex items-center gap-1">
          <span style={{ color: '#6a8aaa', fontSize: '12px' }}>Ток:</span>
          <span style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>{current.toFixed(1)} А</span>
        </div>
      </div>
    </div>
  )
}
