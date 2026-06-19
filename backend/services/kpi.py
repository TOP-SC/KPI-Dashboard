import re
from datetime import datetime
from typing import Any

from services.mercado_apps import resolver_alternativa


def _parse_num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text or re.search(r"[a-zA-Z]{3,}", text):
        return None
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", text):
        return float(text.replace(".", ""))
    normalized = text.replace(".", "").replace(",", ".")
    match = re.search(r"[\d.]+", normalized)
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _parse_usd_mercado(text: str | None) -> float | None:
    if not text:
        return None
    match = re.search(r"USD\s*([\d.,]+)", text, re.I)
    if not match:
        return None
    raw = match.group(1)
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", raw):
        return float(raw.replace(".", ""))
    return _parse_num(raw)


def _texto_caso(caso: dict[str, Any], incluir_mercado: bool = False) -> str:
    partes = [
        caso.get("reporte"),
        caso.get("origen"),
        caso.get("origen_solicitante"),
        caso.get("usuario"),
        caso.get("herramienta"),
        caso.get("asignado"),
        caso.get("partner"),
        caso.get("en_arg"),
        caso.get("obs"),
    ]
    if incluir_mercado:
        partes.extend([caso.get("mercado_similar"), caso.get("valor_mercado")])
    return " ".join(str(p) for p in partes if p).lower()


def _analizar_discovery(
    caso: dict[str, Any],
    horas: float,
    cfg: dict[str, float],
) -> tuple[str, float, str]:
    """
    Evalúa discovery leyendo el contexto del caso en la sheet (no solo el título).
    Retorna: (complejidad, horas_discovery, razón legible).
    """
    texto = _texto_caso(caso, incluir_mercado=False)
    score = 0
    razones: list[str] = []

    # --- Señales de alta complejidad (integraciones, lógica de negocio) ---
    integraciones = {
        "tango": "integración Tango/ERP",
        "sap ": "integración SAP",
        "erp": "lógica ERP",
        "formassembly": "formularios + integración",
        "power apps": "Power Apps + ecosistema Microsoft",
        "power bi": "modelo de datos / BI",
        "vba": "legacy VBA",
        "python": "desarrollo Python custom",
        "sql": "acceso directo a datos",
        "rpa": "automatización RPA",
        "workflow": "flujos de aprobación",
    }
    for kw, razon in integraciones.items():
        if kw in texto:
            score += 12
            if razon not in razones:
                razones.append(razon)

    stack_custom = ["html", "gemini", "cursor", "claude", "javascript", "react", "node"]
    if sum(1 for k in stack_custom if k in texto) >= 2:
        score += 14
        razones.append("stack de desarrollo a medida")
    elif any(k in texto for k in stack_custom):
        score += 8
        razones.append("herramientas de dev asistido")

    if "/" in (caso.get("asignado") or "") or "equipo top" in texto:
        score += 10
        razones.append("múltiples áreas involucradas")

    if any(k in texto for k in ("directorio", "abastecimiento", "comex", "comercial", "finanzas")):
        score += 6
        razones.append("proceso transversal de negocio")

    if len((caso.get("en_arg") or "")) > 120:
        score += 8
        razones.append("contexto AR detallado (adaptación local relevante)")

    if any(k in texto for k in ("pendiente", "permiso", "integración", "cuello de botella", "proceso")):
        score += 5
        razones.append("proceso con dependencias / validaciones")

    # --- Señales de baja complejidad (automatización acotada) ---
    if any(k in texto for k in ("alerta", "aviso", "notific", "slack", "mail")):
        score -= 10
        razones.append("automatización puntual de avisos")

    if "apps script" in texto and not any(k in texto for k in stack_custom + ["html", "power apps"]):
        score -= 4

    if horas > 0 and horas <= 12 and "apps script" in texto:
        score -= 6
        razones.append("automatización liviana en horas")

    # Horas como señal secundaria (no principal)
    if horas >= 80:
        score += 10
        razones.append(f"{int(horas)} hs de desarrollo")
    elif horas >= 40:
        score += 6
    elif horas >= 20:
        score += 3

    # Casos sin desarrollo aún: inferir por tipo de proceso
    if horas == 0 and resolver_alternativa(caso):
        score += 8
        razones.append("caso en análisis con alternativa de mercado identificada")

    # Mapeo score → complejidad + horas (interpolación dentro del rango)
    if score >= 30:
        complejidad = "alta"
        base, techo = cfg["media"], cfg["alta"]
    elif score >= 12:
        complejidad = "media"
        base, techo = cfg["baja"], cfg["media"]
    else:
        complejidad = "baja"
        base, techo = cfg["baja"] * 0.7, cfg["baja"]

    rango = techo - base
    factor = min(max((score + 10) / 50, 0), 1)
    hs_discovery = round(base + rango * factor, 1)
    hs_discovery = max(cfg["baja"] * 0.5, min(hs_discovery, cfg["alta"]))

    if not razones:
        razones.append("automatización estándar según datos de sheet")

    razon_txt = "; ".join(dict.fromkeys(razones))[:200]
    return complejidad, hs_discovery, razon_txt


def _horas_discovery(complejidad: str, cfg: dict[str, float]) -> float:
    return {
        "baja": cfg["baja"],
        "media": cfg["media"],
        "alta": cfg["alta"],
    }.get(complejidad, cfg["media"])


def _estado_caso(caso: dict[str, Any], hoy: datetime | None = None) -> str:
    hoy = hoy or datetime.now()
    inicio = _parse_date(caso.get("fecha_inicio"))
    fin = _parse_date(caso.get("fecha_final"))
    horas = _parse_num(caso.get("horas_invertidas")) or 0

    if horas == 0 and not inicio:
        return "por_comenzar"
    if fin and fin.date() < hoy.date() and horas > 0:
        return "realizado"
    if inicio and inicio.date() > hoy.date():
        return "por_comenzar"
    if horas > 0 or inicio:
        return "en_desarrollo"
    return "por_comenzar"


def _alerta_roi(
    caso: dict[str, Any],
    estado: str,
    roi_usd: float,
    reduccion_mes: float,
    horas: float,
) -> str | None:
    alertas: list[str] = []
    if horas > 300:
        alertas.append("Horas invertidas muy altas: revisar dato en sheet")
    if reduccion_mes == 0 and caso.get("inversion_usd"):
        if estado in ("en_desarrollo", "por_comenzar"):
            alertas.append("Sin horas de ahorro cargadas aún (caso en curso)")
        else:
            alertas.append("Sin ahorro de tiempo registrado")
    if roi_usd < 0 and reduccion_mes > 0:
        alertas.append("Inversión TOP supera el ahorro anual estimado")
    elif roi_usd < 0 and estado == "en_desarrollo":
        alertas.append("ROI negativo provisional: el caso sigue en desarrollo")
    if alertas:
        return " · ".join(alertas)
    return None


def _nombre_app_corto(mercado: str | None) -> str | None:
    if not mercado:
        return None
    parte = mercado.split("/")[0].strip()
    return parte[:80] if parte else None


def _veredicto_discovery(
    inversion_usd: float,
    app_total: float | None,
    brecha_app: float | None,
    ahorro_vs_app_bruto: float | None,
    complejidad: str,
    horas_dev: float,
    hs_discovery: float,
    app_nombre: str | None,
) -> tuple[str, str]:
    """Retorna (codigo, texto) según discovery, conocimiento retenido y encaje con app de mercado."""
    costo_app_real = (app_total or 0) + (brecha_app or 0)
    hs_conocimiento = horas_dev + hs_discovery
    app_ref = app_nombre or "app de mercado"

    # Mucho dev + discovery = conocimiento retenido; app estándar no encaja
    if hs_conocimiento >= 35 or (complejidad == "alta" and hs_conocimiento >= 25):
        return (
            "pro_top",
            f"Conocimiento retenido ({int(hs_conocimiento)}h dev+discovery): "
            f"supera lo que una app estándar ({app_ref}) puede adaptar sin perder lógica interna.",
        )

    if app_total and brecha_app:
        if app_total < inversion_usd and costo_app_real >= inversion_usd:
            return (
                "pro_top",
                f"Licencia de {app_ref} parece barata, pero adaptar la lógica interna "
                "eleva el costo real por encima de TOP.",
            )
        if app_total < inversion_usd * 0.5 and hs_conocimiento < 25:
            return (
                "alerta_app",
                f"{app_ref}: licencia económica; evaluar si cubre el proceso sin discovery adicional.",
            )

    if complejidad == "alta":
        return (
            "pro_top",
            "Alta complejidad y lógica de negocio propia: ventaja TOP frente a solución genérica.",
        )

    if ahorro_vs_app_bruto is not None and ahorro_vs_app_bruto < 0 and brecha_app:
        return (
            "pro_top",
            "TOP incluye discovery de lógica interna; la alternativa comercial no lo incorpora.",
        )

    return (
        "pro_top",
        "TOP incorpora discovery y conocimiento del negocio en la solución.",
    )


def _calcular_comparativo(
    caso: dict[str, Any],
    horas: float,
    inversion_usd: float,
    tarifa_freelancer: float,
    tarifa_empresa: float,
    tarifa_inv: float,
    horizonte_app: int,
    discovery_cfg: dict[str, float],
    discovery_externo_factor: float,
    brecha_app_pct: float,
) -> dict[str, Any]:
    alt = resolver_alternativa(caso)
    app_anual = alt["usd_anual"] if alt else None
    app_nombre = alt["nombre"] if alt else ""
    app_nombre_corto = alt["nombre_corto"] if alt else None
    app_pricing_ref = alt.get("pricing_ref", "") if alt else ""
    app_match_por = alt.get("match_por", "") if alt else ""
    app_alternativas = alt.get("alternativas", []) if alt else []
    fuente_app = alt.get("fuente", "Sin alternativa de mercado identificada") if alt else "Sin alternativa de mercado identificada"
    horas_ext = horas if horas > 0 else 0
    complejidad, hs_discovery_est, discovery_razon = _analizar_discovery(caso, horas, discovery_cfg)

    hs_discovery_sheet = _parse_num(caso.get("discovery_horas"))
    if hs_discovery_sheet is not None and hs_discovery_sheet > 0:
        hs_discovery_top = hs_discovery_sheet
        fuente_discovery_top = "Sheet: Discovery (hs) real"
    else:
        hs_discovery_top = hs_discovery_est
        fuente_discovery_top = f"Estimado por complejidad ({complejidad}): incluye lógica interna"

    hs_discovery_ext = round(hs_discovery_top * discovery_externo_factor, 1)
    hs_conocimiento = horas_ext + hs_discovery_top

    discovery_usd_top = round(hs_discovery_top * tarifa_inv, 2)
    discovery_usd_freelancer = round(hs_discovery_ext * tarifa_freelancer, 2)
    discovery_usd_empresa = round(hs_discovery_ext * tarifa_empresa, 2)
    valor_conocimiento = discovery_usd_top

    freelancer_usd = round(horas_ext * tarifa_freelancer, 2)
    empresa_usd = round(horas_ext * tarifa_empresa, 2)
    freelancer_total = round(freelancer_usd + discovery_usd_freelancer, 2)
    empresa_total = round(empresa_usd + discovery_usd_empresa, 2)

    app_total = round(app_anual * horizonte_app, 2) if app_anual else None
    brecha_factor = 1.0
    if hs_conocimiento >= 50:
        brecha_factor = 1.6
    elif hs_conocimiento >= 35:
        brecha_factor = 1.35
    elif hs_conocimiento >= 25:
        brecha_factor = 1.15

    brecha_app = (
        round(discovery_usd_freelancer * (1 + brecha_app_pct) * brecha_factor, 2)
        if app_anual
        else None
    )
    app_costo_real = round((app_total or 0) + (brecha_app or 0), 2) if app_total else None

    ahorro_vs_freelancer = round(freelancer_total - inversion_usd, 2) if horas_ext else None
    ahorro_vs_empresa = round(empresa_total - inversion_usd, 2) if horas_ext else None
    ahorro_vs_app = round(app_total - inversion_usd, 2) if app_total else None
    ahorro_vs_app_real = round(app_costo_real - inversion_usd, 2) if app_costo_real else None

    veredicto, veredicto_texto = _veredicto_discovery(
        inversion_usd,
        app_total,
        brecha_app,
        ahorro_vs_app,
        complejidad,
        horas_ext,
        hs_discovery_top,
        app_nombre_corto,
    )

    return {
        "complejidad": complejidad,
        "discovery_razon": discovery_razon,
        "discovery_horas_top": hs_discovery_top,
        "discovery_desde_sheet": hs_discovery_sheet is not None and hs_discovery_sheet > 0,
        "discovery_horas_externo_estimado": hs_discovery_ext,
        "discovery_usd_top": discovery_usd_top,
        "discovery_usd_freelancer": discovery_usd_freelancer,
        "discovery_usd_empresa": discovery_usd_empresa,
        "valor_conocimiento_interno_usd": valor_conocimiento,
        "brecha_logica_app_usd": brecha_app,
        "app_mercado_usd_anual": app_anual,
        "app_mercado_usd_horizonte": app_total,
        "app_costo_real_usd": app_costo_real,
        "app_mercado_nombre": app_nombre[:120] if app_nombre else None,
        "app_mercado_nombre_corto": app_nombre_corto,
        "app_mercado_pricing_ref": app_pricing_ref or None,
        "app_mercado_match_por": app_match_por or None,
        "app_mercado_alternativas": app_alternativas,
        "app_mercado_categoria": alt.get("categoria") if alt else None,
        "horas_conocimiento_total": round(hs_conocimiento, 1),
        "freelancer_usd": freelancer_usd,
        "empresa_usd": empresa_usd,
        "freelancer_total_usd": freelancer_total,
        "empresa_total_usd": empresa_total,
        "ahorro_vs_freelancer": ahorro_vs_freelancer,
        "ahorro_vs_empresa": ahorro_vs_empresa,
        "ahorro_vs_app": ahorro_vs_app,
        "ahorro_vs_app_real": ahorro_vs_app_real,
        "veredicto": veredicto,
        "veredicto_texto": veredicto_texto,
        "fuente_app": fuente_app,
        "fuente_discovery_top": fuente_discovery_top,
        "fuente_discovery_externo": f"Discovery × {discovery_externo_factor} (externo no conoce el negocio)",
        "fuente_freelancer": f"(Hs dev + discovery externo) × tarifas mercado",
        "fuente_empresa": f"(Hs dev + discovery externo) × tarifa agencia",
        "horizonte_app_anios": horizonte_app,
    }


def enriquecer_caso(
    caso: dict[str, Any],
    tarifa_inv: float,
    tarifa_ahorro_ars: float,
    cotizacion: float,
    tarifa_freelancer: float = 75,
    tarifa_empresa: float = 100,
    horizonte_app: int = 3,
    discovery_cfg: dict[str, float] | None = None,
    discovery_externo_factor: float = 1.5,
    brecha_app_pct: float = 0.35,
) -> dict[str, Any]:
    discovery_cfg = discovery_cfg or {"baja": 10, "media": 25, "alta": 40}

    horas = _parse_num(caso.get("horas_invertidas")) or 0
    inversion_sheet = _parse_num(caso.get("inversion_usd"))
    reduccion_mes = _parse_num(caso.get("reduccion_hs_mes")) or 0
    ahorro_sheet = _parse_num(caso.get("ahorro_calculado"))

    inversion_usd = inversion_sheet if inversion_sheet is not None else horas * tarifa_inv

    if ahorro_sheet is not None and reduccion_mes > 0:
        ratio = ahorro_sheet / reduccion_mes
        if ratio > 1000:
            ahorro_mensual_ars = ahorro_sheet
            ahorro_mensual_usd = ahorro_sheet / cotizacion if cotizacion else 0
        else:
            ahorro_mensual_usd = ahorro_sheet
            ahorro_mensual_ars = ahorro_sheet * cotizacion if cotizacion else 0
    else:
        ahorro_mensual_ars = reduccion_mes * tarifa_ahorro_ars
        ahorro_mensual_usd = ahorro_mensual_ars / cotizacion if cotizacion else 0

    ahorro_anual_ars = ahorro_mensual_ars * 12
    ahorro_anual_usd = ahorro_mensual_usd * 12
    horas_ahorradas_anual = reduccion_mes * 12
    roi_usd = ahorro_anual_usd - inversion_usd
    estado = _estado_caso(caso)
    alerta = _alerta_roi(caso, estado, roi_usd, reduccion_mes, horas)
    comparativo = _calcular_comparativo(
        caso,
        horas,
        inversion_usd,
        tarifa_freelancer,
        tarifa_empresa,
        tarifa_inv,
        horizonte_app,
        discovery_cfg,
        discovery_externo_factor,
        brecha_app_pct,
    )

    fases_raw = caso.get("fases") or {}
    fases_inversion = _calcular_fases_inversion(
        hs_discovery=comparativo["discovery_horas_top"],
        fases_raw=fases_raw,
        tarifa_inv=tarifa_inv,
        horas_dev=horas,
    )

    return {
        **caso,
        "estado": estado,
        "alerta_roi": alerta,
        "fases_inversion": fases_inversion,
        "kpi": {
            "horas_invertidas": horas,
            "inversion_usd": round(inversion_usd, 2),
            "reduccion_hs_mes": reduccion_mes,
            "horas_ahorradas_anual": horas_ahorradas_anual,
            "ahorro_mensual_ars": round(ahorro_mensual_ars, 2),
            "ahorro_anual_ars": round(ahorro_anual_ars, 2),
            "ahorro_anual_usd": round(ahorro_anual_usd, 2),
            "roi_usd": round(roi_usd, 2),
            "tarifa_inversion_usd_h": tarifa_inv,
            "tarifa_ahorro_ars_h": tarifa_ahorro_ars,
            "cotizacion_dolar": cotizacion,
        },
        "comparativo": comparativo,
    }


def _calcular_fases_inversion(
    hs_discovery: float,
    fases_raw: dict[str, Any],
    tarifa_inv: float,
    horas_dev: float,
) -> dict[str, Any]:
    diseno = _parse_num(fases_raw.get("diseno_hs"))
    dev_fase = _parse_num(fases_raw.get("desarrollo_hs"))
    impl = _parse_num(fases_raw.get("implementacion_hs"))
    mant = _parse_num(fases_raw.get("mantenimiento_hs"))
    fee = _parse_num(fases_raw.get("fee_usd"))
    nube = _parse_num(fases_raw.get("nube_usd_mes"))

    hs_por_fase = {
        "discovery": hs_discovery if hs_discovery > 0 else None,
        "diseno": diseno,
        "desarrollo": dev_fase if dev_fase is not None else (horas_dev if horas_dev > 0 else None),
        "implementacion": impl,
        "mantenimiento": mant,
    }
    usd_horas = sum(
        (h or 0) * tarifa_inv for h in hs_por_fase.values() if h is not None
    )
    usd_directo = (fee or 0) + (nube or 0) * 12
    tiene_sheet = any(
        v is not None and v > 0
        for v in [diseno, dev_fase, impl, mant, fee, nube]
    )

    return {
        "horas_por_fase": hs_por_fase,
        "fee_usd": fee,
        "nube_usd_mes": nube,
        "total_usd_fases": round(usd_horas + usd_directo, 2) if (tiene_sheet or hs_discovery > 0) else None,
        "desde_sheet": tiene_sheet,
    }


def calcular_resumen(casos: list[dict[str, Any]]) -> dict[str, Any]:
    total_inv = sum(c["kpi"]["inversion_usd"] for c in casos)
    total_ahorro_usd = sum(c["kpi"]["ahorro_anual_usd"] for c in casos)
    total_horas_inv = sum(c["kpi"]["horas_invertidas"] for c in casos)
    total_horas_ahorro = sum(c["kpi"]["horas_ahorradas_anual"] for c in casos)
    por_estado: dict[str, int] = {"realizado": 0, "en_desarrollo": 0, "por_comenzar": 0}
    negativos = 0
    ahorro_vs_freelancer = 0.0
    ahorro_vs_empresa = 0.0
    ahorro_vs_app_real = 0.0
    valor_conocimiento_total = 0.0
    discovery_horas_total = 0.0
    pro_top = 0

    for c in casos:
        por_estado[c["estado"]] = por_estado.get(c["estado"], 0) + 1
        if c["kpi"]["roi_usd"] < 0:
            negativos += 1
        comp = c.get("comparativo", {})
        if comp.get("ahorro_vs_freelancer") is not None:
            ahorro_vs_freelancer += comp["ahorro_vs_freelancer"]
        if comp.get("ahorro_vs_empresa") is not None:
            ahorro_vs_empresa += comp["ahorro_vs_empresa"]
        if comp.get("ahorro_vs_app_real") is not None:
            ahorro_vs_app_real += comp["ahorro_vs_app_real"]
        valor_conocimiento_total += comp.get("valor_conocimiento_interno_usd", 0)
        discovery_horas_total += comp.get("discovery_horas_top", 0)
        if comp.get("veredicto") == "pro_top":
            pro_top += 1

    evitamos_usd = max(ahorro_vs_freelancer, ahorro_vs_empresa, ahorro_vs_app_real)

    return {
        "total_casos": len(casos),
        "inversion_total_usd": round(total_inv, 2),
        "ahorro_anual_total_usd": round(total_ahorro_usd, 2),
        "roi_total_usd": round(total_ahorro_usd - total_inv, 2),
        "horas_invertidas_total": total_horas_inv,
        "horas_ahorradas_anual_total": total_horas_ahorro,
        "casos_roi_negativo": negativos,
        "por_estado": por_estado,
        "pizarra": {
            "invertimos_usd": round(total_inv, 2),
            "invertimos_horas_dev": total_horas_inv,
            "conocimiento_usd": round(valor_conocimiento_total, 2),
            "conocimiento_horas": round(discovery_horas_total, 1),
            "liberamos_usd_anual": round(total_ahorro_usd, 2),
            "liberamos_horas_anual": total_horas_ahorro,
            "evitamos_usd": round(evitamos_usd, 2),
            "evitamos_vs_freelancer": round(ahorro_vs_freelancer, 2),
            "evitamos_vs_empresa": round(ahorro_vs_empresa, 2),
            "evitamos_vs_app": round(ahorro_vs_app_real, 2),
        },
        "comparativo_total": {
            "ahorro_vs_freelancer_usd": round(ahorro_vs_freelancer, 2),
            "ahorro_vs_empresa_usd": round(ahorro_vs_empresa, 2),
            "ahorro_vs_app_real_usd": round(ahorro_vs_app_real, 2),
            "valor_conocimiento_interno_usd": round(valor_conocimiento_total, 2),
            "casos_pro_top_discovery": pro_top,
        },
    }
