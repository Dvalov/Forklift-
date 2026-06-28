import { KeyboardEvent, useRef, useLayoutEffect, useState } from 'react'
import { cn } from '@/lib/utils'
import type { Cell } from '@/types/api'

const SLOTS = 3
const SLOT_POSITIONS = [0, 4, 8]

function formatMask(digits: string): string {
  return [0, 1, 2].map(i => digits[i] ?? '_').join(' · ')
}

function nextCursorPos(digitCount: number): number {
  return digitCount < SLOTS ? SLOT_POSITIONS[digitCount] : 9
}

interface Props {
  digits: string
  onChange: (digits: string) => void
  suggestions: Cell[]
  onSelectSuggestion: (cell: Cell) => void
  disabled?: boolean
  hasError?: boolean
}

export default function CellMaskInput({
  digits,
  onChange,
  suggestions,
  onSelectSuggestion,
  disabled,
  hasError,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [focused, setFocused] = useState(false)

  useLayoutEffect(() => {
    const input = inputRef.current
    if (!input || document.activeElement !== input) return
    const pos = nextCursorPos(digits.length)
    input.setSelectionRange(pos, pos)
  }, [digits])

  function snapCursor() {
    const input = inputRef.current
    if (!input) return
    const pos = nextCursorPos(digits.length)
    input.setSelectionRange(pos, pos)
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (/^\d$/.test(e.key)) {
      e.preventDefault()
      if (digits.length < SLOTS) onChange(digits + e.key)
    } else if (e.key === 'Backspace') {
      e.preventDefault()
      onChange(digits.slice(0, -1))
    }
  }

  const showDropdown = focused && suggestions.length > 0 && digits.length > 0

  return (
    <div className="relative">
      <input
        ref={inputRef}
        type="text"
        inputMode="numeric"
        value={formatMask(digits)}
        onKeyDown={handleKeyDown}
        onChange={() => {}}
        onClick={() => { snapCursor(); setFocused(true) }}
        onFocus={() => { snapCursor(); setFocused(true) }}
        onBlur={() => setFocused(false)}
        disabled={disabled}
        className={cn(
          'flex h-9 w-full rounded-md border bg-panel px-3 py-2',
          'text-sm font-mono tracking-widest text-gray-100',
          'focus:outline-none focus:ring-1',
          'disabled:cursor-not-allowed disabled:opacity-50',
          hasError
            ? 'border-danger/70 focus:ring-danger/50'
            : 'border-gray-700 focus:ring-accent',
        )}
      />

      {showDropdown && (
        <ul className="absolute z-50 mt-1 w-full max-h-48 overflow-y-auto rounded-md border border-gray-700 bg-panel shadow-md">
          {suggestions.map(cell => (
            <li key={cell.id}>
              <button
                type="button"
                onMouseDown={e => {
                  e.preventDefault()
                  onSelectSuggestion(cell)
                  setFocused(false)
                }}
                disabled={!cell.available}
                className={cn(
                  'w-full px-3 py-2 text-left text-sm font-mono flex items-center justify-between',
                  cell.available
                    ? 'text-gray-100 hover:bg-gray-800 cursor-pointer'
                    : 'text-gray-500 cursor-default',
                )}
              >
                <span className="tracking-widest">
                  {cell.x} · {cell.y} · {cell.z}
                </span>
                {!cell.available && (
                  <span className="text-xs text-gray-600">unavailable</span>
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
