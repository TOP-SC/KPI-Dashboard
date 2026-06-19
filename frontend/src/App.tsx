import { useCallback, useEffect, useState } from 'react'
import { CasosRevisarView, filtrarCasosRevisar } from './components/CasosRevisar'
import { ComparativosView } from './components/Comparativos'
import { KpiCharts, StatCard } from './components/Dashboard'
import { fmtUsd } from './components/ChartTooltip'
import { CasosTable, PipelineBoard } from './components/Pipeline'
import type { DashboardData, TabId } from './types'

const fuenteLabel: Record<string, string> = {
  google_sheets_service_account: 'Google Sheets (en vivo)',
  google_sheets_public: 'Google Sheets (público)',
  local_cache: 'Caché local (última exportación)',
  export_local: 'Exportación local',
}

export default function App() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [tab, setTab] = useState<TabId>('dashboard')
  const [filtro, setFiltro] = useState<'todos' | 'realizado' | 'en_desarrollo' | 'por_comenzar'>('todos')

  const load = useCallback(async (refresh = false) => {
    setLoading(true)
    setError(null)
    try {
      const url = refresh ? '/api/dashboard?refresh=1' : '/api/dashboard'
      const res = await fetch(url)
      if (!res.ok) throw new Error('No se pudo cargar el dashboard')
      const json = (await res.json()) as DashboardData
      setData(json)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-blue-500 border-t-transparent" />
          <p className="text-slate-300">Cargando tablero TOP…</p>
        </div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="flex min-h-screen items-center justify-center p-6">
        <div className="max-w-md rounded-2xl border border-rose-500/30 bg-rose-950/30 p-6 text-center">
          <p className="text-lg font-semibold text-rose-200">Error al cargar</p>
          <p className="mt-2 text-sm text-rose-100/80">{error}</p>
          <button
            onClick={() => load()}
            className="mt-4 rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500"
          >
            Reintentar
          </button>
        </div>
      </div>
    )
  }

  const casos = filtro === 'todos' ? data.casos : data.casos.filter((c) => c.estado === filtro)
  const casosRevisar = filtrarCasosRevisar(data.casos)

  const tabs: { id: TabId; label: string; badge?: number }[] = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'comparativos', label: 'Comparativos' },
    { id: 'revisar', label: 'Casos a revisar', badge: casosRevisar.length || undefined },
  ]

  return (
    <div className="mx-auto min-h-screen max-w-[1600px] px-4 py-6 md:px-8 md:py-8">
      <header className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-400">Grupo TOP</p>
          <h1 className="mt-1 text-3xl font-bold text-white md:text-4xl">Tablero de KPIs</h1>
          <p className="mt-2 max-w-2xl text-slate-400">
            Inversión interna, ahorro de tiempo y comparativa vs mercado externo.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <span className="rounded-full border border-top-border bg-top-card px-3 py-1 text-xs text-slate-300">
            Fuente: {fuenteLabel[data.fuente] ?? data.fuente}
          </span>
          <button
            onClick={() => load(true)}
            className="rounded-xl border border-top-border bg-slate-900 px-4 py-2 text-sm text-slate-200 hover:border-blue-500/50"
          >
            Actualizar
          </button>
        </div>
      </header>

      {data.avisos && data.avisos.length > 0 && (
        <div className="mb-4 rounded-xl border border-amber-500/30 bg-amber-950/30 px-4 py-3 text-sm text-amber-100">
          {data.avisos.join(' ')}
        </div>
      )}

      <nav className="mb-8 flex gap-2 border-b border-top-border pb-1">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 rounded-t-lg px-5 py-2.5 text-sm font-medium transition ${
              tab === t.id
                ? 'bg-blue-600 text-white'
                : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
            }`}
          >
            {t.label}
            {t.badge != null && t.badge > 0 && (
              <span
                className={`rounded-full px-1.5 py-0.5 text-xs font-bold ${
                  tab === t.id ? 'bg-white/20 text-white' : 'bg-amber-500/20 text-amber-300'
                }`}
              >
                {t.badge}
              </span>
            )}
          </button>
        ))}
      </nav>

      {tab === 'comparativos' && <ComparativosView data={data} />}

      {tab === 'revisar' && <CasosRevisarView casos={data.casos} />}

      {tab === 'dashboard' && (
        <>
          <section className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard label="Casos totales" value={String(data.resumen.total_casos)} accent="bg-blue-500" />
            <StatCard
              label="Inversión TOP"
              value={fmtUsd(data.resumen.inversion_total_usd)}
              sub={`${data.resumen.horas_invertidas_total} hs × USD ${data.parametros.tarifa_inversion_usd_h}/h`}
              accent="bg-indigo-500"
            />
            <StatCard
              label="Ahorro anual"
              value={fmtUsd(data.resumen.ahorro_anual_total_usd)}
              sub={`${data.resumen.horas_ahorradas_anual_total} hs liberadas/año`}
              accent="bg-emerald-500"
            />
            <StatCard
              label="ROI neto"
              value={fmtUsd(data.resumen.roi_total_usd)}
              sub={`Dólar ref: $${data.parametros.cotizacion_dolar}`}
              accent="bg-purple-500"
            />
          </section>

          <section className="mb-8">
            <KpiCharts casos={data.casos} porEstado={data.resumen.por_estado} />
          </section>

          <section className="mb-6 flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-xl font-semibold text-white">Pipeline de casos</h2>
            <div className="flex flex-wrap gap-2">
              {(['todos', 'realizado', 'en_desarrollo', 'por_comenzar'] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFiltro(f)}
                  className={`rounded-lg px-3 py-1.5 text-xs font-medium ${
                    filtro === f
                      ? 'bg-blue-600 text-white'
                      : 'border border-top-border bg-top-card text-slate-300 hover:border-blue-500/40'
                  }`}
                >
                  {f === 'todos' ? 'Todos' : f.replace('_', ' ')}
                </button>
              ))}
            </div>
          </section>

          <section className="mb-10">
            <PipelineBoard casos={filtro === 'todos' ? data.casos : casos} />
          </section>

          <section>
            <h2 className="mb-4 text-xl font-semibold text-white">Detalle de casos</h2>
            <CasosTable casos={casos} />
          </section>
        </>
      )}
    </div>
  )
}
