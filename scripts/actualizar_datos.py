"""Script para refrescar data/casos.json desde Google Sheets."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))

from config import GOOGLE_CREDENTIALS  # noqa: E402
from services.sheets import (  # noqa: E402
    _fetch_public_csv,
    _fetch_with_service_account,
    _parse_markdown_export,
    _save_cache,
)

OUT = ROOT / "data" / "casos.json"


def main() -> None:
    raw = []
    fuente = "local"

    cred = Path(GOOGLE_CREDENTIALS)
    if cred.exists():
        try:
            raw = _fetch_with_service_account()
            fuente = "google_sheets_service_account"
        except Exception as exc:
            print(f"Service account fallo: {exc}")

    if not raw:
        try:
            raw = _fetch_public_csv()
            fuente = "google_sheets_public"
        except Exception as exc:
            print(f"Export publico fallo: {exc}")

    if not raw:
        alt = (
            Path.home()
            / ".cursor"
            / "projects"
            / "c-Users-juan-billiot-Desktop-Juan-Desarrollo-Tablero-de-KPIs-TOP"
            / "uploads"
            / "edit-0.md"
        )
        raw = _parse_markdown_export(alt)
        fuente = "export_local"

    if not raw:
        print("No se pudieron obtener casos.")
        sys.exit(1)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    _save_cache(raw)
    print(f"OK: {len(raw)} casos guardados en {OUT} (fuente: {fuente})")


if __name__ == "__main__":
    main()
