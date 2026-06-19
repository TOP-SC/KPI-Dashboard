export interface KpiCaso {
  horas_invertidas: number
  inversion_usd: number
  reduccion_hs_mes: number
  horas_ahorradas_anual: number
  ahorro_mensual_ars: number
  ahorro_anual_ars: number
  ahorro_anual_usd: number
  roi_usd: number
  tarifa_inversion_usd_h: number
  tarifa_ahorro_ars_h: number
  cotizacion_dolar: number
}

export interface ComparativoCaso {
  complejidad: 'baja' | 'media' | 'alta'
  discovery_razon: string
  discovery_horas_top: number
  discovery_desde_sheet: boolean
  discovery_horas_externo_estimado: number
  discovery_usd_top: number
  discovery_usd_freelancer: number
  discovery_usd_empresa: number
  valor_conocimiento_interno_usd: number
  brecha_logica_app_usd: number | null
  app_mercado_usd_anual: number | null
  app_mercado_usd_horizonte: number | null
  app_costo_real_usd: number | null
  app_mercado_nombre: string | null
  app_mercado_nombre_corto: string | null
  app_mercado_pricing_ref: string | null
  app_mercado_match_por: string | null
  app_mercado_alternativas: string[]
  app_mercado_categoria: string | null
  horas_conocimiento_total: number
  freelancer_usd: number
  empresa_usd: number
  freelancer_total_usd: number
  empresa_total_usd: number
  ahorro_vs_freelancer: number | null
  ahorro_vs_empresa: number | null
  ahorro_vs_app: number | null
  ahorro_vs_app_real: number | null
  veredicto: 'pro_top' | 'alerta_app' | 'neutro'
  veredicto_texto: string
  fuente_app: string
  fuente_discovery_top: string
  fuente_discovery_externo: string
  fuente_freelancer: string
  fuente_empresa: string
  horizonte_app_anios: number
}

export interface Caso {
  listado: number | string
  codigo_unico?: string
  reporte: string
  origen_solicitante?: string
  origen?: string
  usuario?: string
  herramienta?: string
  fecha_inicio?: string
  fecha_final?: string
  mercado_similar?: string
  valor_mercado?: string
  estado: 'realizado' | 'en_desarrollo' | 'por_comenzar'
  alerta_roi?: string | null
  fases_inversion?: {
    horas_por_fase: {
      discovery: number | null
      diseno: number | null
      desarrollo: number | null
      implementacion: number | null
      mantenimiento: number | null
    }
    fee_usd: number | null
    nube_usd_mes: number | null
    total_usd_fases: number | null
    desde_sheet: boolean
  }
  kpi: KpiCaso
  comparativo: ComparativoCaso
}

export interface DashboardData {
  fuente: string
  avisos?: string[]
  parametros: {
    tarifa_inversion_usd_h: number
    tarifa_ahorro_ars_h: number
    cotizacion_dolar: number
    cotizacion_meta?: {
      fuente?: string
      tipo?: string
      auto?: boolean
      venta?: number
      actualizado?: string
      error_api?: string
    }
    tarifa_freelancer_usd_h: number
    tarifa_empresa_usd_h: number
    horizonte_app_anios: number
    discovery_hs_baja: number
    discovery_hs_media: number
    discovery_hs_alta: number
    discovery_externo_factor: number
  }
  resumen: {
    total_casos: number
    inversion_total_usd: number
    ahorro_anual_total_usd: number
    roi_total_usd: number
    horas_invertidas_total: number
    horas_ahorradas_anual_total: number
    casos_roi_negativo: number
    por_estado: Record<string, number>
    pizarra: {
      invertimos_usd: number
      invertimos_horas_dev: number
      conocimiento_usd: number
      conocimiento_horas: number
      liberamos_usd_anual: number
      liberamos_horas_anual: number
      evitamos_usd: number
      evitamos_vs_freelancer: number
      evitamos_vs_empresa: number
      evitamos_vs_app: number
    }
    comparativo_total: {
      ahorro_vs_freelancer_usd: number
      ahorro_vs_empresa_usd: number
      ahorro_vs_app_real_usd: number
      valor_conocimiento_interno_usd: number
      casos_pro_top_discovery: number
    }
  }
  casos: Caso[]
}

export type TabId = 'dashboard' | 'comparativos' | 'revisar'
