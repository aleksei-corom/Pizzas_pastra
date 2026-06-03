"""Punto de entrada de FastBite POS."""

import sys
import os

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from utils.app_logging import setup_logging, install_exception_hook
from utils.session import Session
from database.db_manager import DatabaseManager
from database.seed_data import seed_database


def main():
    """Inicializa y ejecuta la aplicación."""
    # Logging y crash handler
    logger = setup_logging()
    install_exception_hook(logger)
    logger.info("Iniciando FastBite POS...")

    # Ejecutar respaldo automático
    from utils.backup_manager import run_daily_backup
    run_daily_backup()

    # Inicializar DB y seed de datos base (categorías, productos)
    db = DatabaseManager()
    db.init_db()
    seed_database()

    # Crear aplicación Qt
    app = QApplication(sys.argv)
    app.setApplicationName("FastBite POS")
    app.setOrganizationName("FastBitePOS")

    # Fuente global
    font = QFont("Segoe UI", 13)
    font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
    app.setFont(font)

    # Cargar config de DB a runtime
    _load_config_from_db(db)

    # ─── Primera ejecución: Setup ───
    if not db.hay_usuarios():
        _run_first_setup(db, logger)

    session = Session.get()

    # ─── Loop: Login → MainWindow → Logout → Login ───
    while True:
        from views.login_view import LoginView
        login = LoginView()
        result = login.exec()

        if result != QDialog.DialogCode.Accepted:
            logger.info("Login cancelado. Cerrando.")
            break

        user = login.logged_user
        session.login(user)
        logger.info(f"Sesión iniciada: {user.username} ({user.rol})")

        from views.main_window import MainWindow
        window = MainWindow()
        window.showMaximized()
        app.exec()

        if not session.is_logged_in:
            logger.info("Sesión cerrada. Volviendo al login...")
            continue
        else:
            logger.info("Aplicación cerrada.")
            break

    db.close()
    logger.info("Fin.")
    sys.exit(0)


def _run_first_setup(db: DatabaseManager, logger):
    """
    Maneja la primera ejecución de FastBite POS.

    Prioridad:
    1. Si existe 'setup_init.ini' (escrito por el instalador Inno Setup),
       lee los datos, puebla la DB y elimina el archivo por seguridad.
    2. Si no existe (modo desarrollo u otras circunstancias),
       muestra el SetupWizard interactivo como respaldo.
    """
    import configparser

    # Buscar setup_init.ini junto al ejecutable (en producción) o en el dir del proyecto (dev)
    if getattr(sys, "frozen", False):
        # Modo ejecutable PyInstaller
        exe_dir = os.path.dirname(sys.executable)
    else:
        # Modo desarrollo
        exe_dir = os.path.dirname(os.path.abspath(__file__))

    ini_path = os.path.join(exe_dir, "setup_init.ini")

    if os.path.exists(ini_path):
        logger.info(f"setup_init.ini encontrado en: {ini_path}. Configurando desde instalador...")
        cfg = configparser.ConfigParser()
        cfg.read(ini_path, encoding="utf-8")

        section = "Setup"
        business_name = cfg.get(section, "BusinessName", fallback="FastBite POS")
        admin_username = cfg.get(section, "AdminUsername", fallback="admin")
        admin_password = cfg.get(section, "AdminPassword", fallback="")

        if not admin_password:
            logger.warning("setup_init.ini no tiene contraseña. Abriendo SetupWizard como respaldo.")
            _show_setup_wizard(db, logger)
        else:
            # Poblar la DB con los datos del instalador
            try:
                db.set_config("business_name", business_name)
                db.crear_usuario(admin_username, admin_password, nombre_completo="Administrador", rol="admin")
                logger.info(f"Setup desde INI completado: negocio='{business_name}', admin='{admin_username}'")
            except Exception as e:
                logger.error(f"Error al poblar DB desde INI: {e}. Abriendo SetupWizard como respaldo.")
                _show_setup_wizard(db, logger)
            finally:
                # Eliminar el INI por seguridad (contiene contraseña en texto plano)
                try:
                    os.remove(ini_path)
                    logger.info("setup_init.ini eliminado por seguridad.")
                except OSError as e:
                    logger.warning(f"No se pudo eliminar setup_init.ini: {e}")
    else:
        logger.info("setup_init.ini no encontrado. Mostrando Setup Wizard interactivo...")
        _show_setup_wizard(db, logger)


def _show_setup_wizard(db: DatabaseManager, logger):
    """Muestra el SetupWizard interactivo. Termina la app si el usuario cancela."""
    from views.setup_wizard import SetupWizard
    wizard = SetupWizard()
    if wizard.exec() != QDialog.DialogCode.Accepted:
        logger.info("Setup cancelado.")
        db.close()
        sys.exit(0)
    logger.info(f"Setup completado: negocio={wizard.result_data.get('business_name')}")


def _load_config_from_db(db: DatabaseManager):
    """Carga configuración de la DB y actualiza los globals de config.py."""
    import config as app_config

    configs = db.get_all_configs()
    if not configs:
        return

    mapping = {
        "business_name": ("APP_NAME", str),
        "business_slogan": ("BUSINESS_SLOGAN", str),
        "business_phone": ("BUSINESS_PHONE", str),
        "business_address": ("BUSINESS_ADDRESS", str),
        "currency_symbol": ("CURRENCY_SYMBOL", str),
        "tax_rate": ("TAX_RATE", float),
    }
    for db_key, (attr, cast) in mapping.items():
        val = configs.get(db_key)
        if val is not None:
            setattr(app_config, attr, cast(val))

    # También actualizar BUSINESS_NAME si business_name existe
    if "business_name" in configs:
        app_config.BUSINESS_NAME = configs["business_name"]


if __name__ == "__main__":
    main()
