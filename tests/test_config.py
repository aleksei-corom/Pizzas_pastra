"""Tests unitarios para ConfigService."""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.config_service import ConfigService
import config as app_config


class TestConfig(unittest.TestCase):
    def setUp(self):
        app_config.DB_PATH = ":memory:"
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None
        self.db = DatabaseManager()
        self.db.init_db()
        self.cfg_svc = ConfigService(self.db)
        # Crear usuarios base para tests de preferencias (FK a usuarios)
        ahora = "2026-06-01T00:00:00"
        self.db.conn.execute(
            "INSERT INTO usuarios (username, password_hash, salt, nombre_completo, rol, activo, fecha_creacion) "
            "VALUES (?, ?, ?, ?, ?, 1, ?)",
            ("test_user", "hash", "salt", "Test User", "cajero", ahora)
        )
        self.db.conn.execute(
            "INSERT INTO usuarios (username, password_hash, salt, nombre_completo, rol, activo, fecha_creacion) "
            "VALUES (?, ?, ?, ?, ?, 1, ?)",
            ("test_user2", "hash", "salt", "Test User 2", "admin", ahora)
        )
        self.db.conn.commit()

    def tearDown(self):
        self.db.close()
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None

    # ─── CONFIGURACIÓN GLOBAL ───

    def test_set_and_get_config(self):
        self.cfg_svc.set_config("business_name", "Pizzas Pastra")
        valor = self.cfg_svc.get_config("business_name")
        self.assertEqual(valor, "Pizzas Pastra")

    def test_get_config_no_existe_retorna_none(self):
        valor = self.cfg_svc.get_config("clave_inexistente")
        self.assertIsNone(valor)

    def test_set_config_actualiza_valor_existente(self):
        self.cfg_svc.set_config("tax_rate", "0.15")
        self.cfg_svc.set_config("tax_rate", "0.19")
        valor = self.cfg_svc.get_config("tax_rate")
        self.assertEqual(valor, "0.19")

    def test_get_all_configs(self):
        self.cfg_svc.set_config("clave_a", "valor_a")
        self.cfg_svc.set_config("clave_b", "valor_b")
        todo = self.cfg_svc.get_all_configs()
        self.assertEqual(len(todo), 2)
        self.assertEqual(todo["clave_a"], "valor_a")
        self.assertEqual(todo["clave_b"], "valor_b")

    def test_get_all_configs_vacio(self):
        todo = self.cfg_svc.get_all_configs()
        self.assertEqual(todo, {})

    # ─── PREFERENCIAS DE USUARIO ───

    def test_set_and_get_user_preference(self):
        self.cfg_svc.set_user_preference(1, "tema", "oscuro")
        valor = self.cfg_svc.get_user_preference(1, "tema")
        self.assertEqual(valor, "oscuro")

    def test_get_user_preference_no_existe_retorna_none(self):
        valor = self.cfg_svc.get_user_preference(1, "inexistente")
        self.assertIsNone(valor)

    def test_preferencias_son_por_usuario(self):
        self.cfg_svc.set_user_preference(1, "tema", "oscuro")
        self.cfg_svc.set_user_preference(2, "tema", "claro")
        self.assertEqual(self.cfg_svc.get_user_preference(1, "tema"), "oscuro")
        self.assertEqual(self.cfg_svc.get_user_preference(2, "tema"), "claro")

    def test_set_user_preference_actualiza(self):
        self.cfg_svc.set_user_preference(1, "tema", "oscuro")
        self.cfg_svc.set_user_preference(1, "tema", "claro")
        valor = self.cfg_svc.get_user_preference(1, "tema")
        self.assertEqual(valor, "claro")

    def test_get_all_user_preferences(self):
        self.cfg_svc.set_user_preference(1, "tema", "oscuro")
        self.cfg_svc.set_user_preference(1, "idioma", "es")
        prefs = self.cfg_svc.get_all_user_preferences(1)
        self.assertEqual(len(prefs), 2)
        self.assertEqual(prefs["tema"], "oscuro")
        self.assertEqual(prefs["idioma"], "es")

    def test_get_all_user_preferences_solo_de_ese_usuario(self):
        self.cfg_svc.set_user_preference(1, "tema", "oscuro")
        self.cfg_svc.set_user_preference(2, "tema", "claro")
        prefs_u1 = self.cfg_svc.get_all_user_preferences(1)
        self.assertEqual(len(prefs_u1), 1)
        self.assertEqual(prefs_u1["tema"], "oscuro")

    def test_get_all_user_preferences_vacio(self):
        prefs = self.cfg_svc.get_all_user_preferences(99)
        self.assertEqual(prefs, {})

    # ─── PERSISTENCIA (misma DB, no in-memory) ───

    def test_config_persiste_en_db(self):
        """Verifica que los valores persisten creando un nuevo ConfigService sobre la misma DB."""
        self.cfg_svc.set_config("business_name", "Pizzas Pastra")
        otro_svc = ConfigService(self.db)
        valor = otro_svc.get_config("business_name")
        self.assertEqual(valor, "Pizzas Pastra")


if __name__ == '__main__':
    unittest.main()
