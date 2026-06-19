"""Comparativa contextual: modalidad del caso + componentes de costo por alternativa."""
from __future__ import annotations

import re
from typing import Any

CATEGORIAS_ENTERPRISE = frozenset(
    {
        "comex",
        "compras",
        "abastecimiento",
        "rrhh_payroll",
        "auditoria",
        "inteligencia_competitiva",
        "logistica_fletes",
        "costos",
    }
)

MATRIZ_COMPONENTES: dict[str, dict[str, list[str]]] = {
    "script_ligero": {
        "freelancer": ["dev", "discovery"],
        "empresa": ["dev", "discovery"],
        "app": ["licencia", "brecha"],
    },
    "desarrollo_medida": {
        "freelancer": ["dev", "discovery", "nube"],
        "empresa": ["dev", "discovery", "implementacion", "fee", "nube"],
        "app": ["licencia", "brecha"],
    },
    "integracion_enterprise": {
        "freelancer": ["dev", "discovery"],
        "empresa": ["dev", "discovery", "implementacion", "fee", "mantenimiento"],
        "app": ["licencia", "implementacion", "mantenimiento", "brecha"],
    },
    "saas_encaje": {
        "freelancer": ["dev", "discovery"],
        "empresa": ["dev", "discovery"],
        "app": ["licencia", "brecha"],
    },
}

LABELS_COMPONENTE = {
    "dev": "Desarrollo",
    "discovery": "Discovery",
    "implementacion": "Implementación",
    "fee": "Fee / consultoría",
    "licencia": "Licencia",
    "nube": "Nube / hosting",
    "mantenimiento": "Mantenimiento",
    "brecha": "Adaptación lógica",
}

LABELS_EXTERNO = {
    "freelancer": "Freelancer",
    "empresa": "Empresa",
    "app": "App mercado",
}

_ENTERPRISE_RE = re.compile(
    r"\b(sap|erp|comex|coupa|netsuite|workday|oracle\s+erp)\b",
    re.I,
)


def _texto(caso: dict[str, Any]) -> str:
    partes = [
        caso.get("reporte"),
        caso.get("herramienta"),
        caso.get("origen"),
        caso.get("en_arg"),
        caso.get("obs"),
    ]
    return " ".join(str(p) for p in partes if p).lower()


def _fases_tiene_enterprise(fases_raw: dict[str, Any]) -> bool:
    for key in ("implementacion_hs", "fee_usd", "mantenimiento_hs"):
        val = fases_raw.get(key)
        if val is not None and float(val) > 0:
            return True
    return False


def clasificar_modalidad(
    caso: dict[str, Any],
    horas: float,
    complejidad: str,
    alt: dict[str, Any] | None,
    fases_raw: dict[str, Any] | None = None,
) -> dict[str, str]:
    """Clasifica el caso para decidir qué componentes de costo aplican."""
    fases_raw = fases_raw or {}
    texto = _texto(caso)
    modelo = (alt or {}).get("modelo_costo", "saas")
    categoria = (alt or {}).get("categoria", "")

    if _fases_tiene_enterprise(fases_raw):
        return {"modo": "integracion_enterprise", "modo_label": "Integración / enterprise"}

    if modelo == "enterprise" or categoria in CATEGORIAS_ENTERPRISE:
        return {"modo": "integracion_enterprise", "modo_label": "Integración / enterprise"}

    if _ENTERPRISE_RE.search(texto):
        return {"modo": "integracion_enterprise", "modo_label": "Integración / enterprise"}

    es_liviano = (
        complejidad == "baja"
        and horas <= 24
        and any(k in texto for k in ("alerta", "aviso", "notific", "apps script", "vba", "macro"))
    )
    if es_liviano:
        return {"modo": "script_ligero", "modo_label": "Script / alerta liviana"}

    if alt and modelo == "saas" and complejidad in ("baja", "media") and horas < 30:
        return {"modo": "saas_encaje", "modo_label": "Encaja app SaaS"}

    return {"modo": "desarrollo_medida", "modo_label": "Desarrollo a medida"}


def _impl_hs_estimada(modo: str, horas: float, fases_raw: dict[str, Any]) -> float:
    sheet = fases_raw.get("implementacion_hs")
    if sheet is not None and float(sheet) > 0:
        return float(sheet)
    if modo == "integracion_enterprise":
        return round(horas * 0.35, 1) if horas > 0 else 20.0
    if modo == "desarrollo_medida":
        return round(horas * 0.12, 1) if horas > 0 else 0.0
    return 0.0


def _fee_estimado(modo: str, horas: float, tarifa: float, fases_raw: dict[str, Any]) -> float:
    sheet = fases_raw.get("fee_usd")
    if sheet is not None and float(sheet) > 0:
        return float(sheet)
    if modo == "integracion_enterprise":
        return round(max(horas * tarifa * 0.12, 2500), 2) if horas > 0 else 3000.0
    if modo == "desarrollo_medida":
        return round(horas * tarifa * 0.08, 2) if horas > 0 else 0.0
    return 0.0


def _nube_anual(fases_raw: dict[str, Any], horas: float, modo: str) -> float:
    nube = fases_raw.get("nube_usd_mes")
    if nube is not None and float(nube) > 0:
        return float(nube) * 12
    if modo in ("desarrollo_medida",) and horas >= 40:
        return 600.0
    return 0.0


def _calcular_componente(
    comp_id: str,
    alt_key: str,
    *,
    horas: float,
    hs_discovery_ext: float,
    tarifa_freelancer: float,
    tarifa_empresa: float,
    app_anual: float | None,
    horizonte: int,
    brecha_usd: float | None,
    modo: str,
    fases_raw: dict[str, Any],
    app_modelo: dict[str, Any],
) -> float:
    tarifa = tarifa_freelancer if alt_key == "freelancer" else tarifa_empresa

    if comp_id == "dev":
        return round(horas * tarifa, 2) if horas > 0 else 0.0
    if comp_id == "discovery":
        return round(hs_discovery_ext * tarifa, 2)
    if comp_id == "implementacion":
        if alt_key == "app":
            pct = float(app_modelo.get("implementacion_pct", 0))
            return round((app_anual or 0) * pct, 2) if pct > 0 else 0.0
        impl_hs = _impl_hs_estimada(modo, horas, fases_raw)
        return round(impl_hs * tarifa_empresa, 2)
    if comp_id == "fee":
        return _fee_estimado(modo, horas, tarifa_empresa, fases_raw)
    if comp_id == "licencia":
        return round((app_anual or 0) * horizonte, 2)
    if comp_id == "nube":
        return _nube_anual(fases_raw, horas, modo)
    if comp_id == "mantenimiento":
        if alt_key == "app":
            pct = float(app_modelo.get("mantenimiento_pct_anual", 0))
            return round((app_anual or 0) * pct * horizonte, 2) if pct > 0 else 0.0
        mant_hs = fases_raw.get("mantenimiento_hs")
        if mant_hs is not None and float(mant_hs) > 0:
            return round(float(mant_hs) * tarifa_empresa, 2)
        return round(horas * 0.05 * tarifa_empresa, 2) if horas > 0 else 0.0
    if comp_id == "brecha":
        factor = float(app_modelo.get("brecha_factor", 1.0))
        if modo == "script_ligero":
            factor *= 0.5
        elif modo == "saas_encaje":
            factor *= 0.65
        return round((brecha_usd or 0) * factor, 2)
    return 0.0


def calcular_comparativa_contextual(
    caso: dict[str, Any],
    *,
    inversion_usd: float,
    horas: float,
    complejidad: str,
    hs_discovery_ext: float,
    brecha_app: float | None,
    alt: dict[str, Any] | None,
    tarifa_freelancer: float,
    tarifa_empresa: float,
    horizonte: int,
    fases_raw: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Motor contextual: qué alternativas y componentes aplican + vista ejecutiva."""
    fases_raw = fases_raw or {}
    modalidad = clasificar_modalidad(caso, horas, complejidad, alt, fases_raw)
    modo = modalidad["modo"]
    matriz = MATRIZ_COMPONENTES.get(modo, MATRIZ_COMPONENTES["desarrollo_medida"])

    app_anual = float(alt["usd_anual"]) if alt else None
    app_modelo = (alt or {}).get("modelo", {})
    app_nombre_corto = (alt or {}).get("nombre_corto") if alt else None

    externos: dict[str, Any] = {}
    for alt_key in ("freelancer", "empresa", "app"):
        componentes_ids = matriz.get(alt_key, [])
        if alt_key == "app" and not app_anual:
            externos[alt_key] = {
                "aplica": False,
                "total_usd": None,
                "desglose": [],
                "componentes_activos": [],
            }
            continue

        desglose: list[dict[str, Any]] = []
        total = 0.0
        for comp_id in componentes_ids:
            usd = _calcular_componente(
                comp_id,
                alt_key,
                horas=horas,
                hs_discovery_ext=hs_discovery_ext,
                tarifa_freelancer=tarifa_freelancer,
                tarifa_empresa=tarifa_empresa,
                app_anual=app_anual,
                horizonte=horizonte,
                brecha_usd=brecha_app,
                modo=modo,
                fases_raw=fases_raw,
                app_modelo=app_modelo,
            )
            if usd > 0:
                desglose.append(
                    {
                        "id": comp_id,
                        "label": LABELS_COMPONENTE[comp_id],
                        "usd": usd,
                    }
                )
                total += usd

        aplica = len(desglose) > 0 and (alt_key != "app" or horas > 0 or app_anual)
        if alt_key == "app":
            aplica = app_anual is not None and total > 0

        externos[alt_key] = {
            "aplica": aplica,
            "total_usd": round(total, 2) if aplica else None,
            "desglose": desglose,
            "componentes_activos": [d["id"] for d in desglose],
        }

    ahorros: list[tuple[str, float]] = []
    for key, ext in externos.items():
        if ext["aplica"] and ext["total_usd"] is not None:
            ahorros.append((key, round(ext["total_usd"] - inversion_usd, 2)))

    mejor_key = max(ahorros, key=lambda x: x[1])[0] if ahorros else None
    mejor_ahorro = max((a[1] for a in ahorros), default=0.0)
    mejor_total = externos[mejor_key]["total_usd"] if mejor_key else None
    ahorro_pct = (
        round(100 * mejor_ahorro / mejor_total, 0)
        if mejor_key and mejor_total and mejor_total > 0
        else None
    )

    barras: list[dict[str, Any]] = [
        {"id": "top", "label": "TOP", "usd": round(inversion_usd, 2), "aplica": True},
    ]
    for key in ("freelancer", "empresa", "app"):
        ext = externos[key]
        label = LABELS_EXTERNO[key]
        if key == "app" and app_nombre_corto:
            label = app_nombre_corto[:28]
        barras.append(
            {
                "id": key,
                "label": label,
                "usd": ext["total_usd"] or 0,
                "aplica": ext["aplica"],
            }
        )

    if mejor_key and mejor_ahorro > 0:
        veredicto_corto = f"TOP ahorra US$ {mejor_ahorro:,.0f} vs {LABELS_EXTERNO[mejor_key].lower()}"
    elif mejor_key and mejor_ahorro < 0:
        veredicto_corto = f"Revisar: externo más barato en {LABELS_EXTERNO[mejor_key].lower()}"
    else:
        veredicto_corto = "TOP — sin alternativa comparable"

    return {
        **modalidad,
        "externos": externos,
        "ejecutivo": {
            "veredicto_corto": veredicto_corto,
            "mejor_externo": mejor_key,
            "mejor_externo_label": LABELS_EXTERNO.get(mejor_key or "", ""),
            "ahorro_usd": round(mejor_ahorro, 2) if mejor_key else None,
            "ahorro_pct": ahorro_pct,
            "barras": barras,
        },
    }
