import type { Caso } from '../types'
import { fmtUsd } from './ChartTooltip'

export function filtrarCasosRevisar(casos: Caso[]): Caso[] {
  return casos
    .filter((c) => c.kpi.roi_usd < 0 || c.alerta_roi)
    .sort((a, b) => a.kpi.roi_usd - b.kpi.roi_usd)
}

export function CasosRevisarView({ casos }: { casos: Caso[] }) {
  const revisar = filtrarCasosRevisar(casos)

  if (!revisar.length) {
    return (
      <div className="rounded-2xl border border-emerald-500/30 bg-emerald-950/20 p-8 text-center">
        <p className="text-lg font-semibold text-emerald-200">Todo en orden</p>
        <p className="mt-2 text-sm text-emerald-100/70">
          No hay casos con ROI negativo ni alertas de datos pendientes.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-amber-500/30 bg-amber-950/20 p-5">
        <h2 className="text-xl font-semibold text-amber-200">
          Casos a revisar ({revisar.length})
        </h2>
        <p className="mt-1 text-sm text-amber-100/70">
          ROI negativo o datos pendientes de validar en la sheet. Revisá estos casos antes de
          presentar el tablero.
        </p>
      </div>

      <ul className="space-y-3">
        {revisar.map((c) => (
          <li
            key={`${c.listado}-${c.reporte}`}
            className="rounded-xl border border-amber-500/20 bg-top-card/80 px-5 py-4"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="font-semibold text-white">{c.reporte}</h3>
                {c.usuario && (
                  <p className="mt-0.5 text-sm text-slate-400">{c.usuario} · {c.origen || '—'}</p>
                )}
              </div>
              <span
                className={`shrink-0 text-base font-bold ${
                  c.kpi.roi_usd >= 0 ? 'text-amber-300' : 'text-rose-400'
                }`}
              >
                ROI: {fmtUsd(c.kpi.roi_usd)}
              </span>
            </div>

            {c.alerta_roi && (
              <p className="mt-2 text-sm text-amber-100/90">{c.alerta_roi}</p>
            )}

            <div className="mt-3 flex flex-wrap gap-4 text-sm">
              <div>
                <span className="text-slate-500">Inversión</span>
                <p className="font-semibold text-blue-300">{fmtUsd(c.kpi.inversion_usd)}</p>
              </div>
              <div>
                <span className="text-slate-500">Ahorro/año</span>
                <p className="font-semibold text-emerald-300">{fmtUsd(c.kpi.ahorro_anual_usd)}</p>
              </div>
              <div>
                <span className="text-slate-500">Hs invertidas</span>
                <p className="font-semibold text-slate-200">{c.kpi.horas_invertidas}</p>
              </div>
              <div>
                <span className="text-slate-500">Hs ahorro/mes</span>
                <p className="font-semibold text-slate-200">{c.kpi.reduccion_hs_mes}</p>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
