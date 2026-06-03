"""Gestor de base de datos SQLite para FastBite POS."""

import sqlite3
import threading
import hashlib
import os
from datetime import datetime
from typing import Optional

import config as app_config
from database.models import Categoria, Producto, ProductoVariante, ProductoIngrediente, Combo, ComboItem, Orden, OrdenItem, Usuario, Transaccion, Repartidor


class DatabaseManager:
    """Singleton thread-safe para gestionar la conexión SQLite."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._conn = None
                cls._instance._conn_lock = threading.Lock()
        return cls._instance

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            with self._conn_lock:
                if self._conn is None:
                    self._conn = sqlite3.connect(
                        app_config.DB_PATH, check_same_thread=False
                    )
                    self._conn.row_factory = sqlite3.Row
                    self._conn.execute("PRAGMA journal_mode=WAL")
                    self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    def init_db(self):
        """Crea las tablas si no existen."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS categorias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                icono TEXT DEFAULT '🍕',
                orden INTEGER DEFAULT 0,
                activa INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS productos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT DEFAULT '',
                precio REAL NOT NULL DEFAULT 0.0,
                categoria_id INTEGER NOT NULL,
                disponible INTEGER DEFAULT 1,
                icono TEXT DEFAULT '',
                FOREIGN KEY (categoria_id) REFERENCES categorias(id)
            );

            CREATE TABLE IF NOT EXISTS ordenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero TEXT NOT NULL UNIQUE,
                tipo TEXT DEFAULT 'local',
                estado TEXT DEFAULT 'pending',
                subtotal REAL DEFAULT 0.0,
                impuesto REAL DEFAULT 0.0,
                total REAL DEFAULT 0.0,
                cliente_nombre TEXT DEFAULT '',
                notas TEXT DEFAULT '',
                fecha_creacion TEXT NOT NULL,
                fecha_actualizacion TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orden_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                orden_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                producto_nombre TEXT NOT NULL,
                cantidad INTEGER DEFAULT 1,
                precio_unitario REAL NOT NULL,
                FOREIGN KEY (orden_id) REFERENCES ordenes(id) ON DELETE CASCADE,
                FOREIGN KEY (producto_id) REFERENCES productos(id)
            );

            CREATE TABLE IF NOT EXISTS configuracion (
                clave TEXT PRIMARY KEY,
                valor TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                nombre_completo TEXT DEFAULT '',
                rol TEXT DEFAULT 'cajero',
                activo INTEGER DEFAULT 1,
                fecha_creacion TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS transacciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,
                monto REAL NOT NULL,
                descripcion TEXT NOT NULL,
                fecha TEXT NOT NULL,
                categoria TEXT,
                referencia_orden_id INTEGER,
                FOREIGN KEY (referencia_orden_id) REFERENCES ordenes(id)
            );
        """)
        self.conn.commit()
        self._migrate_db()

    def _migrate_db(self):
        """Migra la DB a nuevas versiones agregando columnas y tablas faltantes."""
        migraciones = [
            ("user_preferences", """
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id INTEGER NOT NULL,
                    clave TEXT NOT NULL,
                    valor TEXT NOT NULL,
                    PRIMARY KEY (user_id, clave),
                    FOREIGN KEY (user_id) REFERENCES usuarios(id) ON DELETE CASCADE
                )
            """),
            ("repartidores", """
                CREATE TABLE IF NOT EXISTS repartidores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    telefono TEXT DEFAULT '',
                    vehiculo TEXT DEFAULT 'moto',
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TEXT NOT NULL
                )
            """),
            ("producto_variantes", """
                CREATE TABLE IF NOT EXISTS producto_variantes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto_id INTEGER NOT NULL,
                    nombre TEXT NOT NULL,
                    precio_adicional REAL DEFAULT 0.0,
                    orden INTEGER DEFAULT 0,
                    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
                )
            """),
            ("producto_ingredientes", """
                CREATE TABLE IF NOT EXISTS producto_ingredientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    producto_id INTEGER,
                    nombre TEXT NOT NULL,
                    precio_adicional REAL DEFAULT 0.0,
                    categoria TEXT DEFAULT 'general',
                    activo INTEGER DEFAULT 1,
                    FOREIGN KEY (producto_id) REFERENCES productos(id) ON DELETE CASCADE
                )
            """),
            ("combos", """
                CREATE TABLE IF NOT EXISTS combos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    descripcion TEXT DEFAULT '',
                    precio_total REAL NOT NULL DEFAULT 0.0,
                    ahorro REAL DEFAULT 0.0,
                    icono TEXT DEFAULT '🎉',
                    activo INTEGER DEFAULT 1,
                    fecha_creacion TEXT NOT NULL
                )
            """),
            ("combo_items", """
                CREATE TABLE IF NOT EXISTS combo_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    combo_id INTEGER NOT NULL,
                    producto_id INTEGER NOT NULL,
                    producto_nombre TEXT DEFAULT '',
                    cantidad INTEGER DEFAULT 1,
                    precio_individual REAL DEFAULT 0.0,
                    FOREIGN KEY (combo_id) REFERENCES combos(id) ON DELETE CASCADE,
                    FOREIGN KEY (producto_id) REFERENCES productos(id)
                )
            """),
        ]
        for nombre, sql in migraciones:
            self.conn.execute(sql)

        # Columnas de delivery en ordenes
        columnas_nuevas = [
            ("ordenes", "direccion", "TEXT DEFAULT ''"),
            ("ordenes", "telefono_contacto", "TEXT DEFAULT ''"),
            ("ordenes", "costo_delivery", "REAL DEFAULT 0.0"),
            ("ordenes", "tiempo_estimado", "INTEGER DEFAULT 0"),
            ("ordenes", "repartidor_id", "INTEGER DEFAULT NULL"),
            ("productos", "tiene_variantes", "INTEGER DEFAULT 0"),
        ]
        for tabla, col, tipo in columnas_nuevas:
            try:
                self.conn.execute(f"ALTER TABLE {tabla} ADD COLUMN {col} {tipo}")
            except sqlite3.OperationalError:
                pass  # La columna ya existe
        self.conn.commit()

    def is_empty(self) -> bool:
        """Verifica si la DB está vacía (sin categorías)."""
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM categorias").fetchone()
        return row["cnt"] == 0

    # ─── CATEGORÍAS ───

    def get_categorias(self, solo_activas: bool = True) -> list[Categoria]:
        q = "SELECT * FROM categorias"
        if solo_activas:
            q += " WHERE activa = 1"
        q += " ORDER BY orden, nombre"
        rows = self.conn.execute(q).fetchall()
        return [Categoria(**dict(r)) for r in rows]

    def crear_categoria(self, cat: Categoria) -> int:
        cur = self.conn.execute(
            "INSERT INTO categorias (nombre, icono, orden, activa) VALUES (?, ?, ?, ?)",
            (cat.nombre, cat.icono, cat.orden, int(cat.activa))
        )
        self.conn.commit()
        return cur.lastrowid

    def actualizar_categoria(self, cat: Categoria):
        self.conn.execute(
            "UPDATE categorias SET nombre=?, icono=?, orden=?, activa=? WHERE id=?",
            (cat.nombre, cat.icono, cat.orden, int(cat.activa), cat.id)
        )
        self.conn.commit()

    def eliminar_categoria(self, cat_id: int):
        """Soft-delete: desactiva la categoría en lugar de borrarla."""
        # Verificar si tiene productos activos
        row = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM productos WHERE categoria_id = ? AND disponible = 1",
            (cat_id,)
        ).fetchone()
        if row["cnt"] > 0:
            raise ValueError(
                f"No se puede eliminar: la categoría tiene {row['cnt']} producto(s) activo(s)."
            )
        self.conn.execute(
            "UPDATE categorias SET activa = 0 WHERE id = ?", (cat_id,)
        )
        self.conn.commit()

    # ─── PRODUCTOS ───

    def get_productos(self, categoria_id: Optional[int] = None,
                      solo_disponibles: bool = False) -> list[Producto]:
        q = """
            SELECT p.*, c.nombre as categoria_nombre
            FROM productos p
            JOIN categorias c ON p.categoria_id = c.id
        """
        params = []
        conditions = []
        if categoria_id:
            conditions.append("p.categoria_id = ?")
            params.append(categoria_id)
        if solo_disponibles:
            conditions.append("p.disponible = 1")
        if conditions:
            q += " WHERE " + " AND ".join(conditions)
        q += " ORDER BY c.orden, p.nombre"
        rows = self.conn.execute(q, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            result.append(Producto(
                id=d["id"], nombre=d["nombre"], descripcion=d["descripcion"],
                precio=d["precio"], categoria_id=d["categoria_id"],
                categoria_nombre=d["categoria_nombre"],
                disponible=bool(d["disponible"]), icono=d.get("icono", ""),
                tiene_variantes=bool(d.get("tiene_variantes", 0))
            ))
        return result

    def buscar_productos(self, texto: str) -> list[Producto]:
        q = """
            SELECT p.*, c.nombre as categoria_nombre
            FROM productos p
            JOIN categorias c ON p.categoria_id = c.id
            WHERE p.disponible = 1 AND (p.nombre LIKE ? OR p.descripcion LIKE ?)
            ORDER BY p.nombre
        """
        pat = f"%{texto}%"
        rows = self.conn.execute(q, (pat, pat)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            result.append(Producto(
                id=d["id"], nombre=d["nombre"], descripcion=d["descripcion"],
                precio=d["precio"], categoria_id=d["categoria_id"],
                categoria_nombre=d["categoria_nombre"],
                disponible=bool(d["disponible"]), icono=d.get("icono", ""),
                tiene_variantes=bool(d.get("tiene_variantes", 0))
            ))
        return result

    def crear_producto(self, prod: Producto) -> int:
        cur = self.conn.execute(
            "INSERT INTO productos (nombre, descripcion, precio, categoria_id, disponible, icono) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (prod.nombre, prod.descripcion, prod.precio, prod.categoria_id,
             int(prod.disponible), prod.icono)
        )
        self.conn.commit()
        return cur.lastrowid

    def actualizar_producto(self, prod: Producto):
        self.conn.execute(
            "UPDATE productos SET nombre=?, descripcion=?, precio=?, categoria_id=?, "
            "disponible=?, icono=? WHERE id=?",
            (prod.nombre, prod.descripcion, prod.precio, prod.categoria_id,
             int(prod.disponible), prod.icono, prod.id)
        )
        self.conn.commit()

    def toggle_disponibilidad(self, prod_id: int):
        self.conn.execute(
            "UPDATE productos SET disponible = NOT disponible WHERE id=?", (prod_id,)
        )
        self.conn.commit()

    def eliminar_producto(self, prod_id: int):
        """Soft-delete: marca como no disponible en lugar de borrar.

        Preserva la integridad referencial con orden_items existentes.
        """
        self.conn.execute(
            "UPDATE productos SET disponible = 0 WHERE id = ?", (prod_id,)
        )
        self.conn.commit()

    # ─── ÓRDENES ───

    def _generar_numero_orden(self) -> str:
        """Genera número de orden único basado en fecha + secuencia atómica."""
        hoy = datetime.now().strftime("%Y%m%d")
        row = self.conn.execute(
            "SELECT MAX(CAST(SUBSTR(numero, 10) AS INTEGER)) as max_seq "
            "FROM ordenes WHERE numero LIKE ?",
            (f"{hoy}-%",)
        ).fetchone()
        seq = (row["max_seq"] or 0) + 1
        return f"{hoy}-{seq:04d}"

    def crear_orden(self, orden: Orden) -> Orden:
        """Crea una orden completa (cabecera + items) de forma atómica."""
        ahora = datetime.now().isoformat()
        numero = self._generar_numero_orden()
        subtotal = sum(item.subtotal for item in orden.items)
        # Delivery: el costo de envío NO está sujeto a IVA normalmente
        total_sin_delivery = round(subtotal + orden.costo_delivery, 2)
        impuesto = round(subtotal * app_config.TAX_RATE, 2)
        total = round(total_sin_delivery + impuesto, 2)

        try:
            self.conn.execute("BEGIN IMMEDIATE")

            cur = self.conn.execute(
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
                self.conn.execute(
                    "INSERT INTO orden_items (orden_id, producto_id, producto_nombre, "
                    "cantidad, precio_unitario) VALUES (?, ?, ?, ?, ?)",
                    (orden_id, item.producto_id, item.producto_nombre,
                     item.cantidad, item.precio_unitario)
                )

            # --- Crear transacción contable ---
            desc = f"Venta #{numero} ({orden.tipo})"
            if orden.costo_delivery > 0:
                desc += f" + Delivery {app_config.CURRENCY_SYMBOL}{orden.costo_delivery:.2f}"
            self.conn.execute(
                "INSERT INTO transacciones (tipo, monto, descripcion, fecha, categoria, referencia_orden_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("ingreso", total, desc, ahora, "Ventas POS", orden_id)
            )

            self.conn.commit()
        except Exception:
            self.conn.rollback()
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
                    limit: int = 50) -> list[Orden]:
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
        rows = self.conn.execute(q, params).fetchall()
        return [Orden(**dict(r)) for r in rows]

    def get_ordenes_con_items_count(self, fecha: Optional[str] = None,
                                     estado: Optional[str] = None,
                                     limit: int = 50) -> list[dict]:
        """Retorna órdenes con conteo de items en UNA sola query (evita N+1)."""
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
        rows = self.conn.execute(q, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            items_count = d.pop("items_count", 0)
            result.append({"orden": Orden(**d), "items_count": items_count})
        return result

    def get_orden_items(self, orden_id: int) -> list[OrdenItem]:
        rows = self.conn.execute(
            "SELECT * FROM orden_items WHERE orden_id = ?", (orden_id,)
        ).fetchall()
        return [OrdenItem(**dict(r)) for r in rows]

    def actualizar_estado_orden(self, orden_id: int, nuevo_estado: str):
        ahora = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE ordenes SET estado=?, fecha_actualizacion=? WHERE id=?",
            (nuevo_estado, ahora, orden_id)
        )
        self.conn.commit()

    # ─── REPORTES / ESTADÍSTICAS ───

    def get_ventas_dia(self, fecha: Optional[str] = None) -> dict:
        if not fecha:
            fecha = datetime.now().strftime("%Y-%m-%d")
        row = self.conn.execute(
            "SELECT COUNT(*) as total_ordenes, COALESCE(SUM(total), 0) as total_ventas "
            "FROM ordenes WHERE fecha_creacion LIKE ? AND estado != 'cancelled'",
            (f"{fecha}%",)
        ).fetchone()
        return dict(row)

    def get_productos_populares(self, limit: int = 5) -> list[dict]:
        rows = self.conn.execute(
            "SELECT producto_nombre, SUM(cantidad) as total_cantidad, "
            "SUM(cantidad * precio_unitario) as total_ventas "
            "FROM orden_items oi "
            "JOIN ordenes o ON oi.orden_id = o.id "
            "WHERE o.estado != 'cancelled' "
            "GROUP BY producto_nombre "
            "ORDER BY total_cantidad DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_ventas_por_periodo(self, dias: int = 7) -> list[dict]:
        rows = self.conn.execute(
            "SELECT DATE(fecha_creacion) as fecha, COUNT(*) as ordenes, "
            "COALESCE(SUM(total), 0) as ventas "
            "FROM ordenes WHERE estado != 'cancelled' "
            "AND fecha_creacion >= DATE('now', ? || ' days') "
            "GROUP BY DATE(fecha_creacion) ORDER BY fecha",
            (f"-{dias}",)
        ).fetchall()
        return [dict(r) for r in rows]

    def get_conteo_por_estado(self) -> dict:
        rows = self.conn.execute(
            "SELECT estado, COUNT(*) as cnt FROM ordenes "
            "WHERE fecha_creacion LIKE ? GROUP BY estado",
            (f"{datetime.now().strftime('%Y-%m-%d')}%",)
        ).fetchall()
        return {r["estado"]: r["cnt"] for r in rows}

    # ─── CONFIGURACIÓN ───
    def get_config(self, clave: str) -> Optional[str]:
        """Obtiene un valor de configuración. Retorna None si no existe."""
        row = self.conn.execute(
            "SELECT valor FROM configuracion WHERE clave = ?", (clave,)
        ).fetchone()
        return row["valor"] if row else None

    def set_config(self, clave: str, valor: str):
        """Inserta o actualiza un valor de configuración."""
        self.conn.execute(
            "INSERT INTO configuracion (clave, valor) VALUES (?, ?) "
            "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor",
            (clave, valor)
        )
        self.conn.commit()

    def get_all_configs(self) -> dict:
        """Retorna todas las configuraciones como diccionario."""
        rows = self.conn.execute("SELECT clave, valor FROM configuracion").fetchall()
        return {row["clave"]: row["valor"] for row in rows}

    # ─── PREFERENCIAS POR USUARIO ───

    def get_user_preference(self, user_id: int, clave: str) -> Optional[str]:
        """Obtiene una preferencia específica de un usuario.

        Retorna None si no existe.
        """
        row = self.conn.execute(
            "SELECT valor FROM user_preferences WHERE user_id = ? AND clave = ?",
            (user_id, clave)
        ).fetchone()
        return row["valor"] if row else None

    def set_user_preference(self, user_id: int, clave: str, valor: str):
        """Inserta o actualiza una preferencia de usuario."""
        self.conn.execute(
            "INSERT INTO user_preferences (user_id, clave, valor) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, clave) DO UPDATE SET valor = excluded.valor",
            (user_id, clave, valor)
        )
        self.conn.commit()

    def get_all_user_preferences(self, user_id: int) -> dict:
        """Retorna todas las preferencias de un usuario como diccionario."""
        rows = self.conn.execute(
            "SELECT clave, valor FROM user_preferences WHERE user_id = ?", (user_id,)
        ).fetchall()
        return {row["clave"]: row["valor"] for row in rows}

    # ─── USUARIOS ───

    @staticmethod
    def _generar_salt() -> str:
        """Genera un salt aleatorio de 16 bytes en hex."""
        return os.urandom(16).hex()

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """Hashea un password con SHA-256 + salt."""
        return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()

    def verificar_password(self, username: str, password: str) -> Optional[Usuario]:
        """Verifica credenciales. Retorna Usuario si son válidas, None si no."""
        row = self.conn.execute(
            "SELECT * FROM usuarios WHERE username = ? AND activo = 1",
            (username,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        expected_hash = self._hash_password(password, d["salt"])
        if d["password_hash"] != expected_hash:
            return None
        return Usuario(
            id=d["id"], username=d["username"],
            password_hash=d["password_hash"], salt=d["salt"],
            nombre_completo=d["nombre_completo"], rol=d["rol"],
            activo=bool(d["activo"]), fecha_creacion=d["fecha_creacion"]
        )

    def get_usuario_by_username(self, username: str) -> Optional[Usuario]:
        row = self.conn.execute(
            "SELECT * FROM usuarios WHERE username = ?", (username,)
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        return Usuario(
            id=d["id"], username=d["username"],
            password_hash=d["password_hash"], salt=d["salt"],
            nombre_completo=d["nombre_completo"], rol=d["rol"],
            activo=bool(d["activo"]), fecha_creacion=d["fecha_creacion"]
        )

    def get_usuarios(self, solo_activos: bool = False) -> list[Usuario]:
        q = "SELECT * FROM usuarios"
        if solo_activos:
            q += " WHERE activo = 1"
        q += " ORDER BY nombre_completo"
        rows = self.conn.execute(q).fetchall()
        return [
            Usuario(
                id=r["id"], username=r["username"],
                password_hash=r["password_hash"], salt=r["salt"],
                nombre_completo=r["nombre_completo"], rol=r["rol"],
                activo=bool(r["activo"]), fecha_creacion=r["fecha_creacion"]
            ) for r in rows
        ]

    def crear_usuario(self, username: str, password: str,
                      nombre_completo: str, rol: str = "cajero") -> int:
        """Crea un usuario con password hasheado. Retorna el ID."""
        salt = self._generar_salt()
        pw_hash = self._hash_password(password, salt)
        ahora = datetime.now().isoformat()
        cur = self.conn.execute(
            "INSERT INTO usuarios (username, password_hash, salt, nombre_completo, "
            "rol, activo, fecha_creacion) VALUES (?, ?, ?, ?, ?, 1, ?)",
            (username, pw_hash, salt, nombre_completo, rol, ahora)
        )
        self.conn.commit()
        return cur.lastrowid

    def actualizar_usuario(self, user_id: int, nombre_completo: str,
                            rol: str, activo: bool):
        self.conn.execute(
            "UPDATE usuarios SET nombre_completo=?, rol=?, activo=? WHERE id=?",
            (nombre_completo, rol, int(activo), user_id)
        )
        self.conn.commit()

    def cambiar_password(self, user_id: int, new_password: str):
        """Cambia el password de un usuario (genera nuevo salt)."""
        salt = self._generar_salt()
        pw_hash = self._hash_password(new_password, salt)
        self.conn.execute(
            "UPDATE usuarios SET password_hash=?, salt=? WHERE id=?",
            (pw_hash, salt, user_id)
        )
        self.conn.commit()

    def hay_usuarios(self) -> bool:
        """Verifica si existe al menos un usuario en la DB."""
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM usuarios").fetchone()
        return row["cnt"] > 0

    def contar_admins_activos(self) -> int:
        """Cuenta cuántos administradores activos hay."""
        row = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM usuarios WHERE rol='admin' AND activo=1"
        ).fetchone()
        return row["cnt"]

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ─── REPARTIDORES ───

    def get_repartidores(self, solo_activos: bool = False) -> list[Repartidor]:
        q = "SELECT * FROM repartidores"
        if solo_activos:
            q += " WHERE activo = 1"
        q += " ORDER BY nombre"
        rows = self.conn.execute(q).fetchall()
        return [Repartidor(**dict(r)) for r in rows]

    def get_repartidor(self, repartidor_id: int) -> Optional[Repartidor]:
        row = self.conn.execute(
            "SELECT * FROM repartidores WHERE id = ?", (repartidor_id,)
        ).fetchone()
        return Repartidor(**dict(row)) if row else None

    def crear_repartidor(self, rep: Repartidor) -> int:
        ahora = datetime.now().isoformat()
        cur = self.conn.execute(
            "INSERT INTO repartidores (nombre, telefono, vehiculo, activo, fecha_creacion) "
            "VALUES (?, ?, ?, 1, ?)",
            (rep.nombre, rep.telefono, rep.vehiculo, ahora)
        )
        self.conn.commit()
        return cur.lastrowid

    def actualizar_repartidor(self, rep: Repartidor):
        self.conn.execute(
            "UPDATE repartidores SET nombre=?, telefono=?, vehiculo=?, activo=? WHERE id=?",
            (rep.nombre, rep.telefono, rep.vehiculo, int(rep.activo), rep.id)
        )
        self.conn.commit()

    def toggle_repartidor(self, rep_id: int):
        self.conn.execute(
            "UPDATE repartidores SET activo = NOT activo WHERE id=?", (rep_id,)
        )
        self.conn.commit()

    def contar_repartidores_activos(self) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM repartidores WHERE activo=1"
        ).fetchone()
        return row["cnt"]

    def get_repartidores_disponibles(self) -> list[Repartidor]:
        """Repartidores activos que no están en una entrega activa."""
        rows = self.conn.execute(
            "SELECT r.* FROM repartidores r "
            "WHERE r.activo = 1 AND r.id NOT IN ( "
            "  SELECT o.repartidor_id FROM ordenes o "
            "  WHERE o.repartidor_id IS NOT NULL AND o.estado IN ('ready', 'en_delivery') "
            ") "
            "ORDER BY r.nombre"
        ).fetchall()
        return [Repartidor(**dict(r)) for r in rows]

    def asignar_repartidor(self, orden_id: int, repartidor_id: int) -> bool:
        """Asigna un repartidor a una orden y cambia estado a 'en_delivery'."""
        try:
            self.conn.execute(
                "UPDATE ordenes SET repartidor_id=?, estado='en_delivery', "
                "fecha_actualizacion=? WHERE id=?",
                (repartidor_id, datetime.now().isoformat(), orden_id)
            )
            self.conn.commit()
            return True
        except Exception:
            return False

    # ─── DELIVERY EN ÓRDENES ───

    def get_ordenes_delivery_pendientes(self) -> list[Orden]:
        """Órdenes delivery listas para asignar (estado 'ready' o 'preparing' con tipo delivery)."""
        rows = self.conn.execute(
            "SELECT * FROM ordenes WHERE tipo='delivery' AND estado IN ('pending', 'preparing', 'ready') "
            "ORDER BY fecha_creacion ASC"
        ).fetchall()
        return [Orden(**dict(r)) for r in rows]

    def get_ordenes_en_delivery(self) -> list[Orden]:
        """Órdenes actualmente en delivery."""
        rows = self.conn.execute(
            "SELECT * FROM ordenes WHERE estado='en_delivery' ORDER BY fecha_actualizacion DESC"
        ).fetchall()
        return [Orden(**dict(r)) for r in rows]

    def get_entregas_hoy(self) -> list[Orden]:
        """Todas las entregas del día."""
        hoy = datetime.now().strftime("%Y-%m-%d")
        rows = self.conn.execute(
            "SELECT * FROM ordenes WHERE tipo='delivery' "
            "AND fecha_creacion LIKE ? ORDER BY fecha_creacion DESC",
            (f"{hoy}%",)
        ).fetchall()
        return [Orden(**dict(r)) for r in rows]

    # ─── VARIANTES DE PRODUCTO ───

    def get_variantes(self, producto_id: int) -> list[ProductoVariante]:
        rows = self.conn.execute(
            "SELECT * FROM producto_variantes WHERE producto_id = ? ORDER BY orden",
            (producto_id,)
        ).fetchall()
        return [ProductoVariante(**dict(r)) for r in rows]

    def crear_variante(self, v: ProductoVariante) -> int:
        cur = self.conn.execute(
            "INSERT INTO producto_variantes (producto_id, nombre, precio_adicional, orden) "
            "VALUES (?, ?, ?, ?)",
            (v.producto_id, v.nombre, v.precio_adicional, v.orden)
        )
        self.conn.commit()
        self.conn.execute("UPDATE productos SET tiene_variantes=1 WHERE id=?", (v.producto_id,))
        self.conn.commit()
        return cur.lastrowid

    def eliminar_variante(self, variante_id: int):
        v = self.conn.execute("SELECT producto_id FROM producto_variantes WHERE id=?", (variante_id,)).fetchone()
        prod_id = v["producto_id"] if v else None
        self.conn.execute("DELETE FROM producto_variantes WHERE id=?", (variante_id,))
        self.conn.commit()
        # Desmarcar tiene_variantes si ya no hay más
        if prod_id:
            restantes = self.conn.execute(
                "SELECT COUNT(*) as cnt FROM producto_variantes WHERE producto_id=?", (prod_id,)
            ).fetchone()["cnt"]
            if restantes == 0:
                self.conn.execute("UPDATE productos SET tiene_variantes=0 WHERE id=?", (prod_id,))
                self.conn.commit()

    # ─── INGREDIENTES ADICIONALES ───

    def get_ingredientes(self, producto_id: Optional[int] = None,
                         solo_activos: bool = False) -> list[ProductoIngrediente]:
        if producto_id:
            q = "SELECT * FROM producto_ingredientes WHERE (producto_id = ? OR producto_id IS NULL)"
            params = [producto_id]
            if solo_activos:
                q += " AND activo = 1"
            q += " ORDER BY categoria, nombre"
            rows = self.conn.execute(q, params).fetchall()
        else:
            q = "SELECT * FROM producto_ingredientes"
            if solo_activos:
                q += " WHERE activo = 1"
            q += " ORDER BY categoria, nombre"
            rows = self.conn.execute(q).fetchall()
        return [ProductoIngrediente(**dict(r)) for r in rows]

    def crear_ingrediente(self, ing: ProductoIngrediente) -> int:
        cur = self.conn.execute(
            "INSERT INTO producto_ingredientes (producto_id, nombre, precio_adicional, categoria, activo) "
            "VALUES (?, ?, ?, ?, ?)",
            (ing.producto_id, ing.nombre, ing.precio_adicional, ing.categoria, int(ing.activo))
        )
        self.conn.commit()
        return cur.lastrowid

    def eliminar_ingrediente(self, ing_id: int):
        self.conn.execute("DELETE FROM producto_ingredientes WHERE id=?", (ing_id,))
        self.conn.commit()

    # ─── COMBOS / PROMOCIONES ───

    def get_combos(self, solo_activos: bool = False) -> list[Combo]:
        q = "SELECT * FROM combos"
        if solo_activos:
            q += " WHERE activo = 1"
        q += " ORDER BY nombre"
        rows = self.conn.execute(q).fetchall()
        combos = []
        for r in rows:
            c = Combo(**dict(r))
            c.items = self.get_combo_items(c.id)
            combos.append(c)
        return combos

    def get_combo_items(self, combo_id: int) -> list[ComboItem]:
        rows = self.conn.execute(
            "SELECT ci.*, p.nombre as producto_nombre FROM combo_items ci "
            "JOIN productos p ON ci.producto_id = p.id "
            "WHERE ci.combo_id = ?", (combo_id,)
        ).fetchall()
        return [ComboItem(**dict(r)) for r in rows]

    def crear_combo(self, combo: Combo) -> int:
        ahora = datetime.now().isoformat()
        cur = self.conn.execute(
            "INSERT INTO combos (nombre, descripcion, precio_total, ahorro, icono, activo, fecha_creacion) "
            "VALUES (?, ?, ?, ?, ?, 1, ?)",
            (combo.nombre, combo.descripcion, combo.precio_total, combo.ahorro, combo.icono, ahora)
        )
        combo_id = cur.lastrowid
        for item in combo.items:
            self.conn.execute(
                "INSERT INTO combo_items (combo_id, producto_id, producto_nombre, cantidad, precio_individual) "
                "VALUES (?, ?, ?, ?, ?)",
                (combo_id, item.producto_id, item.producto_nombre, item.cantidad, item.precio_individual)
            )
        self.conn.commit()
        return combo_id

    def eliminar_combo(self, combo_id: int):
        self.conn.execute("DELETE FROM combos WHERE id=?", (combo_id,))
        self.conn.commit()

    def toggle_combo(self, combo_id: int):
        self.conn.execute(
            "UPDATE combos SET activo = NOT activo WHERE id=?", (combo_id,)
        )
        self.conn.commit()

    # ─── CONTABILIDAD ───

    def crear_transaccion(self, transaccion: Transaccion) -> int:
        cur = self.conn.execute(
            "INSERT INTO transacciones (tipo, monto, descripcion, fecha, categoria, referencia_orden_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (transaccion.tipo, transaccion.monto, transaccion.descripcion, transaccion.fecha,
             transaccion.categoria, transaccion.referencia_orden_id)
        )
        self.conn.commit()
        transaccion.id = cur.lastrowid
        return transaccion.id

    def get_transacciones(self, limit: int = 100) -> list[Transaccion]:
        rows = self.conn.execute(
            "SELECT * FROM transacciones ORDER BY fecha DESC LIMIT ?", (limit,)
        ).fetchall()
        return [Transaccion(**dict(r)) for r in rows]

    def get_balance_contable(self) -> dict:
        row = self.conn.execute(
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

