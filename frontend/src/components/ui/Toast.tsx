import { useEffect } from 'react'

interface ToastProps {
  message: string
  visible: boolean
  onHide: () => void
  duration?: number
}

export default function Toast({ message, visible, onHide, duration = 3000 }: ToastProps) {
  useEffect(() => {
    if (!visible) return
    const t = setTimeout(onHide, duration)
    return () => clearTimeout(t)
  }, [visible, duration, onHide])

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 24,
        right: 24,
        zIndex: 9999,
        background: 'rgba(0,255,255,0.12)',
        border: '1px solid rgba(0,255,255,0.3)',
        borderRadius: 12,
        padding: '12px 20px',
        color: '#e0f0ff',
        fontSize: 14,
        fontWeight: 500,
        opacity: visible ? 1 : 0,
        pointerEvents: visible ? 'auto' : 'none',
        transition: 'opacity 0.3s ease',
      }}
    >
      {message}
    </div>
  )
}
