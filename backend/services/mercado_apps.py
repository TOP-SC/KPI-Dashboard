"""Catálogo de apps reales del mercado para comparativos (no usa columnas del Drive)."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
CATALOGO_PATH = ROOT / "data" / "catalogo_mercado.json"


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
        return {"apps": {}, "caso_overrides": {}, "nota": ""}
    return json.loads(CATALOGO_PATH.read_text(encoding="utf-8"))


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
        "fuente": "Catálogo mercado SaaS (precios públicos orientativos)",
    }
