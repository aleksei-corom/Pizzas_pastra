"""Servicio de contabilidad — transacciones, ingresos, egresos y balance."""

from typing import Optional

from database.db_manager import DatabaseManager
from database.models import Transaccion, row_to_model


class ContabilidadService:
    """Maneja transacciones contables (ingresos/egresos) y balance."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self._db = db or DatabaseManager()

    def crear_transaccion(self, transaccion: Transaccion) -> int:
        cur = self._db.conn.execute(
            "INSERT INTO transacciones (tipo, monto, descripcion, fecha, categoria, referencia_orden_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (transaccion.tipo, transaccion.monto, transaccion.descripcion, transaccion.fecha,
             transaccion.categoria, transaccion.referencia_orden_id)
        )
        self._db.conn.commit()
        transaccion.id = cur.lastrowid
        return transaccion.id

    def get_transacciones(self, fecha: Optional[str] = None,
                           tipo: Optional[str] = None,
                           categoria: Optional[str] = None,
                           limit: int = 100) -> tuple[Transaccion, ...]:
        q = "SELECT * FROM transacciones"
        params = []
        conditions = []
        if fecha:
            conditions.append("fecha LIKE ?")
            params.append(f"{fecha}%")
        if tipo:
            conditions.append("tipo = ?")
            params.append(tipo)
        if categoria:
            conditions.append("categoria = ?")
            params.append(categoria)
        if conditions:
            q += " WHERE " + " AND ".join(conditions)
        q += " ORDER BY fecha DESC LIMIT ?"
        params.append(limit)
        rows = self._db.conn.execute(q, params).fetchall()
        return tuple(row_to_model(Transaccion, r) for r in rows)

    def get_balance_contable(self) -> dict:
        row = self._db.conn.execute(
            "SELECT "
            "COALESCE(SUM(CASE WHEN tipo = 'ingreso' THEN monto ELSE 0 END), 0) as total_ingresos, "
            "COALESCE(SUM(CASE WHEN tipo = 'egreso' THEN monto ELSE 0 END), 0) as total_egresos "
            "FROM transacciones"
        ).fetchone()

        ingresos = row["total_ingresos"]
        egresos = row["total_egresos"]

        return {
            "total_ingresos": ingresos,
            "total_egresos": egresos,
            "balance_neto": ingresos - egresos
        }
