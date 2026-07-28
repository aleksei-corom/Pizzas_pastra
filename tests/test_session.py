import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from utils.session import Session
from database.models import Usuario

class TestSession(unittest.TestCase):
    def setUp(self):
        # Reset the singleton state
        DatabaseManager._instance = None
        Session._instance = None
        self.db = DatabaseManager()
        self.db.init_db()
        self.session = Session.get()

    def tearDown(self):
        Session._instance = None
        if hasattr(self, 'db'):
            self.db.close()

    def test_singleton(self):
        s1 = Session.get()
        s2 = Session.get()
        self.assertIs(s1, s2)

    def test_login_logout(self):
        self.assertFalse(self.session.is_logged_in)
        self.assertIsNone(self.session.user)
        
        user = Usuario(id=1, username="test_cajero", rol="cajero")
        self.session.login(user)
        
        self.assertTrue(self.session.is_logged_in)
        self.assertEqual(self.session.user.username, "test_cajero")
        
        self.session.logout()
        self.assertFalse(self.session.is_logged_in)

    def test_role_access(self):
        # Test admin
        admin_user = Usuario(id=1, username="test_admin", rol="admin")
        self.session.login(admin_user)
        
        self.assertTrue(self.session.is_admin())
        self.assertTrue(self.session.has_access("dashboard"))
        self.assertTrue(self.session.has_access("contabilidad"))
        self.assertTrue(self.session.has_access("pos"))
        
        # Test cajero
        self.session.logout()
        cajero_user = Usuario(id=2, username="cajero1", rol="cajero")
        self.session.login(cajero_user)
        
        self.assertFalse(self.session.is_admin())
        self.assertTrue(self.session.has_access("pos"))
        self.assertTrue(self.session.has_access("ordenes"))
        self.assertFalse(self.session.has_access("dashboard"))
        self.assertFalse(self.session.has_access("contabilidad"))


class TestSessionAdvanced(unittest.TestCase):
    """Pruebas avanzadas para Session — preferencias, has_access sin login, get_allowed_modules."""

    def setUp(self):
        DatabaseManager._instance = None
        Session._instance = None
        self.db = DatabaseManager()
        self.db.init_db()
        self.session = Session.get()

    def tearDown(self):
        Session._instance = None
        if hasattr(self, 'db'):
            self.db.close()

    # ─── has_access y get_allowed_modules sin login ───

    def test_has_access_not_logged_in(self):
        """has_access sin usuario logueado debe retornar False."""
        self.assertFalse(self.session.has_access("pos"))
        self.assertFalse(self.session.has_access("dashboard"))
        self.assertFalse(self.session.has_access("nonexistent"))

    def test_get_allowed_modules_not_logged_in(self):
        """get_allowed_modules sin usuario logueado debe retornar lista vacía."""
        modules = self.session.get_allowed_modules()
        self.assertEqual(modules, [])

    def test_is_admin_not_logged_in(self):
        """is_admin sin usuario logueado debe retornar False."""
        self.assertFalse(self.session.is_admin())

    # ─── has_access con roles ───

    def test_has_access_admin_all_modules(self):
        """Admin debe tener acceso a todos los módulos definidos en ROLE_ACCESS."""
        from utils.session import ROLE_ACCESS
        admin_user = Usuario(id=1, username="admin", rol="admin")
        self.session.login(admin_user)

        for module in ROLE_ACCESS["admin"]:
            self.assertTrue(self.session.has_access(module),
                            f"Admin debe tener acceso a '{module}'")

    def test_has_access_cajero_limited_modules(self):
        """Cajero debe tener acceso solo a sus módulos."""
        from utils.session import ROLE_ACCESS
        cajero_user = Usuario(id=2, username="cajero", rol="cajero")
        self.session.login(cajero_user)

        for module in ROLE_ACCESS["cajero"]:
            self.assertTrue(self.session.has_access(module),
                            f"Cajero debe tener acceso a '{module}'")

        for module in ROLE_ACCESS["admin"]:
            if module not in ROLE_ACCESS["cajero"]:
                self.assertFalse(self.session.has_access(module),
                                 f"Cajero NO debe tener acceso a '{module}'")

    def test_get_allowed_modules_admin(self):
        """get_allowed_modules para admin debe retornar la lista completa."""
        from utils.session import ROLE_ACCESS
        admin_user = Usuario(id=1, username="admin", rol="admin")
        self.session.login(admin_user)

        modules = self.session.get_allowed_modules()
        self.assertEqual(modules, ROLE_ACCESS["admin"])

    def test_get_allowed_modules_cajero(self):
        """get_allowed_modules para cajero debe retornar su subconjunto."""
        from utils.session import ROLE_ACCESS
        cajero_user = Usuario(id=2, username="cajero", rol="cajero")
        self.session.login(cajero_user)

        modules = self.session.get_allowed_modules()
        self.assertEqual(modules, ROLE_ACCESS["cajero"])

    # ─── Preferencias ───

    def test_get_preference_default(self):
        """get_preference debe retornar default si no está configurada."""
        admin_user = Usuario(id=1, username="admin", rol="admin")
        self.session.login(admin_user)

        value = self.session.get_preference("nonexistent", "default_val")
        self.assertEqual(value, "default_val")

    def test_get_preference_no_default(self):
        """get_preference sin default debe retornar None si no existe."""
        admin_user = Usuario(id=1, username="admin", rol="admin")
        self.session.login(admin_user)

        value = self.session.get_preference("nonexistent")
        self.assertIsNone(value)

    def test_set_and_get_preference(self):
        """set_preference debe guardar y get_preference recuperar."""
        admin_user = Usuario(id=1, username="admin", rol="admin")
        self.session.login(admin_user)

        self.session.set_preference("my_key", "my_value")
        value = self.session.get_preference("my_key")
        self.assertEqual(value, "my_value")

    # ─── Preferencias sin sesión ───

    def test_set_preference_not_logged_in(self):
        """set_preference sin login no debe lanzar error."""
        try:
            self.session.set_preference("key", "value")
        except Exception as e:
            self.fail(f"set_preference sin login lanzó excepción: {e}")

    def test_get_preference_not_logged_in(self):
        """get_preference sin login debe retornar default."""
        value = self.session.get_preference("key", "default")
        self.assertEqual(value, "default")

    # ─── _load_preferences error handling ───

    def test_load_preferences_error_handling(self):
        """_load_preferences con ConfigService roto no debe crashear."""
        admin_user = Usuario(id=1, username="admin", rol="admin")
        self.session.login(admin_user)

        # ConfigService se importa dentro del método desde database.config_service
        with unittest.mock.patch('database.config_service.ConfigService') as MockCfg:
            mock_cfg = unittest.mock.MagicMock()
            mock_cfg.get_all_user_preferences.side_effect = Exception("DB Error")
            MockCfg.return_value = mock_cfg

            # Re-login para disparar _load_preferences con ConfigService mockeado
            self.session.login(admin_user)

            # No debe crashear, debe tener preferencias vacías
            self.assertEqual(self.session.get_preference("any"), None)

    def test_load_preferences_success(self):
        """_load_preferences debe cargar preferencias desde ConfigService."""
        admin_user = Usuario(id=1, username="admin", rol="admin")

        with unittest.mock.patch('database.config_service.ConfigService') as MockCfg:
            mock_cfg = unittest.mock.MagicMock()
            mock_cfg.get_all_user_preferences.return_value = {"printer": "EPSON"}
            MockCfg.return_value = mock_cfg

            self.session.login(admin_user)

            self.assertEqual(self.session.get_preference("printer"), "EPSON")

    # ─── user property ───

    def test_user_property(self):
        """La propiedad user debe retornar el usuario actual."""
        user = Usuario(id=1, username="testuser", nombre_completo="Test User", rol="cajero")
        self.session.login(user)
        self.assertIs(self.session.user, user)
        self.assertEqual(self.session.user.nombre_completo, "Test User")


if __name__ == '__main__':
    unittest.main()
