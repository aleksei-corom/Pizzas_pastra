"""Servicio de gestión de recetas y análisis de costos.

Este módulo permite construir recetas con desglose de ingredientes,
calcular costos reales por porción y comparar contra el precio de venta
para obtener márgenes y sugerencias de precios.
"""

from datetime import datetime
from typing import Optional

from database.db_manager import DatabaseManager
from database.models import row_to_model, Receta, RecetaIngrediente, Producto


class RecetaService:
    """Maneja recetas, ingredientes y análisis de costos/márgenes."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self._db = db or DatabaseManager()

    # ─── CRUD RECETAS ─────────────────────────────────────────────────

    def crear_receta(self, receta: Receta) -> int:
        """Crea una receta con sus ingredientes y calcula costos."""
        ahora = datetime.now().isoformat()

        # Calcular costos
        costo_total = sum(ing.subtotal for ing in receta.ingredientes)
        costo_porcion = round(costo_total / max(receta.porciones, 1), 2)

        cur = self._db.conn.execute(
            "INSERT INTO recetas (producto_id, nombre, porciones, costo_total, "
            "costo_porcion, activa, fecha_creacion) VALUES (?, ?, ?, ?, ?, 1, ?)",
            (receta.producto_id, receta.nombre, receta.porciones,
             costo_total, costo_porcion, ahora)
        )
        receta_id = cur.lastrowid

        for ing in receta.ingredientes:
            ing.subtotal = round(ing.cantidad * ing.costo_unitario, 2)
            self._db.conn.execute(
                "INSERT INTO receta_ingredientes (receta_id, nombre, cantidad, "
                "unidad, costo_unitario, subtotal) VALUES (?, ?, ?, ?, ?, ?)",
                (receta_id, ing.nombre, ing.cantidad, ing.unidad,
                 ing.costo_unitario, ing.subtotal)
            )

        self._db.conn.commit()
        return receta_id

    def actualizar_receta(self, receta: Receta):
        """Actualiza una receta existente y recalcula costos."""
        costo_total = sum(ing.subtotal for ing in receta.ingredientes)
        costo_porcion = round(costo_total / max(receta.porciones, 1), 2)

        self._db.conn.execute(
            "UPDATE recetas SET nombre=?, porciones=?, costo_total=?, costo_porcion=? "
            "WHERE id=?",
            (receta.nombre, receta.porciones, costo_total, costo_porcion, receta.id)
        )

        # Eliminar ingredientes viejos y reinsertar
        self._db.conn.execute(
            "DELETE FROM receta_ingredientes WHERE receta_id=?", (receta.id,)
        )
        for ing in receta.ingredientes:
            ing.subtotal = round(ing.cantidad * ing.costo_unitario, 2)
            self._db.conn.execute(
                "INSERT INTO receta_ingredientes (receta_id, nombre, cantidad, "
                "unidad, costo_unitario, subtotal) VALUES (?, ?, ?, ?, ?, ?)",
                (receta.id, ing.nombre, ing.cantidad, ing.unidad,
                 ing.costo_unitario, ing.subtotal)
            )

        self._db.conn.commit()

    def get_receta(self, receta_id: int) -> Optional[Receta]:
        """Retorna una receta con sus ingredientes cargados."""
        row = self._db.conn.execute(
            "SELECT * FROM recetas WHERE id=?", (receta_id,)
        ).fetchone()
        if not row:
            return None
        receta = row_to_model(Receta, row)
        receta.ingredientes = self.get_ingredientes(receta_id)
        return receta

    def get_receta_por_producto(self, producto_id: int) -> Optional[Receta]:
        """Retorna la receta asociada a un producto."""
        row = self._db.conn.execute(
            "SELECT * FROM recetas WHERE producto_id=? AND activa=1",
            (producto_id,)
        ).fetchone()
        if not row:
            return None
        receta = row_to_model(Receta, row)
        receta.ingredientes = self.get_ingredientes(receta.id)
        return receta

    def get_recetas(self, solo_activas: bool = True) -> list[Receta]:
        """Retorna todas las recetas con ingredientes."""
        q = "SELECT * FROM recetas"
        if solo_activas:
            q += " WHERE activa = 1"
        q += " ORDER BY nombre"
        rows = self._db.conn.execute(q).fetchall()
        recetas = [row_to_model(Receta, r) for r in rows]
        for rec in recetas:
            rec.ingredientes = self.get_ingredientes(rec.id)
        return recetas

    def eliminar_receta(self, receta_id: int):
        self._db.conn.execute(
            "UPDATE recetas SET activa=0 WHERE id=?", (receta_id,)
        )
        self._db.conn.commit()

    def get_ingredientes(self, receta_id: int) -> list[RecetaIngrediente]:
        rows = self._db.conn.execute(
            "SELECT * FROM receta_ingredientes WHERE receta_id=? ORDER BY id",
            (receta_id,)
        ).fetchall()
        return [row_to_model(RecetaIngrediente, r) for r in rows]

    # ─── ANÁLISIS DE COSTOS Y MÁRGENES ─────────────────────────────────

    def get_analisis_margenes(self) -> list[dict]:
        """Analiza margen de ganancia por producto con receta.

        Compara el costo de la receta contra el precio de venta del producto
        y calcula el margen bruto y el margen con impuesto.

        Returns:
            Lista de dicts con: producto, receta, precio_venta, costo, margen_bruto, margen_neto
        """
        import config as app_config
        impuesto = app_config.TAX_RATE

        rows = self._db.conn.execute(
            "SELECT r.id as receta_id, r.nombre as receta_nombre, r.costo_porcion, r.porciones, "
            "r.costo_total, p.id as producto_id, p.nombre as producto_nombre, "
            "p.precio, p.disponible, c.nombre as categoria_nombre "
            "FROM recetas r "
            "LEFT JOIN productos p ON r.producto_id = p.id "
            "LEFT JOIN categorias c ON p.categoria_id = c.id "
            "WHERE r.activa = 1 AND p.disponible = 1 "
            "ORDER BY c.nombre, p.nombre"
        ).fetchall()

        resultados = []
        for r in rows:
            d = dict(r)
            precio = d["precio"]
            costo = d["costo_porcion"]

            if precio > 0:
                margen_bruto = ((precio - costo) / precio) * 100
                precio_con_iva = precio * (1 + impuesto)
                margen_neto = ((precio_con_iva - costo) / precio_con_iva) * 100
            else:
                margen_bruto = 0
                margen_neto = 0

            # Precio sugerido: costo / (1 - margen_deseado)
            margen_objetivo = 0.65  # 65% de margen bruto objetivo
            if costo > 0:
                precio_sugerido = round(costo / (1 - margen_objetivo), 2)
            else:
                precio_sugerido = 0

            resultados.append({
                "receta_id": d["receta_id"],
                "receta_nombre": d["receta_nombre"],
                "producto_id": d["producto_id"],
                "producto_nombre": d["producto_nombre"],
                "categoria_nombre": d["categoria_nombre"],
                "precio_venta": precio,
                "costo_porcion": costo,
                "porciones": d["porciones"],
                "costo_total": d["costo_total"],
                "margen_bruto": round(margen_bruto, 1),
                "margen_neto": round(margen_neto, 1),
                "precio_sugerido": precio_sugerido,
                "disponible": d["disponible"],
            })

        return resultados

    def get_resumen_costos(self) -> dict:
        """Retorna un resumen general del análisis de costos."""
        analisis = self.get_analisis_margenes()

        if not analisis:
            return {
                "total_recetas": 0,
                "margen_promedio": 0,
                "mejor_margen": None,
                "peor_margen": None,
                "costo_promedio": 0,
            }

        margenes = [a["margen_bruto"] for a in analisis]
        mejores = sorted(analisis, key=lambda x: x["margen_bruto"], reverse=True)
        peores = sorted(analisis, key=lambda x: x["margen_bruto"])

        return {
            "total_recetas": len(analisis),
            "margen_promedio": round(sum(margenes) / len(margenes), 1),
            "mejor_margen": mejores[0] if mejores else None,
            "peor_margen": peores[0] if peores else None,
            "costo_promedio": round(
                sum(a["costo_porcion"] for a in analisis) / len(analisis), 2
            ),
            "productos_bajo_margen": [a for a in analisis if a["margen_bruto"] < 50],
        }

    def get_top_ingredientes_costo(self, limite: int = 10) -> list[dict]:
        """Retorna los ingredientes más costosos agregados por nombre."""
        rows = self._db.conn.execute(
            "SELECT ri.nombre, SUM(ri.subtotal) as costo_total, COUNT(*) as veces_usado "
            "FROM receta_ingredientes ri "
            "JOIN recetas r ON ri.receta_id = r.id AND r.activa = 1 "
            "GROUP BY ri.nombre ORDER BY costo_total DESC LIMIT ?",
            (limite,)
        ).fetchall()
        return [dict(r) for r in rows]
