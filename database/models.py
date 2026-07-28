"""Modelos de datos para Pizzas Pastra."""

import dataclasses as _dc
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Categoria:
    """Categoría de producto (Pizza, Hamburguesa, Bebida, etc.)."""
    id: Optional[int] = None
    nombre: str = ""
    icono: str = "🍕"
    orden: int = 0
    activa: bool = True


@dataclass
class Producto:
    """Producto del menú."""
    id: Optional[int] = None
    nombre: str = ""
    descripcion: str = ""
    precio: float = 0.0
    categoria_id: int = 0
    categoria_nombre: str = ""
    disponible: bool = True
    icono: str = ""
    tiene_variantes: bool = False


@dataclass
class ProductoVariante:
    """Variante de producto (tamaño: Personal, Mediana, Familiar)."""
    id: Optional[int] = None
    producto_id: int = 0
    nombre: str = ""
    precio_adicional: float = 0.0
    orden: int = 0


@dataclass
class ProductoIngrediente:
    """Ingrediente adicional opcional para un producto."""
    id: Optional[int] = None
    producto_id: Optional[int] = None   # None = disponible para todos
    nombre: str = ""
    precio_adicional: float = 0.0
    categoria: str = "general"
    activo: bool = True


@dataclass
class Combo:
    """Combo / promoción con múltiples productos a precio fijo."""
    id: Optional[int] = None
    nombre: str = ""
    descripcion: str = ""
    precio_total: float = 0.0
    ahorro: float = 0.0               # Cuánto se ahorra vs comprar por separado
    icono: str = "🎉"
    activo: bool = True
    fecha_creacion: str = ""
    items: list = field(default_factory=list)


@dataclass
class ComboItem:
    """Producto dentro de un combo."""
    id: Optional[int] = None
    combo_id: int = 0
    producto_id: int = 0
    producto_nombre: str = ""
    cantidad: int = 1
    precio_individual: float = 0.0


@dataclass
class OrdenItem:
    """Ítem dentro de una orden."""
    id: Optional[int] = None
    orden_id: Optional[int] = None
    producto_id: int = 0
    producto_nombre: str = ""
    cantidad: int = 1
    precio_unitario: float = 0.0

    @property
    def subtotal(self) -> float:
        return self.cantidad * self.precio_unitario


@dataclass
class Repartidor:
    """Repartidor / domiciliario."""
    id: Optional[int] = None
    nombre: str = ""
    telefono: str = ""
    vehiculo: str = "moto"       # moto, carro, bicicleta, pie
    activo: bool = True
    fecha_creacion: str = ""


@dataclass
class Orden:
    """Orden / pedido completo."""
    id: Optional[int] = None
    numero: str = ""
    tipo: str = "local"        # local, takeout, delivery
    estado: str = "pending"    # pending, preparing, ready, delivered, cancelled
    subtotal: float = 0.0
    impuesto: float = 0.0
    total: float = 0.0
    cliente_nombre: str = ""
    notas: str = ""
    fecha_creacion: str = ""
    fecha_actualizacion: str = ""
    items: list = field(default_factory=list)
    # ─── Campos de delivery ───
    direccion: str = ""
    telefono_contacto: str = ""
    costo_delivery: float = 0.0
    tiempo_estimado: int = 0       # minutos
    repartidor_id: Optional[int] = None


@dataclass
class Usuario:
    """Usuario del sistema con rol de acceso."""
    id: Optional[int] = None
    username: str = ""
    password_hash: str = ""
    salt: str = ""
    nombre_completo: str = ""
    rol: str = "cajero"        # 'admin' | 'cajero'
    activo: bool = True
    fecha_creacion: str = ""


@dataclass
class Transaccion:
    """Registro de ingreso o egreso contable."""
    id: Optional[int] = None
    tipo: str = "ingreso"      # 'ingreso' | 'egreso'
    monto: float = 0.0
    descripcion: str = ""
    fecha: str = ""
    categoria: Optional[str] = None
    referencia_orden_id: Optional[int] = None


# ─── Utilidad de conversión ───────────────────────────────────────────────────

def row_to_model(cls, row):
    """Construye un dataclass desde una sqlite3.Row filtrando columnas no definidas en el modelo.

    Evita TypeError si la DB tiene columnas extra (migraciones futuras) que
    aún no están definidas como campos en el dataclass correspondiente.

    Args:
        cls: Clase dataclass destino (Orden, Producto, Categoria, etc.).
        row: sqlite3.Row o dict con los datos de la consulta.

    Returns:
        Instancia del dataclass con los campos conocidos poblados.
    """
    known = {f.name for f in _dc.fields(cls)}
    return cls(**{k: v for k, v in dict(row).items() if k in known})
