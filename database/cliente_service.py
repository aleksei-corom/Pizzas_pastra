"""Servicio de gestión de clientes y programa de fidelización."""

from datetime import datetime
from typing import Optional

from database.db_manager import DatabaseManager
from database.models import row_to_model, Cliente, ClientePuntosMov, Premio


class ClienteService:
    """Maneja clientes, puntos de fidelización y premios."""

    PUNTOS_POR_DOLAR = 10  # Cada $1 gastado = 10 puntos
    BONO_CUMPLEANOS = 500  # Puntos de regalo en cumpleaños

    def __init__(self, db: Optional[DatabaseManager] = None):
        self._db = db or DatabaseManager()

    # ─── CRUD CLIENTES ─────────────────────────────────────────────────

    def crear_cliente(self, cliente: Cliente) -> int:
        """Crea un nuevo cliente y retorna su ID."""
        ahora = datetime.now().isoformat()
        cur = self._db.conn.execute(
            "INSERT INTO clientes (nombre, telefono, email, puntos, visitas, "
            "total_gastado, ultima_visita, fecha_cumpleanos, fecha_registro, notas) "
            "VALUES (?, ?, ?, 0, 0, 0.0, '', ?, ?, '')",
            (cliente.nombre, cliente.telefono, cliente.email,
             cliente.fecha_cumpleanos, ahora)
        )
        self._db.conn.commit()
        return cur.lastrowid

    def actualizar_cliente(self, cliente: Cliente):
        """Actualiza los datos de un cliente existente."""
        self._db.conn.execute(
            "UPDATE clientes SET nombre=?, telefono=?, email=?, fecha_cumpleanos=?, notas=? "
            "WHERE id=?",
            (cliente.nombre, cliente.telefono, cliente.email,
             cliente.fecha_cumpleanos, cliente.notas, cliente.id)
        )
        self._db.conn.commit()

    def get_cliente(self, cliente_id: int) -> Optional[Cliente]:
        row = self._db.conn.execute(
            "SELECT * FROM clientes WHERE id=?", (cliente_id,)
        ).fetchone()
        return row_to_model(Cliente, row) if row else None

    def buscar_por_telefono(self, telefono: str) -> Optional[Cliente]:
        """Busca cliente por número de teléfono (búsqueda rápida en POS)."""
        tel_limpio = telefono.strip().replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        row = self._db.conn.execute(
            "SELECT * FROM clientes WHERE REPLACE(REPLACE(REPLACE(REPLACE(telefono, '-', ''), ' ', ''), '(', ''), ')', '') = ?",
            (tel_limpio,)
        ).fetchone()
        return row_to_model(Cliente, row) if row else None

    def get_clientes(self, busqueda: str = "", limite: int = 100) -> list[Cliente]:
        """Retorna lista de clientes, opcionalmente filtrados por búsqueda."""
        q = "SELECT * FROM clientes"
        params = []
        if busqueda:
            q += " WHERE nombre LIKE ? OR telefono LIKE ? OR email LIKE ?"
            term = f"%{busqueda}%"
            params.extend([term, term, term])
        q += " ORDER BY ultima_visita DESC, nombre ASC LIMIT ?"
        params.append(limite)
        rows = self._db.conn.execute(q, params).fetchall()
        return [row_to_model(Cliente, r) for r in rows]

    def get_top_clientes(self, limite: int = 10) -> list[dict]:
        """Retorna los mejores clientes por gasto total."""
        rows = self._db.conn.execute(
            "SELECT * FROM clientes ORDER BY total_gastado DESC, visitas DESC LIMIT ?",
            (limite,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_total_clientes(self) -> int:
        row = self._db.conn.execute("SELECT COUNT(*) as cnt FROM clientes").fetchone()
        return row["cnt"]

    # ─── PUNTOS DE FIDELIZACIÓN ─────────────────────────────────────────

    def acumular_puntos(self, cliente_id: int, monto_gastado: float,
                         orden_id: Optional[int] = None) -> int:
        """Acumula puntos por una compra. Retorna puntos ganados."""
        puntos_ganados = int(monto_gastado * self.PUNTOS_POR_DOLAR)
        if puntos_ganados <= 0:
            return 0

        ahora = datetime.now().isoformat()

        # Obtener saldo anterior
        row = self._db.conn.execute(
            "SELECT puntos FROM clientes WHERE id=?", (cliente_id,)
        ).fetchone()
        if not row:
            return 0
        saldo_anterior = row["puntos"]
        saldo_nuevo = saldo_anterior + puntos_ganados

        self._db.conn.execute(
            "INSERT INTO cliente_puntos_mov (cliente_id, tipo, puntos, saldo_anterior, "
            "saldo_nuevo, concepto, orden_id, fecha) VALUES (?, 'acumulado', ?, ?, ?, ?, ?, ?)",
            (cliente_id, puntos_ganados, saldo_anterior, saldo_nuevo,
             f"Compra - {puntos_ganados} pts por ${monto_gastado:.2f}", orden_id, ahora)
        )

        # Verificar bono de cumpleaños
        cliente = self.get_cliente(cliente_id)
        bono = 0
        if cliente and cliente.fecha_cumpleanos:
            try:
                hoy = datetime.now()
                nac = datetime.strptime(cliente.fecha_cumpleanos, "%Y-%m-%d")
                if nac.month == hoy.month and nac.day == hoy.day:
                    saldo_nuevo += self.BONO_CUMPLEANOS
                    bono = self.BONO_CUMPLEANOS
                    self._db.conn.execute(
                        "INSERT INTO cliente_puntos_mov (cliente_id, tipo, puntos, "
                        "saldo_anterior, saldo_nuevo, concepto, fecha) "
                        "VALUES (?, 'bono_cumpleanos', ?, ?, ?, ?, ?)",
                        (cliente_id, self.BONO_CUMPLEANOS, saldo_nuevo - bono,
                         saldo_nuevo, f"Bono de cumpleaños +{self.BONO_CUMPLEANOS} pts!", ahora)
                    )
            except (ValueError, TypeError):
                pass

        # Actualizar cliente
        self._db.conn.execute(
            "UPDATE clientes SET puntos=?, visitas=visitas+1, "
            "total_gastado=total_gastado+?, ultima_visita=? WHERE id=?",
            (saldo_nuevo, monto_gastado, ahora, cliente_id)
        )
        self._db.conn.commit()
        return puntos_ganados + bono

    def canjear_puntos(self, cliente_id: int, puntos_a_canjear: int,
                       concepto: str, premio_id: Optional[int] = None) -> bool:
        """Canjea puntos de un cliente. Retorna True si exitoso."""
        if puntos_a_canjear <= 0:
            return False

        ahora = datetime.now().isoformat()

        row = self._db.conn.execute(
            "SELECT puntos FROM clientes WHERE id=?", (cliente_id,)
        ).fetchone()
        if not row or row["puntos"] < puntos_a_canjear:
            return False

        saldo_anterior = row["puntos"]
        saldo_nuevo = saldo_anterior - puntos_a_canjear

        self._db.conn.execute(
            "INSERT INTO cliente_puntos_mov (cliente_id, tipo, puntos, saldo_anterior, "
            "saldo_nuevo, concepto, fecha) VALUES (?, 'canjeado', ?, ?, ?, ?, ?)",
            (cliente_id, puntos_a_canjear, saldo_anterior, saldo_nuevo, concepto, ahora)
        )
        self._db.conn.execute(
            "UPDATE clientes SET puntos=? WHERE id=?", (saldo_nuevo, cliente_id)
        )
        self._db.conn.commit()
        return True

    def get_historial_puntos(self, cliente_id: int, limite: int = 50) -> list[ClientePuntosMov]:
        """Retorna el historial de movimientos de puntos de un cliente."""
        rows = self._db.conn.execute(
            "SELECT * FROM cliente_puntos_mov WHERE cliente_id=? "
            "ORDER BY fecha DESC LIMIT ?",
            (cliente_id, limite)
        ).fetchall()
        return [row_to_model(ClientePuntosMov, r) for r in rows]

    def get_compras_cliente(self, cliente_id: int, limite: int = 20) -> list[dict]:
        """Retorna las órdenes asociadas a un cliente."""
        rows = self._db.conn.execute(
            "SELECT o.*, cpm.puntos as puntos_ganados "
            "FROM ordenes o "
            "JOIN cliente_puntos_mov cpm ON cpm.orden_id = o.id AND cpm.cliente_id = ? "
            "WHERE o.estado != 'cancelled' "
            "ORDER BY o.fecha_creacion DESC LIMIT ?",
            (cliente_id, limite)
        ).fetchall()
        return [dict(r) for r in rows]

    # ─── PREMIOS ─────────────────────────────────────────────────────────

    def crear_premio(self, premio: Premio) -> int:
        ahora = datetime.now().isoformat()
        cur = self._db.conn.execute(
            "INSERT INTO premios (nombre, descripcion, puntos_requeridos, "
            "descuento_porcentaje, producto_gratis_id, activo) "
            "VALUES (?, ?, ?, ?, ?, 1)",
            (premio.nombre, premio.descripcion, premio.puntos_requeridos,
             premio.descuento_porcentaje, premio.producto_gratis_id)
        )
        self._db.conn.commit()
        return cur.lastrowid

    def get_premios(self, solo_activos: bool = True) -> list[Premio]:
        q = "SELECT * FROM premios"
        if solo_activos:
            q += " WHERE activo = 1"
        q += " ORDER BY puntos_requeridos ASC"
        rows = self._db.conn.execute(q).fetchall()
        return [row_to_model(Premio, r) for r in rows]

    def eliminar_premio(self, premio_id: int):
        self._db.conn.execute("DELETE FROM premios WHERE id=?", (premio_id,))
        self._db.conn.commit()

    # ─── ESTADÍSTICAS ────────────────────────────────────────────────────

    def get_stats_fidelizacion(self) -> dict:
        """Retorna estadísticas generales del programa de fidelización."""
        total = self.get_total_clientes()
        hoy = datetime.now().strftime("%Y-%m-%d")

        nuevos_hoy = self._db.conn.execute(
            "SELECT COUNT(*) as cnt FROM clientes WHERE fecha_registro LIKE ?",
            (f"{hoy}%",)
        ).fetchone()["cnt"]

        puntos_activos = self._db.conn.execute(
            "SELECT COALESCE(SUM(puntos), 0) as total FROM clientes"
        ).fetchone()["total"]

        total_canjeados = self._db.conn.execute(
            "SELECT COALESCE(SUM(ABS(puntos)), 0) as total "
            "FROM cliente_puntos_mov WHERE tipo='canjeado'"
        ).fetchone()["total"]

        return {
            "total_clientes": total,
            "nuevos_hoy": nuevos_hoy,
            "puntos_activos": int(puntos_activos),
            "total_canjeados": int(total_canjeados),
        }
