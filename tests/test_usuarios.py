import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
import config as app_config

class TestUsuarios(unittest.TestCase):
    def setUp(self):
        app_config.DB_PATH = ":memory:"
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None
        self.db = DatabaseManager()
        self.db.init_db()

    def tearDown(self):
        self.db.close()
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None

    def test_creacion_y_verificacion_usuario(self):
        # Crear usuario
        uid = self.db.crear_usuario("jdoe", "pass123", "John Doe", "cajero")
        self.assertIsNotNone(uid)

        # Verificar password correcto
        user = self.db.verificar_password("jdoe", "pass123")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "jdoe")
        self.assertEqual(user.nombre_completo, "John Doe")
        self.assertEqual(user.rol, "cajero")

        # Verificar password incorrecto
        bad_user = self.db.verificar_password("jdoe", "wrongpass")
        self.assertIsNone(bad_user)

    def test_contar_admins(self):
        self.assertEqual(self.db.contar_admins_activos(), 0)
        self.db.crear_usuario("admin1", "pass", "Admin Uno", "admin")
        self.assertEqual(self.db.contar_admins_activos(), 1)
        self.db.crear_usuario("admin2", "pass", "Admin Dos", "admin")
        self.assertEqual(self.db.contar_admins_activos(), 2)

    def test_cambio_password(self):
        uid = self.db.crear_usuario("user", "oldpass", "Test", "cajero")
        self.db.cambiar_password(uid, "newpass")

        self.assertIsNone(self.db.verificar_password("user", "oldpass"))
        self.assertIsNotNone(self.db.verificar_password("user", "newpass"))

if __name__ == '__main__':
    unittest.main()
