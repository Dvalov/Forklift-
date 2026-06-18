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
          <span className="text-xs text-gray-400 mb-1">{label}</span>
          <span className="text-gray-100 font-mono text-sm">{value.toFixed(2)}m</span>
        </div>
      ))}
    </div>
  )
}
