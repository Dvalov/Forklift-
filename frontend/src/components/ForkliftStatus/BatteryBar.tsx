import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

function indicatorClass(level: number): string {
  if (level >= 60) return '[&>div]:bg-cyan'
  if (level >= 20) return '[&>div]:bg-accent-warn'
  return '[&>div]:bg-accent-err'
}

function labelColor(level: number): string {
  if (level >= 60) return '#00ffff'
  if (level >= 20) return '#ffaa00'
  return '#ff3366'
}

export default function BatteryBar({ level }: { level: number }) {
  return (
    <div className="flex items-center gap-3">
      <Progress value={level} className={cn('flex-1', indicatorClass(level))} />
      <span
        className="text-sm w-10 text-right font-mono"
        style={{ color: labelColor(level) }}
      >
        {level}%
      </span>
    </div>
  )
}
