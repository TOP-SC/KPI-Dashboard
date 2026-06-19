"""Cotización dólar — API con fallback a .env."""
from __future__ import annotations

import os
from typing import Any

import httpx

from config import COTIZACION_DOLAR

TIPOS_VALIDOS = ("oficial", "blue", "bolsa", "contadoconliqui", "mayorista", "tarjeta")


def obtener_cotizacion() -> tuple[float, dict[str, Any]]:
    auto = os.getenv("COTIZACION_AUTO", "true").lower() in ("1", "true", "yes", "si")
    tipo = os.getenv("COTIZACION_TIPO", "blue").lower().strip()
    if tipo not in TIPOS_VALIDOS:
        tipo = "blue"

    meta: dict[str, Any] = {
        "fuente": "manual (.env)",
        "tipo": tipo,
        "auto": auto,
    }

    if not auto:
        return COTIZACION_DOLAR, meta

    try:
        url = f"https://dolarapi.com/v1/dolares/{tipo}"
        with httpx.Client(timeout=8.0) as client:
            r = client.get(url)
            r.raise_for_status()
            data = r.json()
        venta = float(data.get("venta") or data.get("promedio") or 0)
        if venta > 0:
            meta["fuente"] = f"dolarapi.com ({tipo})"
            meta["compra"] = data.get("compra")
            meta["venta"] = venta
            meta["actualizado"] = data.get("fechaActualizacion")
            return round(venta, 2), meta
    except Exception as exc:
        meta["error_api"] = str(exc)

    meta["fuente"] = "manual (.env) — API no disponible"
    return COTIZACION_DOLAR, meta
