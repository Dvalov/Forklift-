interface BottomStatusBarProps {
  moving: boolean
  cargo: boolean
  navigation: boolean
  diagnostics: boolean
  stopValve: boolean
  navigationLabel?: string
  lastDiagnostics?: string
}

export default function BottomStatusBar({
  moving,
  cargo,
  navigation,
  diagnostics,
  stopValve,
  navigationLabel = 'GPS',
  lastDiagnostics,
}: BottomStatusBarProps) {
  const indicators = [
    { label: 'Движение', value: moving ? 'АКТИВНО' : 'СТОП', dot: moving ? '#3fb950' : '#ff3366' },
    { label: 'Груз', value: cargo ? 'стабилен' : 'отсутствует', dot: cargo ? '#3fb950' : '#ffaa00' },
    { label: 'Навигация', value: navigation ? navigationLabel : 'нет сигнала', dot: navigation ? '#3fb950' : '#ff3366' },
    ...(lastDiagnostics
      ? [{ label: 'Последняя диагностика', value: lastDiagnostics, dot: diagnostics ? '#ff3366' : '#6a8aaa' }]
      : []),
    { label: 'Стоп-кран', value: stopValve ? 'АКТИВЕН' : 'ОК', dot: stopValve ? '#ff3366' : '#3fb950' },
  ]

  return (
    <div
      className="rounded-2xl px-3 py-2"
      style={{
        background: 'rgba(0,0,0,0.4)',
        backdropFilter: 'blur(5px)',
        WebkitBackdropFilter: 'blur(5px)',
        border: '1px solid rgba(0,255,255,0.1)',
      }}
    >
      <div className="flex flex-wrap gap-4 items-center">
        {indicators.map(({ label, value, dot }) => (
          <div key={label} className="flex items-center gap-2">
            <span style={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: dot, display: 'inline-block', flexShrink: 0 }} />
            <span style={{ color: '#6a8aaa', fontSize: '12px' }}>{label}:</span>
            <span style={{ color: '#e0f0ff', fontSize: '12px', fontWeight: 600 }}>{value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
