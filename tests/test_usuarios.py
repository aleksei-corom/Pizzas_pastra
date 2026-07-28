import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.auth_service import AuthService
import config as app_config


class TestUsuarios(unittest.TestCase):
    def setUp(self):
        app_config.DB_PATH = ":memory:"
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None
        self.db = DatabaseManager()
        self.db.init_db()
        self.auth_svc = AuthService(self.db)

    def tearDown(self):
        self.db.close()
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None

    def test_creacion_y_verificacion_usuario(self):
        uid = self.auth_svc.crear_usuario("jdoe", "pass123", "John Doe", "cajero")
        self.assertIsNotNone(uid)

        user = self.auth_svc.verificar_password("jdoe", "pass123")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "jdoe")
        self.assertEqual(user.nombre_completo, "John Doe")
        self.assertEqual(user.rol, "cajero")

        bad_user = self.auth_svc.verificar_password("jdoe", "wrongpass")
        self.assertIsNone(bad_user)

    def test_contar_admins(self):
        self.assertEqual(self.auth_svc.contar_admins_activos(), 0)
        self.auth_svc.crear_usuario("admin1", "pass", "Admin Uno", "admin")
        self.assertEqual(self.auth_svc.contar_admins_activos(), 1)
        self.auth_svc.crear_usuario("admin2", "pass", "Admin Dos", "admin")
        self.assertEqual(self.auth_svc.contar_admins_activos(), 2)

    def test_cambio_password(self):
        uid = self.auth_svc.crear_usuario("user", "oldpass", "Test", "cajero")
        self.auth_svc.cambiar_password(uid, "newpass")

        self.assertIsNone(self.auth_svc.verificar_password("user", "oldpass"))
        self.assertIsNotNone(self.auth_svc.verificar_password("user", "newpass"))


if __name__ == '__main__':
    unittest.main()
