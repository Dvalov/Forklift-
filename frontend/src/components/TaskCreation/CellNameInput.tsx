import { useState } from 'react'
import { cn } from '@/lib/utils'
import type { Cell } from '@/types/api'

interface Props {
  value: string
  onChange: (value: string) => void
  cells: Cell[]
  onSelectCell: (cell: Cell) => void
  disabled?: boolean
  hasError?: boolean
  placeholder?: string
}

function cellLabel(cell: Cell): string {
  return cell.name || `${cell.x}·${cell.y}·${cell.z}`
}

export default function CellNameInput({
  value,
  onChange,
  cells,
  onSelectCell,
  disabled,
  hasError,
  placeholder = 'Поиск ячейки...',
}: Props) {
  const [focused, setFocused] = useState(false)

  const q = value.toLowerCase()
  const suggestions =
    value.length > 0
      ? cells
          .filter(c => cellLabel(c).toLowerCase().includes(q))
          .slice(0, 12)
      : cells.slice(0, 12)

  const showDropdown = focused && (value.length > 0 ? suggestions.length > 0 : cells.length > 0)

  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={e => onChange(e.target.value)}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        disabled={disabled}
        placeholder={placeholder}
        style={{ background: 'rgba(0,0,0,0.4)', color: '#e0f0ff' }}
        className={cn(
          'flex h-9 w-full rounded-md border px-3 py-2',
          'text-sm',
          'focus:outline-none focus:ring-1',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'placeholder:text-[#6a8aaa]',
          hasError
            ? 'border-[#ff3366] focus:ring-[rgba(255,51,102,0.5)]'
            : 'border-[rgba(0,255,255,0.2)] focus:ring-[#00ffff]',
        )}
      />

      {showDropdown && (
        <ul
          className="absolute z-50 mt-1 w-full max-h-48 overflow-y-auto rounded-md shadow-md"
          style={{
            background: 'rgba(10,18,32,0.97)',
            backdropFilter: 'blur(5px)',
            border: '1px solid rgba(0,255,255,0.15)',
          }}
        >
          {suggestions.map(cell => (
            <li key={cell.id}>
              <button
                type="button"
                onMouseDown={e => {
                  e.preventDefault()
                  onSelectCell(cell)
                  setFocused(false)
                }}
                className="w-full px-3 py-2 text-left text-sm flex items-center justify-between hover:bg-[rgba(0,255,255,0.07)] cursor-pointer"
                style={{ color: '#e0f0ff' }}
              >
                <span>{cellLabel(cell)}</span>
                {cell.name && (
                  <span className="text-xs ml-2 flex-shrink-0" style={{ color: '#6a8aaa' }}>
                    {cell.x}·{cell.y}·{cell.z}
                  </span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
