"""Servicio de autenticación y gestión de usuarios."""

import hashlib
import os
import logging
from datetime import datetime
from typing import Optional

from database.db_manager import DatabaseManager
from database.models import Usuario


logger = logging.getLogger(__name__)


class AuthService:
    """Maneja autenticación, creación y gestión de usuarios."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self._db = db or DatabaseManager()

    # ─── Helpers de hash ───

    @staticmethod
    def _generar_salt() -> str:
        """Genera un salt aleatorio de 32 bytes en hex."""
        return os.urandom(32).hex()

    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        """Hashea un password con PBKDF2-HMAC-SHA256 + salt (100,000 iteraciones)."""
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100_000,
        ).hex()

    # ─── Autenticación ───

    def verificar_password(self, username: str, password: str) -> Optional[Usuario]:
        """Verifica credenciales con migración automática de hash legacy."""
        row = self._db.conn.execute(
            "SELECT * FROM usuarios WHERE username = ? AND activo = 1",
            (username,)
        ).fetchone()
        if not row:
            return None

        d = dict(row)
        stored_hash = d["password_hash"]
        stored_salt = d["salt"]

        # 1. Intentar con método actual (PBKDF2)
        if self._hash_password(password, stored_salt) == stored_hash:
            return Usuario(
                id=d["id"], username=d["username"],
                password_hash=stored_hash, salt=stored_salt,
                nombre_completo=d["nombre_completo"], rol=d["rol"],
                activo=bool(d["activo"]), fecha_creacion=d["fecha_creacion"]
            )

        # 2. Fallback: método legacy (SHA-256 directo)
        legacy_salt_bytes = stored_salt[:32] if len(stored_salt) >= 32 else stored_salt
        legacy_hash = hashlib.sha256(
            f"{legacy_salt_bytes}{password}".encode("utf-8")
        ).hexdigest()
        if legacy_hash == stored_hash:
            logger.info(f"Migrando hash de '{username}' de SHA-256 a PBKDF2")
            new_hash = self._hash_password(password, stored_salt)
            self._db.conn.execute(
                "UPDATE usuarios SET password_hash=?, salt=? WHERE id=?",
                (new_hash, stored_salt, d["id"])
            )
            self._db.conn.commit()
            return Usuario(
                id=d["id"], username=d["username"],
                password_hash=new_hash, salt=stored_salt,
                nombre_completo=d["nombre_completo"], rol=d["rol"],
                activo=bool(d["activo"]), fecha_creacion=d["fecha_creacion"]
            )

        return None

    # ─── CRUD de usuarios ───

    def get_usuario_by_username(self, username: str) -> Optional[Usuario]:
        row = self._db.conn.execute(
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
        rows = self._db.conn.execute(q).fetchall()
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
        cur = self._db.conn.execute(
            "INSERT INTO usuarios (username, password_hash, salt, nombre_completo, "
            "rol, activo, fecha_creacion) VALUES (?, ?, ?, ?, ?, 1, ?)",
            (username, pw_hash, salt, nombre_completo, rol, ahora)
        )
        self._db.conn.commit()
        return cur.lastrowid

    def actualizar_usuario(self, user_id: int, nombre_completo: str,
                           rol: str, activo: bool):
        self._db.conn.execute(
            "UPDATE usuarios SET nombre_completo=?, rol=?, activo=? WHERE id=?",
            (nombre_completo, rol, int(activo), user_id)
        )
        self._db.conn.commit()

    def cambiar_password(self, user_id: int, new_password: str):
        """Cambia el password de un usuario (genera nuevo salt)."""
        salt = self._generar_salt()
        pw_hash = self._hash_password(new_password, salt)
        self._db.conn.execute(
            "UPDATE usuarios SET password_hash=?, salt=? WHERE id=?",
            (pw_hash, salt, user_id)
        )
        self._db.conn.commit()

    def hay_usuarios(self) -> bool:
        row = self._db.conn.execute("SELECT COUNT(*) as cnt FROM usuarios").fetchone()
        return row["cnt"] > 0

    def contar_admins_activos(self) -> int:
        row = self._db.conn.execute(
            "SELECT COUNT(*) as cnt FROM usuarios WHERE rol='admin' AND activo=1"
        ).fetchone()
        return row["cnt"]
