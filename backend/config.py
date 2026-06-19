import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

SHEET_ID = os.getenv("SHEET_ID", "1xjKnaJBcKVPBQAY-DLJQQeFP9oW3A2o5TDszKSJm4_o")
SHEET_GID = os.getenv("SHEET_GID", "1156348848")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS", str(ROOT / "credentials.json"))
FALLBACK_DATA = ROOT / "data" / "casos.json"

TARIFA_INVERSION_USD_H = float(os.getenv("TARIFA_INVERSION_USD_H", "50"))
TARIFA_AHORRO_ARS_H = float(os.getenv("TARIFA_AHORRO_ARS_H", "12000"))
COTIZACION_DOLAR = float(os.getenv("COTIZACION_DOLAR", "1470"))

TARIFA_FREELANCER_USD_H = float(os.getenv("TARIFA_FREELANCER_USD_H", "75"))
TARIFA_EMPRESA_USD_H = float(os.getenv("TARIFA_EMPRESA_USD_H", "100"))
HORIZONTE_APP_ANIOS = int(os.getenv("HORIZONTE_APP_ANIOS", "3"))

# Discovery (pizarra: ~30h referencia; varía por complejidad)
DISCOVERY_HS_BAJA = float(os.getenv("DISCOVERY_HS_BAJA", "10"))
DISCOVERY_HS_MEDIA = float(os.getenv("DISCOVERY_HS_MEDIA", "25"))
DISCOVERY_HS_ALTA = float(os.getenv("DISCOVERY_HS_ALTA", "40"))
# Externo necesita más hs por no conocer la lógica interna
DISCOVERY_EXTERNO_FACTOR = float(os.getenv("DISCOVERY_EXTERNO_FACTOR", "1.5"))
# Brecha de adaptación cuando se elige app comercial (integración + lógica)
BRECHA_APP_PCT = float(os.getenv("BRECHA_APP_PCT", "0.35"))

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8765"))
