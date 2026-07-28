"""Servicio de gestión de repartidores / domiciliarios."""

from datetime import datetime
from typing import Optional

from database.db_manager import DatabaseManager
from database.models import Repartidor, row_to_model


class RepartidorService:
    """Maneja repartidores, disponibilidad y asignación a órdenes."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self._db = db or DatabaseManager()

    def get_repartidores(self, solo_activos: bool = False) -> list[Repartidor]:
        q = "SELECT * FROM repartidores"
        if solo_activos:
            q += " WHERE activo = 1"
        q += " ORDER BY nombre"
        rows = self._db.conn.execute(q).fetchall()
        return [row_to_model(Repartidor, r) for r in rows]

    def get_repartidor(self, repartidor_id: int) -> Optional[Repartidor]:
        row = self._db.conn.execute(
            "SELECT * FROM repartidores WHERE id = ?", (repartidor_id,)
        ).fetchone()
        return row_to_model(Repartidor, row) if row else None

    def crear_repartidor(self, rep: Repartidor) -> int:
        ahora = datetime.now().isoformat()
        cur = self._db.conn.execute(
            "INSERT INTO repartidores (nombre, telefono, vehiculo, activo, fecha_creacion) "
            "VALUES (?, ?, ?, 1, ?)",
            (rep.nombre, rep.telefono, rep.vehiculo, ahora)
        )
        self._db.conn.commit()
        return cur.lastrowid

    def actualizar_repartidor(self, rep: Repartidor):
        self._db.conn.execute(
            "UPDATE repartidores SET nombre=?, telefono=?, vehiculo=?, activo=? WHERE id=?",
            (rep.nombre, rep.telefono, rep.vehiculo, int(rep.activo), rep.id)
        )
        self._db.conn.commit()

    def toggle_repartidor(self, rep_id: int):
        self._db.conn.execute(
            "UPDATE repartidores SET activo = NOT activo WHERE id=?", (rep_id,)
        )
        self._db.conn.commit()

    def contar_repartidores_activos(self) -> int:
        row = self._db.conn.execute(
            "SELECT COUNT(*) as cnt FROM repartidores WHERE activo=1"
        ).fetchone()
        return row["cnt"]

    def get_repartidores_disponibles(self) -> list[Repartidor]:
        """Repartidores activos que no están en una entrega activa."""
        rows = self._db.conn.execute(
            "SELECT r.* FROM repartidores r "
            "WHERE r.activo = 1 AND r.id NOT IN ( "
            "  SELECT o.repartidor_id FROM ordenes o "
            "  WHERE o.repartidor_id IS NOT NULL AND o.estado IN ('ready', 'en_delivery') "
            ") "
            "ORDER BY r.nombre"
        ).fetchall()
        return [row_to_model(Repartidor, r) for r in rows]

    def asignar_repartidor(self, orden_id: int, repartidor_id: int) -> bool:
        """Asigna un repartidor a una orden y cambia estado a 'en_delivery'."""
        try:
            self._db.conn.execute(
                "UPDATE ordenes SET repartidor_id=?, estado='en_delivery', "
                "fecha_actualizacion=? WHERE id=?",
                (repartidor_id, datetime.now().isoformat(), orden_id)
            )
            self._db.conn.commit()
            return True
        except Exception:
            return False
