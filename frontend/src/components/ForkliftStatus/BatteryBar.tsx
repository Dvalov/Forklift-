import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

function indicatorClass(level: number): string {
  if (level >= 60) return '[&>div]:bg-success'
  if (level >= 20) return '[&>div]:bg-warning'
  return '[&>div]:bg-danger'
}

function labelClass(level: number): string {
  if (level >= 60) return 'text-success'
  if (level >= 20) return 'text-warning'
  return 'text-danger'
}

export default function BatteryBar({ level }: { level: number }) {
  return (
    <div className="flex items-center gap-3">
      <Progress value={level} className={cn('flex-1', indicatorClass(level))} />
      <span className={cn('text-sm w-10 text-right font-mono', labelClass(level))}>
        {level}%
      </span>
    </div>
  )
}
