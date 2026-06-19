import type { Caso } from '../types'

const estadoLabel: Record<string, string> = {
  realizado: 'Realizado',
  en_desarrollo: 'En desarrollo',
  por_comenzar: 'Por comenzar',
}

const estadoClass: Record<string, string> = {
  realizado: 'bg-emerald-500/20 text-emerald-300 ring-emerald-500/30',
  en_desarrollo: 'bg-blue-500/20 text-blue-300 ring-blue-500/30',
  por_comenzar: 'bg-amber-500/20 text-amber-300 ring-amber-500/30',
}

const fmtUsd = (n: number) =>
  new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n)

export function PipelineBoard({ casos }: { casos: Caso[] }) {
  const columnas: Array<{ key: Caso['estado']; title: string }> = [
    { key: 'por_comenzar', title: 'Por comenzar' },
    { key: 'en_desarrollo', title: 'En desarrollo' },
    { key: 'realizado', title: 'Realizados' },
  ]

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      {columnas.map((col) => {
        const items = casos.filter((c) => c.estado === col.key)
        return (
          <div key={col.key} className="rounded-2xl border border-top-border bg-top-card/60 p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="font-semibold text-white">{col.title}</h3>
              <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-xs text-slate-300">
                {items.length}
              </span>
            </div>
            <div className="space-y-3 max-h-[420px] overflow-y-auto pr-1">
              {items.map((c) => (
                <article
                  key={`${c.listado}-${c.reporte}`}
                  className="rounded-xl border border-top-border bg-slate-900/50 p-3 transition hover:border-blue-500/40"
                >
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="text-sm font-medium leading-snug text-slate-100">{c.reporte}</h4>
                    <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] ring-1 ${estadoClass[c.estado]}`}>
                      {estadoLabel[c.estado]}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-slate-400">{c.usuario || c.origen || '—'}</p>
                  <div className="mt-2 grid grid-cols-3 gap-1 text-[10px]">
                    <div>
                      <span className="text-slate-500">Invertimos</span>
                      <p className="font-semibold text-blue-300">{fmtUsd(c.kpi.inversion_usd)}</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Liberamos</span>
                      <p className="font-semibold text-emerald-300">{fmtUsd(c.kpi.ahorro_anual_usd)}</p>
                    </div>
                    <div>
                      <span className="text-slate-500">Evitamos</span>
                      <p className="font-semibold text-amber-300">
                        {c.comparativo.ahorro_vs_app_real != null
                          ? fmtUsd(c.comparativo.ahorro_vs_app_real)
                          : '—'}
                      </p>
                    </div>
                  </div>
                </article>
              ))}
              {items.length === 0 && (
                <p className="py-8 text-center text-sm text-slate-500">Sin casos en esta columna</p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export function CasosTable({ casos }: { casos: Caso[] }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-top-border bg-top-card/80">
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-900/80 text-xs uppercase tracking-wider text-slate-400">
            <tr>
              <th className="px-4 py-3">Caso</th>
              <th className="px-4 py-3">Usuario</th>
              <th className="px-4 py-3">Estado</th>
              <th className="px-4 py-3">Hs inv.</th>
              <th className="px-4 py-3">Inversión</th>
              <th className="px-4 py-3">Hs ahorro/año</th>
              <th className="px-4 py-3">Ahorro USD/año</th>
              <th className="px-4 py-3">ROI</th>
            </tr>
          </thead>
          <tbody>
            {casos.map((c) => (
              <tr key={`${c.listado}-${c.reporte}`} className="border-t border-top-border/70 hover:bg-slate-900/40">
                <td className="px-4 py-3 font-medium text-slate-100">{c.reporte}</td>
                <td className="px-4 py-3 text-slate-300">{c.usuario || '—'}</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-0.5 text-xs ring-1 ${estadoClass[c.estado]}`}>
                    {estadoLabel[c.estado]}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-300">{c.kpi.horas_invertidas}</td>
                <td className="px-4 py-3 text-blue-300">{fmtUsd(c.kpi.inversion_usd)}</td>
                <td className="px-4 py-3 text-slate-300">{c.kpi.horas_ahorradas_anual}</td>
                <td className="px-4 py-3 text-emerald-300">{fmtUsd(c.kpi.ahorro_anual_usd)}</td>
                <td className={`px-4 py-3 font-semibold ${c.kpi.roi_usd >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {fmtUsd(c.kpi.roi_usd)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
