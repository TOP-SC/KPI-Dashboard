import re
from typing import Any


def _is_date(value: str) -> bool:
    if not value:
        return False
    return bool(
        re.match(r"^(\d{1,2}[/\-]\d{1,2}([/\-]\d{2,4})?|\d{1,2}/\d{1,2}/\d{4})$", value.strip())
    )


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


def _looks_like_tool(value: str) -> bool:
    if not value:
        return False
    keywords = (
        "script", "python", "vba", "gemini", "chatgpt", "cursor",
        "query", "html", "apps", "power bi", "javascript", "workspace",
    )
    lower = value.lower()
    return any(k in lower for k in keywords) or "+" in value


def _texto(val: Any) -> str:
    return str(val or "").strip()


def es_caso_valido(caso: dict[str, Any]) -> bool:
    """Excluye filas vacias de la sheet (formulas sin caso real)."""
    listado = caso.get("listado")
    try:
        if listado is None or int(listado) <= 0:
            return False
    except (TypeError, ValueError):
        return False

    reporte = _texto(caso.get("reporte"))
    codigo = _texto(caso.get("codigo_unico"))

    if reporte in ("", "0", "-", "—", "N/A", "n/a") or reporte.isdigit():
        if not codigo.startswith("TOP-"):
            return False

    if codigo.startswith("TOP-"):
        return True

    campos = (
        reporte,
        codigo,
        _texto(caso.get("usuario")),
        _texto(caso.get("origen")),
        _texto(caso.get("origen_solicitante")),
        _texto(caso.get("herramienta")),
        _texto(caso.get("fecha_inicio")),
        _texto(caso.get("fecha_final")),
        _texto(caso.get("mercado_similar")),
        _texto(caso.get("valor_mercado")),
        _texto(caso.get("obs")),
    )
    if not any(campos):
        return False

    for key in ("horas_invertidas", "inversion_usd", "reduccion_hs_mes", "ahorro_calculado"):
        val = _parse_num(caso.get(key))
        if val is not None and val > 0:
            return True

    if len(reporte) >= 2 and not reporte.isdigit():
        return True

    return False


def _header_looks_like_sheet(header: list[str]) -> bool:
    if not header:
        return False
    joined = " ".join(h.strip().lower() for h in header)
    return "listado" in joined and ("reporte" in joined or "proceso" in joined)


def _column_map_from_header(header: list[str]) -> dict[str, int | None]:
    norm = [h.strip().lower() for h in header]

    def find(*needles: str) -> int | None:
        for i, h in enumerate(norm):
            if any(n in h for n in needles):
                return i
        return None

    return {
        "listado": find("listado") or 0,
        "codigo_unico": find("codigo", "código"),
        "reporte": find("reporte", "proceso"),
        "origen": find("origen"),
        "usuario": find("usuario"),
        "asignado": find("asignado"),
        "partner": find("partner"),
        "herramienta": find("herramienta"),
        "fecha_inicio": find("fecha inicio", "fecha ini"),
        "fecha_final": find("fecha final", "fecha fin"),
        "prioridad": find("prioridad"),
        "estado_sheet": find("estado"),
        "horas_invertidas": find("horas invertidas", "horas inv"),
        "inversion_usd": find("usd/hora", "50 usd", "inversión", "inversion"),
        "reduccion_hs_mes": find("reduccion", "reducción"),
        "ahorro_calculado": find("12000", "ahorro", "x hora"),
        "mercado_similar": find("mercado", "similar", "aplicación", "aplicacion"),
        "valor_mercado": find("valor aprox", "valor"),
        "en_arg": find("en arg"),
        "obs": find("obs"),
    }


def _cell(row: list[str], idx: int | None) -> str:
    if idx is None or idx < 0 or idx >= len(row):
        return ""
    return row[idx].strip()


def normalize_row_mapped(row: list[str], col: dict[str, int | None]) -> dict[str, Any]:
    listado_raw = _cell(row, col["listado"])
    if not listado_raw or not re.match(r"^\d+$", listado_raw):
        return {}

    listado = int(listado_raw)
    codigo = _cell(row, col["codigo_unico"])
    reporte = _cell(row, col["reporte"])

    horas = _parse_num(_cell(row, col["horas_invertidas"]))
    inversion = _parse_num(_cell(row, col["inversion_usd"]))
    reduccion = _parse_num(_cell(row, col["reduccion_hs_mes"]))
    ahorro = _parse_num(_cell(row, col["ahorro_calculado"]))

    if horas is not None and horas > 2000:
        horas = None
    if reduccion is not None and reduccion > 744:
        reduccion = None
    if inversion is not None and inversion > 500_000:
        inversion = None

    caso = {
        "listado": listado,
        "codigo_unico": codigo,
        "reporte": reporte or codigo or f"Caso {listado}",
        "origen_solicitante": _cell(row, col["origen"]),
        "origen": _cell(row, col["usuario"]),
        "usuario": _cell(row, col["asignado"]),
        "asignado": "",
        "partner": _cell(row, col["partner"]),
        "herramienta": _cell(row, col["herramienta"]),
        "fecha_inicio": _cell(row, col["fecha_inicio"]),
        "fecha_final": _cell(row, col["fecha_final"]),
        "prioridad": _cell(row, col["prioridad"]),
        "estado_sheet": _cell(row, col["estado_sheet"]),
        "horas_invertidas": horas,
        "inversion_usd": inversion,
        "reduccion_hs_mes": reduccion,
        "ahorro_calculado": ahorro,
        "mercado_similar": _cell(row, col["mercado_similar"]),
        "valor_mercado": _cell(row, col["valor_mercado"]),
        "en_arg": _cell(row, col["en_arg"]),
        "obs": _cell(row, col["obs"]),
    }
    return caso if es_caso_valido(caso) else {}


def parse_sheet_rows(rows: list[list[str]]) -> list[dict[str, Any]]:
    if not rows:
        return []

    if _header_looks_like_sheet(rows[0]):
        col = _column_map_from_header(rows[0])
        casos: list[dict[str, Any]] = []
        for row in rows[1:]:
            caso = normalize_row_mapped(row, col)
            if caso:
                casos.append(caso)
        return casos

    casos = []
    for row in rows[1:]:
        caso = normalize_row(row)
        if caso:
            casos.append(caso)
    return casos


def normalize_row(raw: list[str]) -> dict[str, Any]:
    cells = [c.strip() for c in raw]
    while len(cells) < 16:
        cells.append("")

    if not cells[0] or not re.match(r"^\d+$", cells[0]):
        return {}
    if cells[0].lower() == "listado":
        return {}

    listado = int(cells[0])

    fecha_ini_idx = None
    for idx in range(5, min(len(cells), 12)):
        if _is_date(cells[idx]):
            fecha_ini_idx = idx
            break

    if fecha_ini_idx is None:
        reporte = cells[1] if len(cells) > 1 else f"Caso {listado}"
        mercado = ""
        valor_mercado = ""
        for cell in cells[6:]:
            if not cell:
                continue
            if re.search(r"USD\s*\d", cell, re.I) and not valor_mercado:
                valor_mercado = cell
            elif len(cell) > 20 and not mercado:
                mercado = cell

        caso = {
            "listado": listado,
            "codigo_unico": reporte if reporte.startswith("TOP-") else "",
            "reporte": reporte if not reporte.startswith("TOP-") else (cells[2] if len(cells) > 2 else reporte),
            "origen_solicitante": cells[2] if len(cells) > 2 else "",
            "origen": cells[3] if len(cells) > 3 else "",
            "usuario": cells[4] if len(cells) > 4 else "",
            "asignado": cells[5] if len(cells) > 5 else "",
            "partner": "",
            "herramienta": "",
            "fecha_inicio": "",
            "fecha_final": "",
            "horas_invertidas": None,
            "inversion_usd": None,
            "reduccion_hs_mes": None,
            "ahorro_calculado": None,
            "mercado_similar": mercado,
            "valor_mercado": valor_mercado,
            "en_arg": "",
            "obs": "",
        }
        return caso if es_caso_valido(caso) else {}

    fecha_fin_idx = fecha_ini_idx + 1 if _is_date(cells[fecha_ini_idx + 1]) else fecha_ini_idx

    meta = cells[1:fecha_ini_idx]
    codigo = ""
    fields: list[str] = meta

    if meta and re.match(r"^TOP-", meta[0], re.I):
        codigo = meta[0]
        fields = meta[1:]

    slots = ["reporte", "origen_solicitante", "origen", "usuario", "asignado", "partner", "herramienta"]
    mapped = {slot: fields[i] if i < len(fields) else "" for i, slot in enumerate(slots)}

    # Si falta partner/asignado, la herramienta suele ocupar el ultimo slot antes de fechas
    if mapped["herramienta"] == "" and mapped["asignado"] and _looks_like_tool(mapped["asignado"]):
        mapped["herramienta"] = mapped["asignado"]
        mapped["asignado"] = mapped["usuario"] if _looks_like_tool(mapped.get("asignado", "")) else mapped["asignado"]
    if mapped["herramienta"] == "" and mapped["partner"] and _looks_like_tool(mapped["partner"]):
        mapped["herramienta"] = mapped["partner"]
        mapped["partner"] = ""

    # Caso tipico sin partner: ultimo meta es herramienta
    if len(fields) == 5 and _looks_like_tool(fields[-1]):
        mapped["reporte"] = fields[0]
        mapped["origen_solicitante"] = fields[1]
        mapped["origen"] = fields[2]
        mapped["usuario"] = fields[3]
        mapped["herramienta"] = fields[4]
        mapped["asignado"] = ""
        mapped["partner"] = ""

    nums_start = fecha_fin_idx + 1
    nums = cells[nums_start : nums_start + 4]
    while len(nums) < 4:
        nums.append("")

    horas = _parse_num(nums[0])
    inversion = _parse_num(nums[1])
    reduccion = _parse_num(nums[2])
    ahorro = _parse_num(nums[3])

    texts = [t for t in cells[nums_start + 4 : nums_start + 8] if t]

    if horas is not None and horas > 2000:
        horas = None
    if reduccion is not None and reduccion > 744:
        reduccion = None
    if inversion is not None and inversion > 500_000:
        inversion = None

    reporte_final = mapped["reporte"] or codigo or f"Caso {listado}"

    caso = {
        "listado": listado,
        "codigo_unico": codigo if codigo else (mapped["reporte"] if mapped["reporte"].startswith("TOP-") else ""),
        "reporte": reporte_final,
        "origen_solicitante": mapped["origen_solicitante"],
        "origen": mapped["origen"],
        "usuario": mapped["usuario"],
        "asignado": mapped["asignado"],
        "partner": mapped["partner"],
        "herramienta": mapped["herramienta"],
        "fecha_inicio": cells[fecha_ini_idx],
        "fecha_final": cells[fecha_fin_idx] if fecha_fin_idx != fecha_ini_idx else "",
        "horas_invertidas": horas,
        "inversion_usd": inversion,
        "reduccion_hs_mes": reduccion,
        "ahorro_calculado": ahorro,
        "mercado_similar": texts[0] if texts else "",
        "valor_mercado": texts[1] if len(texts) > 1 else "",
        "en_arg": texts[2] if len(texts) > 2 else "",
        "obs": texts[3] if len(texts) > 3 else "",
    }
    return caso if es_caso_valido(caso) else {}
