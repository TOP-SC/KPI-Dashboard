import { useState } from 'react'
import type { DashboardData } from '../types'
import { fmtNum, fmtUsd } from './ChartTooltip'

type PeriodoVista = 'mes' | 'anio'

const PERIODOS: { id: PeriodoVista; label: string; factor: number }[] = [
  { id: 'mes', label: 'Mes', factor: 1 / 12 },
  { id: 'anio', label: 'Año', factor: 1 },
]

function subtituloPeriodo(base: string, periodo: PeriodoVista): string {
  return periodo === 'mes' ? `${base} / mes` : `${base} / año`
}

function PizarraBlock({
  title,
  subtitle,
  value,
  lines,
  accent,
  glow,
  nota,
}: {
  title: string
  subtitle: string
  value: string
  lines: string[]
  accent: string
  glow: string
  nota?: string
}) {
  return (
    <article
      className={`relative overflow-hidden rounded-2xl border border-top-border bg-top-card/90 p-6 shadow-lg shadow-black/25`}
    >
      <div className={`absolute -right-8 -top-8 h-32 w-32 rounded-full opacity-25 blur-3xl ${glow}`} />
      <div className={`mb-3 inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-widest ${accent}`}>
        {title}
      </div>
      <p className="text-sm text-slate-400">{subtitle}</p>
      <p className="mt-3 text-4xl font-extrabold tracking-tight text-white md:text-[2.75rem]">{value}</p>
      <ul className="mt-4 space-y-1.5">
        {lines.map((line) => (
          <li key={line} className="text-sm text-slate-300">
            {line}
          </li>
        ))}
      </ul>
      {nota && <p className="mt-3 text-xs text-slate-500">{nota}</p>}
    </article>
  )
}

export function PizarraHero({ data }: { data: DashboardData }) {
  const [periodo, setPeriodo] = useState<PeriodoVista>('anio')
  const factor = periodo === 'mes' ? 1 / 12 : 1

  const p = data.resumen.pizarra
  const cot = data.parametros.cotizacion_dolar
  const cotMeta = data.parametros.cotizacion_meta
  const cotLabel =
    cotMeta?.auto && cotMeta.fuente?.includes('dolarapi')
      ? `Dólar ${cotMeta.tipo ?? 'blue'}: $${fmtNum(cot)}`
      : `Dólar ref: $${fmtNum(cot)}`

  const evitamosRef =
    p.evitamos_usd === p.evitamos_vs_app
      ? 'vs apps de mercado'
      : p.evitamos_usd === p.evitamos_vs_empresa
        ? 'vs empresa desarrolladora'
        : 'vs freelancer'

  const roiAnual = p.roi_usd
  const entregados = p.casos_entregados ?? 0
  const totalCasos = data.resumen.total_casos

  const invertimosUsd = p.invertimos_usd * factor
  const conocimientoUsd = p.conocimiento_usd * factor
  const liberamosUsd = p.liberamos_usd_anual * factor
  const liberamosHoras = p.liberamos_horas_anual * factor
  const evitamosUsd = p.evitamos_usd * factor
  const evitamosFl = p.evitamos_vs_freelancer * factor
  const evitamosEm = p.evitamos_vs_empresa * factor
  const evitamosApp = p.evitamos_vs_app * factor

  const horasInvLabel =
    periodo === 'mes'
      ? `${fmtNum(p.invertimos_horas_dev / 12)} hs dev equivalentes/mes`
      : `${fmtNum(p.invertimos_horas_dev)} hs de desarrollo`

  const horasLiberamosLabel =
    periodo === 'mes'
      ? `${fmtNum(liberamosHoras)} hs/mes de tiempo liberado`
      : `${fmtNum(liberamosHoras)} hs/año de tiempo liberado`

  const roiLine =
    periodo === 'mes'
      ? `ROI neto equivalente/mes: ${fmtUsd(roiAnual * factor)}`
      : `ROI neto portfolio: ${fmtUsd(roiAnual)}`

  const tarifaLine =
    periodo === 'mes'
      ? `ARS ${fmtNum(data.parametros.tarifa_ahorro_ars_h)}/h · vista mensual`
      : `ARS ${fmtNum(data.parametros.tarifa_ahorro_ars_h)}/h × 12 meses`

  return (
    <section className="mb-8">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">Modelo pizarra</p>
          <h2 className="mt-1 text-xl font-bold text-white md:text-2xl">Valor TOP en tres dimensiones</h2>
          <p className="mt-1 text-xs text-slate-500">
            Solo apps entregadas ({entregados} de {totalCasos} casos)
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div
            className="inline-flex rounded-full border border-top-border bg-slate-900/90 p-0.5"
            role="group"
            aria-label="Período de visualización"
          >
            {PERIODOS.map((opt) => (
              <button
                key={opt.id}
                type="button"
                onClick={() => setPeriodo(opt.id)}
                className={`rounded-full px-3 py-1 text-xs font-medium transition ${
                  periodo === opt.id
                    ? 'bg-cyan-500/25 text-cyan-200 ring-1 ring-cyan-500/40'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <span className="rounded-full border border-top-border bg-slate-900/80 px-3 py-1 text-xs text-slate-300">
            {cotLabel}
            {cotMeta?.auto ? ' · vivo' : ''}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <PizarraBlock
          title="1 · Invertimos"
          subtitle={subtituloPeriodo('Lo que pone TOP (desarrollo + conocimiento)', periodo)}
          value={fmtUsd(invertimosUsd)}
          accent="bg-blue-500/20 text-blue-300 ring-1 ring-blue-500/30"
          glow="bg-blue-500"
          nota={periodo === 'mes' ? 'Inversión total expresada en equivalente mensual.' : undefined}
          lines={[
            horasInvLabel,
            `${fmtNum(p.conocimiento_horas)} hs discovery · ${fmtUsd(conocimientoUsd)}`,
            `${entregados} apps entregadas`,
          ]}
        />
        <PizarraBlock
          title="2 · Liberamos"
          subtitle={subtituloPeriodo('Tiempo y dinero que recupera el negocio', periodo)}
          value={fmtUsd(liberamosUsd)}
          accent="bg-emerald-500/20 text-emerald-300 ring-1 ring-emerald-500/30"
          glow="bg-emerald-500"
          lines={[horasLiberamosLabel, roiLine, tarifaLine]}
        />
        <PizarraBlock
          title="3 · Evitamos pagar afuera"
          subtitle={subtituloPeriodo('Ahorro vs contratar externo o comprar apps', periodo)}
          value={fmtUsd(evitamosUsd)}
          accent="bg-amber-500/20 text-amber-300 ring-1 ring-amber-500/30"
          glow="bg-amber-500"
          lines={[
            `Referencia principal: ${evitamosRef}`,
            `Freelancer: ${fmtUsd(evitamosFl)} · Empresa: ${fmtUsd(evitamosEm)}`,
            `Apps mercado: ${fmtUsd(evitamosApp)}`,
          ]}
        />
      </div>
    </section>
  )
}
