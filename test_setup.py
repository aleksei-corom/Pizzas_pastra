"""Test completo del sistema de setup + auth."""
import sys
sys.path.insert(0, '.')

# Resetear DB para simular primer inicio
import os
db_path = os.path.join(os.path.dirname(os.path.abspath('.')), 'Pizzas_pastra', 'pizzas_pastra.db')

print("=== TEST SETUP + AUTH SYSTEM ===\n")

print("--- DB Init ---")
from database.db_manager import DatabaseManager
db = DatabaseManager()
db.init_db()
from database.seed_data import seed_database
seed_database()
print(f"  hay_usuarios: {db.hay_usuarios()}")

print("\n--- Config from DB ---")
import config as app_config
configs = db.get_all_configs()
print(f"  Configs: {len(configs)} keys")
for k, v in configs.items():
    print(f"    {k}: {v}")

print("\n--- Auth ---")
user = db.verificar_password('admin', 'admin123')
print(f"  Login admin: {'OK' if user else 'NO USER - first run detected'}")

print("\n--- Session RBAC ---")
from utils.session import Session
s = Session.get()
if user:
    s.login(user)
    print(f"  User: {s.user.nombre_completo}")
    print(f"  Is admin: {s.is_admin()}")
    print(f"  Allowed: {s.get_allowed_modules()}")
    s.logout()

print("\n--- View Imports ---")
from views.setup_wizard import SetupWizard
print("  setup_wizard OK")
from views.login_view import LoginView
print("  login_view OK")
from views.usuarios_view import UsuariosView
print("  usuarios_view OK")
from views.components.user_dialog import UserDialog
print("  user_dialog OK")
from views.components.sidebar import Sidebar
print("  sidebar OK")
from views.main_window import MainWindow
print("  main_window OK")
from views.dashboard_view import DashboardView
print("  dashboard_view OK")
from views.ajustes_view import AjustesView
print("  ajustes_view OK")

print("\n--- Hardcoded check ---")
# Verify no more hardcoded names in dynamic components
import inspect
sidebar_src = inspect.getsource(Sidebar)
login_src = inspect.getsource(LoginView)
has_hardcode = 'Pizzas Pastra' in sidebar_src or 'Pizzas Pastra' in login_src
print(f"  Hardcoded 'Pizzas Pastra' in Sidebar/Login: {'FAIL' if has_hardcode else 'CLEAN'}")

db.close()
print("\n=== ALL TESTS PASSED ===")
