import type { DashboardData } from '../types'
import { fmtNum, fmtUsd } from './ChartTooltip'

function PizarraBlock({
  title,
  subtitle,
  value,
  lines,
  accent,
  glow,
}: {
  title: string
  subtitle: string
  value: string
  lines: string[]
  accent: string
  glow: string
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
    </article>
  )
}

export function PizarraHero({ data }: { data: DashboardData }) {
  const p = data.resumen.pizarra
  const cot = data.parametros.cotizacion_dolar
  const cotMeta = data.parametros.cotizacion_meta
  const cotLabel =
    cotMeta?.auto && cotMeta.fuente?.includes('dolarapi')
      ? `Dólar ${cotMeta.tipo ?? 'blue'}: $${fmtNum(cot)} (vivo)`
      : `Dólar ref: $${fmtNum(cot)}`

  const evitamosRef =
    p.evitamos_usd === p.evitamos_vs_app
      ? 'vs apps de mercado'
      : p.evitamos_usd === p.evitamos_vs_empresa
        ? 'vs empresa desarrolladora'
        : 'vs freelancer'

  return (
    <section className="mb-8">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">Modelo pizarra</p>
          <h2 className="mt-1 text-xl font-bold text-white md:text-2xl">Valor TOP en tres dimensiones</h2>
        </div>
        <span className="rounded-full border border-top-border bg-slate-900/80 px-3 py-1 text-xs text-slate-300">
          {cotLabel}
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <PizarraBlock
          title="1 · Invertimos"
          subtitle="Lo que pone TOP (desarrollo + conocimiento)"
          value={fmtUsd(p.invertimos_usd)}
          accent="bg-blue-500/20 text-blue-300 ring-1 ring-blue-500/30"
          glow="bg-blue-500"
          lines={[
            `${fmtNum(p.invertimos_horas_dev)} hs de desarrollo`,
            `${fmtNum(p.conocimiento_horas)} hs discovery · ${fmtUsd(p.conocimiento_usd)}`,
            `${data.resumen.total_casos} casos activos`,
          ]}
        />
        <PizarraBlock
          title="2 · Liberamos"
          subtitle="Tiempo y dinero que recupera el negocio / año"
          value={fmtUsd(p.liberamos_usd_anual)}
          accent="bg-emerald-500/20 text-emerald-300 ring-1 ring-emerald-500/30"
          glow="bg-emerald-500"
          lines={[
            `${fmtNum(p.liberamos_horas_anual)} hs/año de tiempo liberado`,
            `ROI neto portfolio: ${fmtUsd(data.resumen.roi_total_usd)}`,
            `ARS ${fmtNum(data.parametros.tarifa_ahorro_ars_h)}/h × 12 meses`,
          ]}
        />
        <PizarraBlock
          title="3 · Evitamos pagar afuera"
          subtitle="Ahorro vs contratar externo o comprar apps"
          value={fmtUsd(p.evitamos_usd)}
          accent="bg-amber-500/20 text-amber-300 ring-1 ring-amber-500/30"
          glow="bg-amber-500"
          lines={[
            `Referencia principal: ${evitamosRef}`,
            `Freelancer: ${fmtUsd(p.evitamos_vs_freelancer)} · Empresa: ${fmtUsd(p.evitamos_vs_empresa)}`,
            `Apps mercado: ${fmtUsd(p.evitamos_vs_app)}`,
          ]}
        />
      </div>
    </section>
  )
}
