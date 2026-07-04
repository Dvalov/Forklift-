interface BottomStatusBarProps {
  moving: boolean
  cargo: boolean
  navigation: boolean
  diagnostics: boolean
  stopValve: boolean
}

export default function BottomStatusBar({ moving, cargo, navigation, diagnostics, stopValve }: BottomStatusBarProps) {
  const indicators = [
    { label: 'Движение', active: moving },
    { label: 'Груз', active: cargo },
    { label: 'Навигация', active: navigation },
    { label: 'Диагностика', active: diagnostics },
    { label: 'Стоп-кран', active: stopValve, danger: true },
  ]

  return (
    <div
      className="rounded-2xl p-4"
      style={{ background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(5px)', WebkitBackdropFilter: 'blur(5px)', border: '1px solid rgba(0,255,255,0.1)' }}
    >
      <h3 style={{ borderLeft: '3px solid #00ffff', paddingLeft: '12px', color: '#8ab4f8', fontSize: '16px', fontWeight: 600, marginBottom: '12px' }}>
        Статус системы
      </h3>
      <div className="flex gap-2 flex-wrap">
        {indicators.map(({ label, active, danger }) => {
          let style: React.CSSProperties
          if (active && danger) {
            style = { background: 'rgba(255,51,102,0.2)', color: '#ff3366', border: '1px solid rgba(255,51,102,0.4)', fontWeight: 600 }
          } else if (active) {
            style = { background: 'rgba(0,255,255,0.2)', color: '#00ffff', border: '1px solid rgba(0,255,255,0.4)', fontWeight: 600 }
          } else {
            style = { background: 'rgba(0,0,0,0.3)', color: '#6a8aaa', border: '1px solid rgba(106,138,170,0.3)' }
          }
          return (
            <span key={label} className="px-2 py-1 rounded text-xs font-medium" style={style}>
              {label}
            </span>
          )
        })}
      </div>
    </div>
  )
}
