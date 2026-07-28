"""Tests avanzados para AuthService — hash legacy, get_usuario_by_username, hay_usuarios, get_usuarios con filtros."""

import unittest
import sys
import os
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.auth_service import AuthService
from database.models import Usuario
import config as app_config


class TestAuthServiceAdvanced(unittest.TestCase):
    """Pruebas avanzadas para AuthService — métodos no cubiertos por tests básicos."""

    def setUp(self):
        app_config.DB_PATH = ":memory:"
        DatabaseManager._instance = None
        self.db = DatabaseManager()
        self.db.init_db()
        self.auth_svc = AuthService(self.db)

    def tearDown(self):
        self.db.close()
        DatabaseManager._instance = None

    # ─── get_usuario_by_username ───

    def test_get_usuario_by_username_exists(self):
        """get_usuario_by_username debe retornar el usuario si existe."""
        uid = self.auth_svc.crear_usuario("jdoe", "pass123", "John Doe", "cajero")
        user = self.auth_svc.get_usuario_by_username("jdoe")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, uid)
        self.assertEqual(user.username, "jdoe")
        self.assertEqual(user.nombre_completo, "John Doe")
        self.assertEqual(user.rol, "cajero")
        self.assertTrue(user.activo)

    def test_get_usuario_by_username_not_found(self):
        """get_usuario_by_username debe retornar None si no existe."""
        user = self.auth_svc.get_usuario_by_username("noexiste")
        self.assertIsNone(user)

    def test_get_usuario_by_username_inactive_user(self):
        """get_usuario_by_username debe encontrar usuarios inactivos también."""
        uid = self.auth_svc.crear_usuario("inactivo", "pass", "Inactivo", "cajero")
        self.auth_svc.actualizar_usuario(uid, "Inactivo", "cajero", False)
        user = self.auth_svc.get_usuario_by_username("inactivo")
        self.assertIsNotNone(user)
        self.assertFalse(user.activo)

    # ─── get_usuarios con filtro solo_activos ───

    def test_get_usuarios_solo_activos_filters_inactive(self):
        """get_usuarios(solo_activos=True) no debe incluir usuarios inactivos."""
        uid1 = self.auth_svc.crear_usuario("activo1", "pass", "Activo", "cajero")
        uid2 = self.auth_svc.crear_usuario("inactivo1", "pass", "Inactivo", "cajero")
        self.auth_svc.actualizar_usuario(uid2, "Inactivo", "cajero", False)

        todos = self.auth_svc.get_usuarios(solo_activos=False)
        activos = self.auth_svc.get_usuarios(solo_activos=True)

        self.assertEqual(len(todos), 2)
        self.assertEqual(len(activos), 1)
        self.assertEqual(activos[0].username, "activo1")

    def test_get_usuarios_todos_incluye_inactivos(self):
        """get_usuarios(solo_activos=False) debe incluir todos los usuarios."""
        uid1 = self.auth_svc.crear_usuario("user1", "pass", "User1", "cajero")
        uid2 = self.auth_svc.crear_usuario("user2", "pass", "User2", "admin")
        self.auth_svc.actualizar_usuario(uid1, "User1", "cajero", False)

        todos = self.auth_svc.get_usuarios(solo_activos=False)
        self.assertEqual(len(todos), 2)

    # ─── hay_usuarios ───

    def test_hay_usuarios_empty(self):
        """hay_usuarios debe retornar False si no hay usuarios."""
        self.assertFalse(self.auth_svc.hay_usuarios())

    def test_hay_usuarios_with_users(self):
        """hay_usuarios debe retornar True si hay usuarios."""
        self.auth_svc.crear_usuario("user", "pass", "User", "cajero")
        self.assertTrue(self.auth_svc.hay_usuarios())

    # ─── Legacy hash migration ───

    def test_legacy_hash_migration(self):
        """verificar_password con hash legacy (SHA-256) debe migrar a PBKDF2."""
        import os as _os

        # Generar salt como lo haría el AuthService actual
        salt = _os.urandom(32).hex()  # 64 hex chars

        # Calcular hash legacy como se hacía antes: SHA-256(salt[:32] + password)
        legacy_salt_part = salt[:32]
        password = "mypassword"
        legacy_hash = hashlib.sha256(
            f"{legacy_salt_part}{password}".encode("utf-8")
        ).hexdigest()

        # Insertar usuario directamente con el hash legacy
        from datetime import datetime
        ahora = datetime.now().isoformat()
        self.db.conn.execute(
            "INSERT INTO usuarios (username, password_hash, salt, nombre_completo, "
            "rol, activo, fecha_creacion) VALUES (?, ?, ?, ?, ?, 1, ?)",
            ("legacy_user", legacy_hash, salt, "Legacy User", "cajero", ahora)
        )
        self.db.conn.commit()

        # Verificar que el login funciona con el hash legacy
        user = self.auth_svc.verificar_password("legacy_user", "mypassword")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "legacy_user")
        self.assertEqual(user.nombre_completo, "Legacy User")

        # Verificar que el hash fue migrado en DB (el nuevo hash es diferente del legacy)
        row = self.db.conn.execute(
            "SELECT password_hash FROM usuarios WHERE username = ?",
            ("legacy_user",)
        ).fetchone()
        migrated_hash = row["password_hash"]
        self.assertNotEqual(migrated_hash, legacy_hash,
                            "El hash debe haber sido migrado de SHA-256 a PBKDF2")

        # Verificar que el nuevo hash funciona con el método actual
        user2 = self.auth_svc.verificar_password("legacy_user", "mypassword")
        self.assertIsNotNone(user2)

    def test_legacy_hash_migration_wrong_password(self):
        """verificar_password con hash legacy y contraseña incorrecta debe retornar None."""
        import os as _os

        salt = _os.urandom(32).hex()
        legacy_salt_part = salt[:32]
        legacy_hash = hashlib.sha256(
            f"{legacy_salt_part}correctpass".encode("utf-8")
        ).hexdigest()

        from datetime import datetime
        ahora = datetime.now().isoformat()
        self.db.conn.execute(
            "INSERT INTO usuarios (username, password_hash, salt, nombre_completo, "
            "rol, activo, fecha_creacion) VALUES (?, ?, ?, ?, ?, 1, ?)",
            ("legacy_user2", legacy_hash, salt, "Legacy User 2", "cajero", ahora)
        )
        self.db.conn.commit()

        # Contraseña incorrecta
        user = self.auth_svc.verificar_password("legacy_user2", "wrongpass")
        self.assertIsNone(user)

    # ─── verificar_password con usuario inactivo ───

    def test_verificar_password_inactive_user(self):
        """verificar_password con usuario inactivo debe retornar None."""
        uid = self.auth_svc.crear_usuario("inactive", "pass123", "Inactive", "cajero")
        self.auth_svc.actualizar_usuario(uid, "Inactive", "cajero", False)

        user = self.auth_svc.verificar_password("inactive", "pass123")
        self.assertIsNone(user)

    # ─── Contar admins con mezcla de activos/inactivos ───

    def test_contar_admins_mixed_active_inactive(self):
        """contar_admins_activos solo debe contar admins activos."""
        uid1 = self.auth_svc.crear_usuario("admin1", "pass", "Admin1", "admin")
        uid2 = self.auth_svc.crear_usuario("admin2", "pass", "Admin2", "admin")
        self.auth_svc.actualizar_usuario(uid2, "Admin2", "admin", False)
        self.auth_svc.crear_usuario("cajero1", "pass", "Cajero1", "cajero")

        self.assertEqual(self.auth_svc.contar_admins_activos(), 1)

    # ─── actualizar_usuario ───

    def test_actualizar_usuario_changes_fields(self):
        """actualizar_usuario debe cambiar nombre_completo, rol y activo."""
        uid = self.auth_svc.crear_usuario("testuser", "pass", "Original", "cajero")
        self.auth_svc.actualizar_usuario(uid, "Modificado", "admin", False)

        user = self.auth_svc.get_usuario_by_username("testuser")
        self.assertEqual(user.nombre_completo, "Modificado")
        self.assertEqual(user.rol, "admin")
        self.assertFalse(user.activo)


if __name__ == '__main__':
    unittest.main()
