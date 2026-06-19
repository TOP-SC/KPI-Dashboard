import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { Caso } from '../types'
import { ChartTooltip, fmtNum, fmtUsd } from './ChartTooltip'

const COLORS = ['#22c55e', '#3b82f6', '#f59e0b']

export function KpiCharts({ casos, porEstado }: { casos: Caso[]; porEstado: Record<string, number> }) {
  const estadoData = [
    { name: 'Realizados', value: porEstado.realizado ?? 0, key: 'realizado' },
    { name: 'En desarrollo', value: porEstado.en_desarrollo ?? 0, key: 'en_desarrollo' },
    { name: 'Por comenzar', value: porEstado.por_comenzar ?? 0, key: 'por_comenzar' },
  ]

  const topRoi = [...casos]
    .filter((c) => c.kpi.roi_usd > 0)
    .sort((a, b) => b.kpi.roi_usd - a.kpi.roi_usd)
    .slice(0, 8)
    .map((c) => ({
      name: c.reporte.length > 22 ? `${c.reporte.slice(0, 22)}…` : c.reporte,
      fullName: c.reporte,
      roi: c.kpi.roi_usd,
    }))

  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
      <div className="rounded-2xl border border-top-border bg-top-card/80 p-5 backdrop-blur">
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
          Pipeline de casos
        </h3>
        <ResponsiveContainer width="100%" height={260}>
          <PieChart>
            <Pie data={estadoData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={95} paddingAngle={4}>
              {estadoData.map((_, i) => (
                <Cell key={i} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip content={<ChartTooltip />} />
            <Legend wrapperStyle={{ color: '#cbd5e1' }} />
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="rounded-2xl border border-top-border bg-top-card/80 p-5 backdrop-blur">
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
          Top casos por ROI (USD/año)
        </h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={topRoi} layout="vertical" margin={{ left: 10, right: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 11 }} />
            <YAxis type="category" dataKey="name" width={120} tick={{ fill: '#e2e8f0', fontSize: 10 }} />
            <Tooltip
              content={<ChartTooltip />}
              labelFormatter={(_, payload) => payload?.[0]?.payload?.fullName ?? ''}
            />
            <Bar dataKey="roi" name="ROI" fill="#a855f7" radius={[0, 6, 6, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="rounded-2xl border border-top-border bg-top-card/80 p-5 backdrop-blur xl:col-span-2">
        <h3 className="mb-4 text-sm font-semibold uppercase tracking-wider text-slate-400">
          Inversión vs ahorro anual (top 10)
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={[...casos]
              .sort((a, b) => b.kpi.ahorro_anual_usd - a.kpi.ahorro_anual_usd)
              .slice(0, 10)
              .map((c) => ({
                name: c.reporte.length > 18 ? `${c.reporte.slice(0, 18)}…` : c.reporte,
                fullName: c.reporte,
                inversion: c.kpi.inversion_usd,
                ahorro: c.kpi.ahorro_anual_usd,
              }))}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="name" tick={{ fill: '#e2e8f0', fontSize: 10 }} interval={0} angle={-20} textAnchor="end" height={70} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 11 }} tickFormatter={(v) => fmtNum(v)} />
            <Tooltip content={<ChartTooltip />} labelFormatter={(_, p) => p?.[0]?.payload?.fullName ?? ''} />
            <Legend wrapperStyle={{ color: '#cbd5e1' }} />
            <Bar dataKey="inversion" name="Inversión TOP" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="ahorro" name="Ahorro anual" fill="#22c55e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}

export function StatCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string
  value: string
  sub?: string
  accent: string
}) {
  return (
    <div className="relative overflow-hidden rounded-2xl border border-top-border bg-top-card/90 p-5 shadow-lg shadow-black/20">
      <div className={`absolute -right-6 -top-6 h-24 w-24 rounded-full opacity-20 blur-2xl ${accent}`} />
      <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</p>
      <p className="mt-2 text-3xl font-bold text-white">{value}</p>
      {sub && <p className="mt-1 text-sm text-slate-400">{sub}</p>}
    </div>
  )
}
