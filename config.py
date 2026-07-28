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

# Lista de monedas compatibles
CURRENCY_CODES = {
    "USD": {"symbol": "$", "name": "Dólar Estadounidense"},
    "EUR": {"symbol": "€", "name": "Euro"},
    "MXN": {"symbol": "$", "name": "Peso Mexicano"},
    "GTQ": {"symbol": "Q", "name": "Quetzal Guatemalteco"},
    "COP": {"symbol": "$", "name": "Peso Colombiano"},
    "ARS": {"symbol": "$", "name": "Peso Argentino"},
    "CLP": {"symbol": "$", "name": "Peso Chileno"},
    "PEN": {"symbol": "S/", "name": "Sol Peruano"},
    "BOB": {"symbol": "Bs", "name": "Boliviano"},
    "CRC": {"symbol": "₡", "name": "Colón Costarricense"},
    "DOP": {"symbol": "RD$", "name": "Peso Dominicano"},
    "PAB": {"symbol": "B/.", "name": "Balboa Panameño"},
    "VES": {"symbol": "Bs.S", "name": "Bolívar Soberano"},
}

# ─── Rutas de Datos (Producción) ───
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Usar %APPDATA% en Windows para evitar errores de permisos
appdata = os.environ.get("APPDATA")
if appdata:
    APP_DATA_DIR = os.path.join(appdata, "FastBitePOS")
else:
    # Fallback si no está en Windows o no existe APPDATA
    APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".fastbitepos")

def ensure_data_dir() -> str:
    """Crea el directorio de datos si no existe y lo retorna.
    
    Llama esta funcion al inicio de la app (main.py) en vez de ejecutar
    os.makedirs al importar config.py. Esto evita efectos secundarios
    durante imports de prueba y mejora la testabilidad.
    """
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    return APP_DATA_DIR

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
    "en_delivery": "🛵 En Camino",
    "delivered": "📦 Entregado",
    "cancelled": "❌ Cancelado",
}
