"""Catálogo de apps reales del mercado para comparativos (no usa columnas del Drive)."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
CATALOGO_PATH = ROOT / "data" / "catalogo_mercado.json"

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


def _texto_busqueda(caso: dict[str, Any]) -> str:
    partes = [
        caso.get("reporte"),
        caso.get("origen"),
        caso.get("origen_solicitante"),
        caso.get("usuario"),
        caso.get("herramienta"),
        caso.get("en_arg"),
        caso.get("obs"),
    ]
    return " ".join(str(p) for p in partes if p).lower()


@lru_cache(maxsize=1)
def _cargar_catalogo() -> dict[str, Any]:
    if not CATALOGO_PATH.exists():
        return {"apps": {}, "caso_overrides": {}, "modelos_default": {}, "nota": ""}
    return json.loads(CATALOGO_PATH.read_text(encoding="utf-8"))


def _modelo_costo_app(app: dict[str, Any]) -> str:
    explicito = app.get("modelo_costo")
    if explicito in ("saas", "enterprise"):
        return explicito
    if app.get("categoria") in CATEGORIAS_ENTERPRISE:
        return "enterprise"
    if float(app.get("usd_anual", 0)) >= 10000:
        return "enterprise"
    return "saas"


def _params_modelo(app: dict[str, Any], catalogo: dict[str, Any]) -> dict[str, float]:
    defaults = catalogo.get("modelos_default", {})
    tipo = _modelo_costo_app(app)
    base = defaults.get(tipo, {})
    return {
        "modelo_costo": tipo,
        "implementacion_pct": float(app.get("implementacion_pct", base.get("implementacion_pct", 0))),
        "mantenimiento_pct_anual": float(
            app.get("mantenimiento_pct_anual", base.get("mantenimiento_pct_anual", 0))
        ),
        "brecha_factor": float(app.get("brecha_factor", base.get("brecha_factor", 1.0))),
    }


def _score_app(texto: str, app: dict[str, Any]) -> int:
    score = 0
    for kw in app.get("keywords", []):
        if kw.lower() in texto:
            score += 4
    categoria = app.get("categoria", "")
    if categoria and categoria.replace("_", " ") in texto:
        score += 2
    return score


def resolver_alternativa(caso: dict[str, Any]) -> dict[str, Any] | None:
    """
    Resuelve la app de mercado más comparable al caso.
    Prioridad: override por listado → scoring por keywords del catálogo.
    """
    catalogo = _cargar_catalogo()
    apps: dict[str, dict] = catalogo.get("apps", {})
    if not apps:
        return None

    listado = str(caso.get("listado", "")).strip()
    overrides: dict[str, str] = catalogo.get("caso_overrides", {})

    app_id = overrides.get(listado)
    match_por = "catalogo: override por tipo de caso"

    if not app_id:
        texto = _texto_busqueda(caso)
        mejor_id = None
        mejor_score = 0
        for aid, app in apps.items():
            s = _score_app(texto, app)
            if s > mejor_score:
                mejor_score = s
                mejor_id = aid
        if mejor_id and mejor_score >= 4:
            app_id = mejor_id
            match_por = f"catalogo: similitud por keywords (score {mejor_score})"

    if not app_id or app_id not in apps:
        return None

    app = apps[app_id]
    modelo = _params_modelo(app, catalogo)
    alternativas = [
        apps[aid]["nombre"]
        for aid, alt in apps.items()
        if aid != app_id and alt.get("categoria") == app.get("categoria")
    ][:3]

    return {
        "app_id": app_id,
        "nombre": app["nombre"],
        "nombre_corto": app["nombre"].split("(")[0].strip()[:80],
        "categoria": app.get("categoria", ""),
        "usd_anual": float(app["usd_anual"]),
        "pricing_ref": app.get("pricing_ref", ""),
        "match_por": match_por,
        "alternativas": alternativas,
        "modelo_costo": modelo["modelo_costo"],
        "modelo": modelo,
        "fuente": "Catálogo mercado SaaS (precios públicos orientativos)",
    }
