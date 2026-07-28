"""Servicio de gestión de órdenes y estadísticas de ventas."""

from datetime import datetime
from typing import Optional

from database.db_manager import DatabaseManager
from database.models import Orden, OrdenItem, row_to_model
import config as app_config


class OrdenService:
    """Maneja órdenes, items, delivery y estadísticas de ventas."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self._db = db or DatabaseManager()
        # Cache manual: evita el memory leak de @lru_cache en métodos de instancia
        self._cache: dict = {}

    def _clear_cache(self):
        """Invalida todas las caches de consultas de órdenes."""
        self._cache.clear()

    # ─── GENERACIÓN DE NÚMERO ───

    def _generar_numero_orden(self) -> str:
        """Genera número de orden único basado en fecha + secuencia atómica.

        NOTA: Debe llamarse dentro de una transacción BEGIN IMMEDIATE activa
        para garantizar atomicidad y evitar duplicados.
        """
        hoy = datetime.now().strftime("%Y%m%d")
        row = self._db.conn.execute(
            "SELECT MAX(CAST(SUBSTR(numero, 10) AS INTEGER)) as max_seq "
            "FROM ordenes WHERE numero LIKE ?",
            (f"{hoy}-%",)
        ).fetchone()
        seq = (row["max_seq"] or 0) + 1
        return f"{hoy}-{seq:04d}"

    # ─── CRUD DE ÓRDENES ───

    def crear_orden(self, orden: Orden) -> Orden:
        """Crea una orden completa (cabecera + items) de forma atómica."""
        self._clear_cache()
        ahora = datetime.now().isoformat()
        subtotal = sum(item.subtotal for item in orden.items)
        total_sin_delivery = round(subtotal + orden.costo_delivery, 2)
        impuesto = round(subtotal * app_config.TAX_RATE, 2)
        total = round(total_sin_delivery + impuesto, 2)

        try:
            self._db.conn.execute("BEGIN IMMEDIATE")

            # Número generado DENTRO de la transacción para evitar race condition
            numero = self._generar_numero_orden()

            cur = self._db.conn.execute(
                "INSERT INTO ordenes (numero, tipo, estado, subtotal, impuesto, total, "
                "cliente_nombre, notas, direccion, telefono_contacto, costo_delivery, "
                "tiempo_estimado, fecha_creacion, fecha_actualizacion) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (numero, orden.tipo, "pending", subtotal, impuesto, total,
                 orden.cliente_nombre, orden.notas,
                 orden.direccion, orden.telefono_contacto, orden.costo_delivery,
                 orden.tiempo_estimado, ahora, ahora)
            )
            orden_id = cur.lastrowid

            for item in orden.items:
                self._db.conn.execute(
                    "INSERT INTO orden_items (orden_id, producto_id, producto_nombre, "
                    "cantidad, precio_unitario) VALUES (?, ?, ?, ?, ?)",
                    (orden_id, item.producto_id, item.producto_nombre,
                     item.cantidad, item.precio_unitario)
                )

            # Crear transacción contable
            desc = f"Venta #{numero} ({orden.tipo})"
            if orden.costo_delivery > 0:
                desc += f" + Delivery {app_config.CURRENCY_SYMBOL}{orden.costo_delivery:.2f}"
            self._db.conn.execute(
                "INSERT INTO transacciones (tipo, monto, descripcion, fecha, categoria, referencia_orden_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("ingreso", total, desc, ahora, "Ventas POS", orden_id)
            )

            self._db.conn.commit()
        except Exception:
            self._db.conn.rollback()
            raise

        orden.id = orden_id
        orden.numero = numero
        orden.subtotal = subtotal
        orden.impuesto = impuesto
        orden.total = total
        orden.fecha_creacion = ahora
        orden.fecha_actualizacion = ahora
        return orden

    def get_ordenes(self, fecha: Optional[str] = None,
                    estado: Optional[str] = None,
                    limit: int = 50) -> tuple:
        """Retorna órdenes filtradas. Usa cache manual invalidable."""
        key = ("ordenes", fecha, estado, limit)
        if key in self._cache:
            return self._cache[key]

        q = "SELECT * FROM ordenes"
        params = []
        conditions = []
        if fecha:
            conditions.append("fecha_creacion LIKE ?")
            params.append(f"{fecha}%")
        if estado:
            conditions.append("estado = ?")
            params.append(estado)
        if conditions:
            q += " WHERE " + " AND ".join(conditions)
        q += " ORDER BY fecha_creacion DESC LIMIT ?"
        params.append(limit)
        rows = self._db.conn.execute(q, params).fetchall()
        result = tuple(row_to_model(Orden, r) for r in rows)
        self._cache[key] = result
        return result

    def get_ordenes_con_items_count(self, fecha: Optional[str] = None,
                                    estado: Optional[str] = None,
                                    limit: int = 50) -> tuple:
        """Retorna órdenes con conteo de items en UNA sola query (evita N+1)."""
        key = ("ordenes_count", fecha, estado, limit)
        if key in self._cache:
            return self._cache[key]

        q = """
            SELECT o.*, COALESCE(SUM(oi.cantidad), 0) as items_count
            FROM ordenes o
            LEFT JOIN orden_items oi ON o.id = oi.orden_id
        """
        params = []
        conditions = []
        if fecha:
            conditions.append("o.fecha_creacion LIKE ?")
            params.append(f"{fecha}%")
        if estado:
            conditions.append("o.estado = ?")
            params.append(estado)
        if conditions:
            q += " WHERE " + " AND ".join(conditions)
        q += " GROUP BY o.id ORDER BY o.fecha_creacion DESC LIMIT ?"
        params.append(limit)
        rows = self._db.conn.execute(q, params).fetchall()
        result_list = []
        for r in rows:
            d = dict(r)
            items_count = d.pop("items_count", 0)
            result_list.append({"orden": row_to_model(Orden, d), "items_count": items_count})
        result = tuple(result_list)
        self._cache[key] = result
        return result

    def get_orden_items(self, orden_id: int) -> list[OrdenItem]:
        rows = self._db.conn.execute(
            "SELECT * FROM orden_items WHERE orden_id = ?", (orden_id,)
        ).fetchall()
        return [row_to_model(OrdenItem, r) for r in rows]

    def actualizar_estado_orden(self, orden_id: int, nuevo_estado: str):
        self._clear_cache()
        ahora = datetime.now().isoformat()
        self._db.conn.execute(
            "UPDATE ordenes SET estado=?, fecha_actualizacion=? WHERE id=?",
            (nuevo_estado, ahora, orden_id)
        )
        self._db.conn.commit()

    # ─── DELIVERY ───

    def get_ordenes_delivery_pendientes(self) -> list[Orden]:
        """Órdenes delivery listas para asignar."""
        rows = self._db.conn.execute(
            "SELECT * FROM ordenes WHERE tipo='delivery' AND estado IN ('pending', 'preparing', 'ready') "
            "ORDER BY fecha_creacion ASC"
        ).fetchall()
        return [row_to_model(Orden, r) for r in rows]

    def get_ordenes_en_delivery(self) -> list[Orden]:
        """Órdenes actualmente en delivery (en camino)."""
        rows = self._db.conn.execute(
            "SELECT * FROM ordenes WHERE estado='en_delivery' ORDER BY fecha_actualizacion DESC"
        ).fetchall()
        return [row_to_model(Orden, r) for r in rows]

    def get_entregas_hoy(self) -> list[Orden]:
        """Todas las entregas del día."""
        hoy = datetime.now().strftime("%Y-%m-%d")
        rows = self._db.conn.execute(
            "SELECT * FROM ordenes WHERE tipo='delivery' "
            "AND fecha_creacion LIKE ? ORDER BY fecha_creacion DESC",
            (f"{hoy}%",)
        ).fetchall()
        return [row_to_model(Orden, r) for r in rows]

    # ─── ESTADÍSTICAS ───

    def get_ventas_dia(self, fecha: Optional[str] = None) -> dict:
        if not fecha:
            fecha = datetime.now().strftime("%Y-%m-%d")
        row = self._db.conn.execute(
            "SELECT COUNT(*) as total_ordenes, COALESCE(SUM(total), 0) as total_ventas "
            "FROM ordenes WHERE fecha_creacion LIKE ? AND estado != 'cancelled'",
            (f"{fecha}%",)
        ).fetchone()
        return dict(row)

    def get_ventas_por_periodo(self, dias: int = 7) -> list[dict]:
        rows = self._db.conn.execute(
            "SELECT DATE(fecha_creacion) as fecha, COUNT(*) as ordenes, "
            "COALESCE(SUM(total), 0) as ventas "
            "FROM ordenes WHERE estado != 'cancelled' "
            "AND fecha_creacion >= DATE('now', ? || ' days') "
            "GROUP BY DATE(fecha_creacion) ORDER BY fecha",
            (f"-{dias}",)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_conteo_por_estado(self) -> dict:
        rows = self._db.conn.execute(
            "SELECT estado, COUNT(*) as cnt FROM ordenes "
            "WHERE fecha_creacion LIKE ? GROUP BY estado",
            (f"{datetime.now().strftime('%Y-%m-%d')}%",)
        ).fetchall()
        return {r["estado"]: r["cnt"] for r in rows}

    # ─── COMBOS ───

    def get_combos(self, solo_activos: bool = False) -> list:
        """Retorna combos con items cargados en UNA sola query (evita N+1)."""
        from database.models import Combo, ComboItem

        q = "SELECT * FROM combos"
        if solo_activos:
            q += " WHERE activo = 1"
        q += " ORDER BY nombre"
        rows = self._db.conn.execute(q).fetchall()
        combos = [row_to_model(Combo, r) for r in rows]
        if not combos:
            return combos

        combo_ids = [c.id for c in combos]
        placeholders = ",".join("?" for _ in combo_ids)
        items_rows = self._db.conn.execute(
            f"SELECT ci.*, p.nombre as producto_nombre FROM combo_items ci "
            f"JOIN productos p ON ci.producto_id = p.id "
            f"WHERE ci.combo_id IN ({placeholders}) ORDER BY ci.id",
            combo_ids
        ).fetchall()

        items_by_combo: dict[int, list] = {}
        for r in items_rows:
            item = row_to_model(ComboItem, r)
            items_by_combo.setdefault(item.combo_id, []).append(item)

        for c in combos:
            c.items = items_by_combo.get(c.id, [])

        return combos

    def get_combo_items(self, combo_id: int) -> list:
        from database.models import ComboItem
        rows = self._db.conn.execute(
            "SELECT ci.*, p.nombre as producto_nombre FROM combo_items ci "
            "JOIN productos p ON ci.producto_id = p.id "
            "WHERE ci.combo_id = ?", (combo_id,)
        ).fetchall()
        return [row_to_model(ComboItem, r) for r in rows]

    def crear_combo(self, combo) -> int:
        ahora = datetime.now().isoformat()
        cur = self._db.conn.execute(
            "INSERT INTO combos (nombre, descripcion, precio_total, ahorro, icono, activo, fecha_creacion) "
            "VALUES (?, ?, ?, ?, ?, 1, ?)",
            (combo.nombre, combo.descripcion, combo.precio_total, combo.ahorro, combo.icono, ahora)
        )
        combo_id = cur.lastrowid
        for item in combo.items:
            self._db.conn.execute(
                "INSERT INTO combo_items (combo_id, producto_id, producto_nombre, cantidad, precio_individual) "
                "VALUES (?, ?, ?, ?, ?)",
                (combo_id, item.producto_id, item.producto_nombre, item.cantidad, item.precio_individual)
            )
        self._db.conn.commit()
        return combo_id

    def eliminar_combo(self, combo_id: int):
        self._db.conn.execute("DELETE FROM combos WHERE id=?", (combo_id,))
        self._db.conn.commit()

    def toggle_combo(self, combo_id: int):
        self._db.conn.execute(
            "UPDATE combos SET activo = NOT activo WHERE id=?", (combo_id,)
        )
        self._db.conn.commit()
