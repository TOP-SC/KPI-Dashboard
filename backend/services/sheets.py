import csv
import io
import json
import re
from pathlib import Path
from typing import Any

import httpx

from config import (
    BRECHA_APP_PCT,
    COTIZACION_DOLAR,
    DISCOVERY_EXTERNO_FACTOR,
    DISCOVERY_HS_ALTA,
    DISCOVERY_HS_BAJA,
    DISCOVERY_HS_MEDIA,
    FALLBACK_DATA,
    GOOGLE_CREDENTIALS,
    HORIZONTE_APP_ANIOS,
    SHEET_GID,
    SHEET_ID,
    TARIFA_AHORRO_ARS_H,
    TARIFA_EMPRESA_USD_H,
    TARIFA_FREELANCER_USD_H,
    TARIFA_INVERSION_USD_H,
)
from services.cotizacion import obtener_cotizacion
from services.kpi import calcular_resumen, enriquecer_caso
from services.parser import es_caso_valido, normalize_row, parse_sheet_rows


def _load_fallback() -> list[dict[str, Any]]:
    if not FALLBACK_DATA.exists():
        return []
    return json.loads(FALLBACK_DATA.read_text(encoding="utf-8"))


def _save_cache(raw: list[dict[str, Any]]) -> None:
    FALLBACK_DATA.parent.mkdir(parents=True, exist_ok=True)
    FALLBACK_DATA.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")


def _fetch_public_csv() -> list[dict[str, Any]]:
    url = (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/"
        f"export?format=csv&gid={SHEET_GID}"
    )
    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        text = response.text
        if "<html" in text.lower():
            raise RuntimeError("La sheet requiere autenticación.")

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    return parse_sheet_rows(rows)


def _fetch_with_service_account() -> list[dict[str, Any]]:
    cred_path = Path(GOOGLE_CREDENTIALS)
    if not cred_path.exists():
        raise FileNotFoundError("No se encontró credentials.json")

    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_file(str(cred_path), scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    worksheet = None
    for ws in sheet.worksheets():
        if str(ws.id) == str(SHEET_GID):
            worksheet = ws
            break
    if worksheet is None:
        worksheet = sheet.sheet1

    values = worksheet.get_all_values()
    return parse_sheet_rows(values)


def _parse_markdown_export(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    casos = []
    for line in lines[48:]:
        if not line.startswith("|"):
            continue
        cells = [x.strip() for x in line.split("|")[1:-1]]
        if len(cells) < 3:
            continue
        if cells[1] in ("Listado", "---") or not re.match(r"^\d+$", cells[1]):
            continue
        caso = normalize_row(cells[1:])
        if caso:
            casos.append(caso)
    return casos


def _intentar_fetch_sheet() -> tuple[list[dict[str, Any]], str, str | None]:
    errores: list[str] = []

    if Path(GOOGLE_CREDENTIALS).exists():
        try:
            rows = _fetch_with_service_account()
            if rows:
                return rows, "google_sheets_service_account", None
            errores.append("Service account: la sheet no devolvió filas válidas.")
        except Exception as exc:
            errores.append(f"Service account: {exc}")

    try:
        rows = _fetch_public_csv()
        if rows:
            return rows, "google_sheets_public", None
        errores.append("Export público: no hay filas válidas.")
    except Exception as exc:
        errores.append(f"Export público: {exc}")

    return [], "", " · ".join(errores) if errores else "No se pudo leer Google Sheets."


def _enriquecer_todos(raw: list[dict[str, Any]], cotizacion: float | None = None) -> list[dict[str, Any]]:
    cot = cotizacion if cotizacion is not None else COTIZACION_DOLAR
    return [
        enriquecer_caso(
            caso,
            TARIFA_INVERSION_USD_H,
            TARIFA_AHORRO_ARS_H,
            cot,
            TARIFA_FREELANCER_USD_H,
            TARIFA_EMPRESA_USD_H,
            HORIZONTE_APP_ANIOS,
            {"baja": DISCOVERY_HS_BAJA, "media": DISCOVERY_HS_MEDIA, "alta": DISCOVERY_HS_ALTA},
            DISCOVERY_EXTERNO_FACTOR,
            BRECHA_APP_PCT,
        )
        for caso in raw
    ]


def cargar_casos(force_refresh: bool = False, cotizacion: float | None = None) -> tuple[list[dict[str, Any]], str, list[str]]:
    avisos: list[str] = []

    sheet_raw, fuente_sheet, error_sheet = _intentar_fetch_sheet()
    if sheet_raw:
        sheet_raw = [c for c in sheet_raw if es_caso_valido(c)]
        if sheet_raw:
            _save_cache(sheet_raw)
            return _enriquecer_todos(sheet_raw, cotizacion), fuente_sheet, avisos

    if force_refresh and error_sheet:
        avisos.append(error_sheet)

    fallback = _load_fallback()
    if fallback:
        raw = [c for c in fallback if es_caso_valido(c)]
        if raw:
            if force_refresh:
                avisos.append("Mostrando caché local porque no se pudo leer la sheet en vivo.")
            return _enriquecer_todos(raw, cotizacion), "local_cache", avisos

    export_md = Path(__file__).resolve().parent.parent.parent / "uploads" / "edit-0.md"
    alt_export = (
        Path.home()
        / ".cursor"
        / "projects"
        / "c-Users-juan-billiot-Desktop-Juan-Desarrollo-Tablero-de-KPIs-TOP"
        / "uploads"
        / "edit-0.md"
    )
    for candidate in (export_md, alt_export):
        parsed = _parse_markdown_export(candidate)
        if parsed:
            raw = [c for c in parsed if es_caso_valido(c)]
            if raw:
                if force_refresh:
                    avisos.append("Mostrando exportación local (sheet no disponible).")
                return _enriquecer_todos(raw, cotizacion), "export_local", avisos

    return [], "local_cache", avisos + (["Sin datos disponibles."] if not avisos else [])


def obtener_dashboard(force_refresh: bool = False) -> dict[str, Any]:
    cotizacion, cotizacion_meta = obtener_cotizacion()
    casos, fuente, avisos = cargar_casos(force_refresh=force_refresh, cotizacion=cotizacion)

    return {
        "fuente": fuente,
        "avisos": avisos,
        "parametros": {
            "tarifa_inversion_usd_h": TARIFA_INVERSION_USD_H,
            "tarifa_ahorro_ars_h": TARIFA_AHORRO_ARS_H,
            "cotizacion_dolar": cotizacion,
            "cotizacion_meta": cotizacion_meta,
            "tarifa_freelancer_usd_h": TARIFA_FREELANCER_USD_H,
            "tarifa_empresa_usd_h": TARIFA_EMPRESA_USD_H,
            "horizonte_app_anios": HORIZONTE_APP_ANIOS,
            "discovery_hs_baja": DISCOVERY_HS_BAJA,
            "discovery_hs_media": DISCOVERY_HS_MEDIA,
            "discovery_hs_alta": DISCOVERY_HS_ALTA,
            "discovery_externo_factor": DISCOVERY_EXTERNO_FACTOR,
        },
        "resumen": calcular_resumen(casos),
        "casos": casos,
    }
