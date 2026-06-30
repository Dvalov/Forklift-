export default function PositionDisplay({ x, y, z }: { x: number; y: number; z: number }) {
  const axes = [
    { label: 'X', value: x },
    { label: 'Y', value: y },
    { label: 'Z', value: z },
  ]

  return (
    <div className="grid grid-cols-3 gap-4">
      {axes.map(({ label, value }) => (
        <div key={label} className="flex flex-col items-center">
          <span className="mb-1" style={{ color: '#6a8aaa', fontSize: '12px' }}>{label}</span>
          <span style={{ color: '#e0f0ff', fontFamily: "'Courier New', monospace", fontWeight: 600, fontSize: '14px' }}>
            {value.toFixed(2)}m
          </span>
        </div>
      ))}
    </div>
  )
}
