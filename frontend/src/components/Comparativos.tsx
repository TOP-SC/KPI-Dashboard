import { useEffect, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { Caso, DashboardData } from '../types'
import { ChartTooltip, fmtUsd } from './ChartTooltip'
import { StatCard } from './Dashboard'

const veredictoStyle: Record<string, string> = {
  pro_top: 'bg-emerald-500/20 text-emerald-300 ring-emerald-500/40',
  alerta_app: 'bg-amber-500/20 text-amber-300 ring-amber-500/40',
  neutro: 'bg-slate-500/20 text-slate-300 ring-slate-500/40',
}

const veredictoLabel: Record<string, string> = {
  pro_top: 'Pro TOP',
  alerta_app: 'Revisar app',
  neutro: 'Neutro',
}

export function ComparativosView({ data }: { data: DashboardData }) {
  const { parametros, resumen, casos } = data
  const horizonte = parametros.horizonte_app_anios
  const horizonteLabel = `${horizonte} años`
  const [detalle, setDetalle] = useState<Caso | null>(null)

  const chartData = casos
    .filter((c) => c.kpi.inversion_usd > 0 || c.comparativo.freelancer_total_usd > 0)
    .map((c) => ({
      name: c.reporte.length > 16 ? `${c.reporte.slice(0, 16)}…` : c.reporte,
      fullName: c.reporte,
      top: c.kpi.inversion_usd,
      freelancer: c.comparativo.freelancer_total_usd,
      empresa: c.comparativo.empresa_total_usd,
      app: c.comparativo.app_costo_real_usd ?? c.comparativo.app_mercado_usd_horizonte ?? 0,
    }))
    .slice(0, 12)

  return (
    <div className="space-y-8">
      <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Valor conocimiento interno"
          value={fmtUsd(resumen.comparativo_total.valor_conocimiento_interno_usd)}
          sub="Discovery TOP acumulado"
          accent="bg-cyan-500"
        />
        <StatCard
          label="Ahorro vs Freelancer"
          value={fmtUsd(resumen.comparativo_total.ahorro_vs_freelancer_usd)}
          sub="Costo externo − TOP"
          accent="bg-purple-500"
        />
        <StatCard
          label="Ahorro vs Empresa"
          value={fmtUsd(resumen.comparativo_total.ahorro_vs_empresa_usd)}
          sub={`USD ${parametros.tarifa_empresa_usd_h}/h + discovery`}
          accent="bg-amber-500"
        />
        <StatCard
          label={`Ahorro vs App real (${horizonteLabel})`}
          value={fmtUsd(resumen.comparativo_total.ahorro_vs_app_real_usd)}
          sub="Licencia + brecha − TOP"
          accent="bg-emerald-500"
        />
      </section>

      <div className="rounded-2xl border border-top-border bg-top-card/80 p-5">
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
          Inversión TOP vs alternativas externas
        </h3>
        <ResponsiveContainer width="100%" height={380}>
          <BarChart data={chartData} margin={{ bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="name" tick={{ fill: '#e2e8f0', fontSize: 10 }} angle={-25} textAnchor="end" height={80} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={(v) => fmtUsd(v).replace('US$', '$')} />
            <Tooltip content={<ChartTooltip />} labelFormatter={(_, p) => p?.[0]?.payload?.fullName ?? ''} />
            <Legend wrapperStyle={{ color: '#cbd5e1' }} />
            <Bar dataKey="top" name="Inversión TOP" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="freelancer" name="Freelancer" fill="#a855f7" radius={[4, 4, 0, 0]} />
            <Bar dataKey="empresa" name="Empresa dev." fill="#f59e0b" radius={[4, 4, 0, 0]} />
            <Bar dataKey="app" name={`App costo real (${horizonteLabel})`} fill="#22c55e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <ComparativosTable casos={casos} horizonteLabel={horizonteLabel} onDetalle={setDetalle} />

      {detalle && (
        <CasoDetalleModal caso={detalle} horizonteLabel={horizonteLabel} onClose={() => setDetalle(null)} />
      )}
    </div>
  )
}

function ComparativosTable({
  casos,
  horizonteLabel,
  onDetalle,
}: {
  casos: Caso[]
  horizonteLabel: string
  onDetalle: (c: Caso) => void
}) {
  return (
    <div className="overflow-hidden rounded-2xl border border-top-border bg-top-card/80">
      <p className="border-b border-top-border/70 px-4 py-2 text-xs text-slate-500">
        Click en una fila para ver discovery, brechas y detalle completo
      </p>
      <div className="overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="bg-slate-900/80 text-xs uppercase tracking-wider text-slate-400">
            <tr>
              <th className="px-4 py-3">Caso</th>
              <th className="px-4 py-3">Compl.</th>
              <th className="px-4 py-3">Discovery</th>
              <th className="px-4 py-3">Inv. TOP</th>
              <th className="px-4 py-3">Freelancer</th>
              <th className="px-4 py-3">Empresa</th>
              <th className="px-4 py-3">App real ({horizonteLabel})</th>
              <th className="px-4 py-3">Veredicto</th>
            </tr>
          </thead>
          <tbody>
            {casos.map((c) => (
              <tr
                key={`${c.listado}-${c.reporte}`}
                onClick={() => onDetalle(c)}
                className="cursor-pointer border-t border-top-border/70 transition hover:bg-slate-900/50"
              >
                <td className="px-4 py-3">
                  <p className="font-medium text-slate-100">{c.reporte}</p>
                </td>
                <td className="px-4 py-3 capitalize text-slate-400">{c.comparativo.complejidad}</td>
                <td className="px-4 py-3 whitespace-nowrap text-cyan-300">
                  {c.comparativo.discovery_horas_top}h
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-blue-300">
                  {fmtUsd(c.kpi.inversion_usd)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-purple-300">
                  {fmtUsd(c.comparativo.freelancer_total_usd)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-amber-300">
                  {fmtUsd(c.comparativo.empresa_total_usd)}
                </td>
                <td className="px-4 py-3">
                  {c.comparativo.app_costo_real_usd != null ? (
                    <div className="max-w-[10rem]">
                      {c.comparativo.app_mercado_nombre_corto && (
                        <p className="truncate text-xs text-emerald-200/90" title={c.comparativo.app_mercado_nombre_corto}>
                          {c.comparativo.app_mercado_nombre_corto}
                        </p>
                      )}
                      <span className="text-emerald-300">{fmtUsd(c.comparativo.app_costo_real_usd)}</span>
                    </div>
                  ) : (
                    '—'
                  )}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`whitespace-nowrap rounded-full px-2 py-0.5 text-xs ring-1 ${veredictoStyle[c.comparativo.veredicto]}`}
                  >
                    {veredictoLabel[c.comparativo.veredicto]}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function CasoDetalleModal({
  caso,
  horizonteLabel,
  onClose,
}: {
  caso: Caso
  horizonteLabel: string
  onClose: () => void
}) {
  const c = caso
  const comp = c.comparativo

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
      onClick={onClose}
      role="presentation"
    >
      <div
        className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-top-border bg-slate-900 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="detalle-titulo"
      >
        <div className="sticky top-0 flex items-start justify-between gap-4 border-b border-top-border bg-slate-900/95 px-6 py-4 backdrop-blur">
          <div>
            <h2 id="detalle-titulo" className="text-xl font-semibold text-white">
              {c.reporte}
            </h2>
            <div className="mt-2 flex flex-wrap gap-2">
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs ring-1 ${veredictoStyle[comp.veredicto]}`}
              >
                {veredictoLabel[comp.veredicto]}
              </span>
              <span className="rounded-full bg-slate-800 px-2.5 py-0.5 text-xs capitalize text-slate-300">
                {comp.complejidad}
              </span>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white"
            aria-label="Cerrar"
          >
            ✕
          </button>
        </div>

        <div className="space-y-6 px-6 py-5">
          <p className="text-sm leading-relaxed text-slate-300">{comp.veredicto_texto}</p>

          <section>
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Comparativa de costos
            </h3>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <DetalleKpi label="Inversión TOP" value={fmtUsd(c.kpi.inversion_usd)} color="text-blue-300" />
              <DetalleKpi label="Freelancer" value={fmtUsd(comp.freelancer_total_usd)} color="text-purple-300" />
              <DetalleKpi label="Empresa dev." value={fmtUsd(comp.empresa_total_usd)} color="text-amber-300" />
              <DetalleKpi
                label={`App real (${horizonteLabel})`}
                value={comp.app_costo_real_usd != null ? fmtUsd(comp.app_costo_real_usd) : '—'}
                color="text-emerald-300"
              />
            </div>
          </section>

          <section>
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Discovery y conocimiento
            </h3>
            <div className="rounded-xl bg-slate-800/50 p-4 text-sm">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                <DetalleKpi label="Discovery TOP" value={`${comp.discovery_horas_top}h`} color="text-cyan-300" />
                <DetalleKpi label="Valor discovery" value={fmtUsd(comp.discovery_usd_top)} color="text-cyan-300" />
                <DetalleKpi
                  label="Conocimiento total"
                  value={`${comp.horas_conocimiento_total}h`}
                  color="text-white"
                />
              </div>
              <p className="mt-3 text-slate-400">{comp.discovery_razon}</p>
            </div>
          </section>

          {comp.app_mercado_nombre_corto && (
            <section>
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
                Alternativa comercial (mercado)
              </h3>
              <div className="rounded-xl bg-slate-800/50 p-4 text-sm">
                <p className="font-medium text-emerald-200">{comp.app_mercado_nombre_corto}</p>
                {comp.app_mercado_pricing_ref && (
                  <p className="mt-1 text-slate-400">{comp.app_mercado_pricing_ref}</p>
                )}
                {comp.app_mercado_match_por && (
                  <p className="mt-2 text-xs text-slate-500">{comp.app_mercado_match_por}</p>
                )}
                {comp.app_mercado_alternativas?.length > 0 && (
                  <p className="mt-2 text-xs text-slate-500">
                    Similares: {comp.app_mercado_alternativas.join(' · ')}
                  </p>
                )}
                <p className="mt-2 text-xs text-cyan-400/80">{comp.fuente_app}</p>
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <DetalleKpi
                    label={`Licencia ${horizonteLabel}`}
                    value={fmtUsd(comp.app_mercado_usd_horizonte ?? 0)}
                    color="text-slate-300"
                  />
                  <DetalleKpi
                    label="Brecha adaptación"
                    value={comp.brecha_logica_app_usd != null ? fmtUsd(comp.brecha_logica_app_usd) : '—'}
                    color="text-slate-300"
                  />
                </div>
              </div>
            </section>
          )}

          <section>
            <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Ahorro vs alternativas
            </h3>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
              <AhorroItem
                label="vs Freelancer"
                value={comp.ahorro_vs_freelancer}
              />
              <AhorroItem label="vs Empresa" value={comp.ahorro_vs_empresa} />
              <AhorroItem label="vs App real" value={comp.ahorro_vs_app_real} />
            </div>
          </section>

          {(c.usuario || c.origen || c.herramienta) && (
            <section>
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Caso</h3>
              <dl className="grid grid-cols-1 gap-2 text-sm sm:grid-cols-2">
                {c.usuario && (
                  <>
                    <dt className="text-slate-500">Usuario</dt>
                    <dd className="text-slate-200">{c.usuario}</dd>
                  </>
                )}
                {c.origen && (
                  <>
                    <dt className="text-slate-500">Origen</dt>
                    <dd className="text-slate-200">{c.origen}</dd>
                  </>
                )}
                {c.herramienta && (
                  <>
                    <dt className="text-slate-500">Herramienta</dt>
                    <dd className="text-slate-200">{c.herramienta}</dd>
                  </>
                )}
                {c.kpi.horas_invertidas > 0 && (
                  <>
                    <dt className="text-slate-500">Hs invertidas</dt>
                    <dd className="text-slate-200">{c.kpi.horas_invertidas}</dd>
                  </>
                )}
              </dl>
            </section>
          )}
        </div>
      </div>
    </div>
  )
}

function DetalleKpi({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div>
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`mt-0.5 font-semibold ${color}`}>{value}</p>
    </div>
  )
}

function AhorroItem({ label, value }: { label: string; value: number | null }) {
  if (value == null) return null
  return (
    <div className="rounded-lg bg-slate-800/50 px-3 py-2">
      <p className="text-xs text-slate-500">{label}</p>
      <p className={`font-semibold ${value >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
        {value >= 0 ? '+' : ''}
        {fmtUsd(value)}
      </p>
    </div>
  )
}
