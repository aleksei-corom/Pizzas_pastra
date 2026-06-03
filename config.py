"""Configuración global de FastBite POS."""

import os

# ─── Información del Negocio ───
APP_NAME = "FastBite POS"
APP_VERSION = "1.0.0"
BUSINESS_NAME = "FastBite POS"
BUSINESS_SLOGAN = "Gestión de Restaurantes y Comidas Rápidas"
BUSINESS_PHONE = "+58 412-000-0000"
BUSINESS_ADDRESS = "Av. Principal, Local 1"

# ─── Moneda e Impuestos ───
CURRENCY_SYMBOL = "$"
CURRENCY_CODE = "USD"
TAX_RATE = 0.16  # 16% IVA

# ─── Rutas de Datos (Producción) ───
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Usar %APPDATA% en Windows para evitar errores de permisos
appdata = os.environ.get("APPDATA")
if appdata:
    APP_DATA_DIR = os.path.join(appdata, "FastBitePOS")
else:
    # Fallback si no está en Windows o no existe APPDATA
    APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".fastbitepos")

os.makedirs(APP_DATA_DIR, exist_ok=True)

# ─── Base de Datos ───
DB_PATH = os.path.join(APP_DATA_DIR, "fastbitepos.db")

# ─── Dimensiones de Ventana ───
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 750
SIDEBAR_WIDTH = 260

# ─── Tipos de Pedido ───
ORDER_TYPES = {
    "local": "🍽️ Comer Aquí",
    "takeout": "🛍️ Para Llevar",
    "delivery": "🛵 Delivery",
}

# ─── Impresión Térmica (ESC/POS) ───
PRINTER_NAME = ""  # Nombre de impresora predeterminada (vacío = usar la de Windows)
PRINTER_AUTO_CUT = True
PRINTER_PAPER_WIDTH = 48  # 48 para 80mm, 32 para 58mm
PRINTER_CODEPAGE = "cp850"  # cp437 o cp850
PRINTER_PRINT_QR = True  # Incluir código QR en recibos
PRINTER_SAVE_PDF = True  # Guardar copia PDF del recibo antes de imprimir

# ─── Estados de Orden ───
ORDER_STATUS = {
    "pending": "⏳ Pendiente",
    "preparing": "👨‍🍳 En Preparación",
    "ready": "✅ Listo",
    "delivered": "📦 Entregado",
    "cancelled": "❌ Cancelado",
}
