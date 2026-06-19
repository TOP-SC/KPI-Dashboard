import type { TooltipProps } from 'recharts'
import type { NameType, ValueType } from 'recharts/types/component/DefaultTooltipContent'

export const fmtUsd = (n: number) =>
  new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)

export const fmtNum = (n: number) => new Intl.NumberFormat('es-AR').format(n)

export function ChartTooltip({
  active,
  payload,
  label,
}: TooltipProps<ValueType, NameType>) {
  if (!active || !payload?.length) return null

  return (
    <div className="rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 shadow-xl">
      {label && <p className="mb-1.5 text-sm font-semibold text-white">{label}</p>}
      <ul className="space-y-1">
        {payload.map((entry) => (
          <li key={String(entry.name)} className="flex items-center gap-2 text-sm">
            <span
              className="inline-block h-2.5 w-2.5 rounded-sm"
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-slate-200">{entry.name}:</span>
            <span className="font-semibold text-white">
              {typeof entry.value === 'number' ? fmtUsd(entry.value) : entry.value}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
