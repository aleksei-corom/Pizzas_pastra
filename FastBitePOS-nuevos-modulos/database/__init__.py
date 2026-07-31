"""Módulo de base de datos de FastBite POS — CON NUEVOS MÓDULOS.

Reemplaza completamente a database/__init__.py.

Cambios vs original:
- Se agregaron imports para ClienteService, RecetaService, AsistenteService
- Se agregaron modelos nuevos: Cliente, ClientePuntosMov, Premio, Receta, RecetaIngrediente, Insight
"""

from database.db_manager import DatabaseManager
from database.models import (
    Categoria, Producto, Orden, OrdenItem, Usuario, Repartidor, Transaccion,
    Combo, ComboItem,
    # ↓ NUEVOS MODELOS ↓
    Cliente, ClientePuntosMov, Premio,
    Receta, RecetaIngrediente, Insight,
)
from database.auth_service import AuthService
from database.producto_service import ProductoService
from database.orden_service import OrdenService
from database.contabilidad_service import ContabilidadService
from database.repartidor_service import RepartidorService
from database.config_service import ConfigService
# ↓ NUEVOS SERVICIOS ↓
from database.cliente_service import ClienteService
from database.receta_service import RecetaService
from database.asistente_service import AsistenteService
