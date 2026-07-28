"""Servicio de configuración y preferencias de usuario."""

from typing import Optional

from database.db_manager import DatabaseManager


class ConfigService:
    """Maneja configuración global del sistema y preferencias por usuario."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self._db = db or DatabaseManager()

    # ─── CONFIGURACIÓN GLOBAL ───

    def get_config(self, clave: str) -> Optional[str]:
        """Obtiene un valor de configuración. Retorna None si no existe."""
        row = self._db.conn.execute(
            "SELECT valor FROM configuracion WHERE clave = ?", (clave,)
        ).fetchone()
        return row["valor"] if row else None

    def set_config(self, clave: str, valor: str):
        """Inserta o actualiza un valor de configuración."""
        self._db.conn.execute(
            "INSERT INTO configuracion (clave, valor) VALUES (?, ?) "
            "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor",
            (clave, valor)
        )
        self._db.conn.commit()

    def get_all_configs(self) -> dict:
        """Retorna todas las configuraciones como diccionario."""
        rows = self._db.conn.execute("SELECT clave, valor FROM configuracion").fetchall()
        return {row["clave"]: row["valor"] for row in rows}

    # ─── PREFERENCIAS POR USUARIO ───

    def get_user_preference(self, user_id: int, clave: str) -> Optional[str]:
        """Obtiene una preferencia específica de un usuario."""
        row = self._db.conn.execute(
            "SELECT valor FROM user_preferences WHERE user_id = ? AND clave = ?",
            (user_id, clave)
        ).fetchone()
        return row["valor"] if row else None

    def set_user_preference(self, user_id: int, clave: str, valor: str):
        """Inserta o actualiza una preferencia de usuario."""
        self._db.conn.execute(
            "INSERT INTO user_preferences (user_id, clave, valor) VALUES (?, ?, ?) "
            "ON CONFLICT(user_id, clave) DO UPDATE SET valor = excluded.valor",
            (user_id, clave, valor)
        )
        self._db.conn.commit()

    def get_all_user_preferences(self, user_id: int) -> dict:
        """Retorna todas las preferencias de un usuario como diccionario."""
        rows = self._db.conn.execute(
            "SELECT clave, valor FROM user_preferences WHERE user_id = ?", (user_id,)
        ).fetchall()
        return {row["clave"]: row["valor"] for row in rows}
