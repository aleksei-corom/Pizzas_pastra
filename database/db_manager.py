"""Gestor de conexión SQLite singleton — maneja init, migración y conexión thread-safe."""

import sqlite3
import threading
from typing import Optional

import config as app_config


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
                pass
        self.conn.commit()

    def is_empty(self) -> bool:
        """Verifica si la DB está vacía (sin categorías)."""
        row = self.conn.execute("SELECT COUNT(*) as cnt FROM categorias").fetchone()
        return row["cnt"] == 0

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
