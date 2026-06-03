"""Smoke test completo: navega por las 10 vistas programáticamente.

Uso:
    python smoke_test_completo.py [--headless]

Requiere: PySide6, qrcode[pil]
No requiere: pywin32 (opcional, solo Windows)

Exit codes:
    0  — Todas las vistas cargaron correctamente
    1  — Error en alguna vista (traceback)
"""

import sys
import os
import argparse

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ─── Mock de win32print para entornos sin Windows ───
# Esto evita crashes si pywin32 no está instalado (Linux/macOS)
import types
try:
    import win32print  # noqa: F401
except ImportError:
    win32print_module = types.ModuleType("win32print")

    def _enum_printers(*args, **kwargs):
        return []

    def _open_printer(*args, **kwargs):
        raise OSError("pywin32 not available (mock)")

    def _close_printer(*args, **kwargs):
        pass

    def _get_default_printer(*args, **kwargs):
        return None

    def _noop(*args, **kwargs):
        return True

    def _noop_doc(*args, **kwargs):
        return 1

    win32print_module.EnumPrinters = _enum_printers
    win32print_module.OpenPrinter = _open_printer
    win32print_module.ClosePrinter = _close_printer
    win32print_module.GetDefaultPrinter = _get_default_printer
    win32print_module.WritePrinter = _noop
    win32print_module.StartDocPrinter = _noop_doc
    win32print_module.StartPagePrinter = _noop
    win32print_module.EndPagePrinter = _noop
    win32print_module.EndDocPrinter = _noop
    sys.modules["win32print"] = win32print_module


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Smoke test completo de FastBite POS"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Usar plataforma offscreen de Qt (util en CI sin display)",
    )
    args = parser.parse_args()

    # ─── Qt: usar offscreen si --headless ───
    if args.headless:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # ─── Preparar DB ───
    from database.db_manager import DatabaseManager
    from database.seed_data import seed_database
    from utils.session import Session
    from database.models import Usuario

    print("=" * 55)
    print("  SMOKE TEST COMPLETO — FastBite POS")
    print("=" * 55)

    db = DatabaseManager()
    db.init_db()
    if db.is_empty():
        seed_database(db)
    print("[OK] DB inicializada y seed aplicado")

    # ─── Login como admin ───
    session = Session.get()
    row = db.conn.execute(
        "SELECT * FROM usuarios WHERE username = ?", ("admin",)
    ).fetchone()
    if not row:
        print("[FAIL] No se encontro el usuario admin")
        return 1
    user = Usuario(**dict(row))
    session.login(user)
    print(f"[OK] Login como {user.username} ({user.rol})")

    # ─── Crear MainWindow ───
    from views.main_window import MainWindow

    try:
        window = MainWindow()
        print("[OK] MainWindow creada sin errores")
    except Exception as e:
        print(f"[FAIL] MainWindow: {e}")
        return 1

    # ─── Navegar por todas las vistas ───
    vistas = [
        "dashboard",
        "pos",
        "menu",
        "ordenes",
        "domicilios",
        "cocina",
        "reportes",
        "contabilidad",
        "ajustes",
        "usuarios",
    ]

    exitosas = []
    fallidas = []
    omitidas = []

    for name in vistas:
        if name not in window._views:
            omitidas.append(name)
            print(f"[-] Vista '{name}' no permitida para este rol — omitida")
            continue

        try:
            window._navigate(name)
            view = window._views[name]
            if hasattr(view, "cargar_datos"):
                view.cargar_datos()
            exitosas.append(name)
            print(f"[OK] Vista '{name}' — navegacion + datos OK")
        except Exception as e:
            fallidas.append((name, str(e)))
            print(f"[FAIL] Vista '{name}': {e}")

    # ─── Verificar estado de impresora ───
    try:
        window._update_printer_status()
        print(
            "[OK] Printer status check ejecutado — "
            f"texto: {window._printer_status.text()}"
        )
    except Exception as e:
        print(f"[WARN] Printer status check: {e}")

    # ─── Cerrar ───
    window.close()

    # ─── Resultados ───
    print()
    print("=" * 55)
    print("  RESULTADOS")
    print("=" * 55)
    print(f"  Exitosas: {len(exitosas)}/{len(vistas)}")
    if omitidas:
        print(f"  Omitidas: {len(omitidas)} ({', '.join(omitidas)})")
    if fallidas:
        print(f"  Fallidas: {len(fallidas)}")
        for name, err in fallidas:
            print(f"    - {name}: {err}")

    if fallidas:
        print("\n[FAIL] Smoke test completo FALLIDO")
        return 1
    else:
        print("\n[PASS] Smoke test completo SUPERADO")
        return 0


if __name__ == "__main__":
    exit_code = 1  # default: failure
    try:
        exit_code = main()
    finally:
        import sys as _sys
        _sys.stdout.flush()
        _sys.stderr.flush()
        # Forzar salida: los QTimers de Qt mantienen el proceso vivo incluso
        # después de window.close(). os._exit() evita el colgado.
        import os as _os
        _os._exit(exit_code)
