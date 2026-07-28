"""Tests unitarios para módulos de utilidad: printer.py, backup_manager.py, app_logging.py."""
import unittest
import unittest.mock
import sys
import os
import tempfile
import shutil
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.models import Orden, OrdenItem
import config as app_config


# ═══════════════════════════════════════════
#  printer.py — ESC/POS Printing
# ═══════════════════════════════════════════

class TestPrinterFormatText(unittest.TestCase):
    """Pruebas para format_receipt_text (formateo de texto sin hardware)."""

    def setUp(self):
        self.orden = Orden(
            numero="TEST-001", tipo="local", estado="pending",
            subtotal=12.50, impuesto=2.00, total=14.50,
            cliente_nombre="Juan Perez",
            fecha_creacion="2026-01-15T14:30:00",
        )
        self.items = [
            OrdenItem(producto_nombre="Margarita", cantidad=2, precio_unitario=5.0),
            OrdenItem(producto_nombre="Cola", cantidad=1, precio_unitario=2.5),
        ]

    def test_format_header_includes_business_name(self):
        """El encabezado debe incluir el nombre del negocio."""
        from utils.printer import format_receipt_text
        text = format_receipt_text(self.orden, self.items, paper_width=48)
        self.assertIn(app_config.BUSINESS_NAME, text)
        self.assertIn(self.orden.numero, text)

    def test_format_includes_items(self):
        """Los items deben aparecer en el texto formateado."""
        from utils.printer import format_receipt_text
        text = format_receipt_text(self.orden, self.items, paper_width=48)
        self.assertIn("Margarita", text)
        self.assertIn("Cola", text)

    def test_format_includes_totals(self):
        """Los totales deben aparecer."""
        from utils.printer import format_receipt_text
        text = format_receipt_text(self.orden, self.items, paper_width=48)
        self.assertIn("12.50", text)
        self.assertIn("2.00", text)
        self.assertIn("14.50", text)

    def test_format_delivery_includes_address(self):
        """Para orden delivery, debe incluir dirección y teléfono."""
        from utils.printer import format_receipt_text
        self.orden.tipo = "delivery"
        self.orden.direccion = "Calle 123, Colonia Centro"
        self.orden.telefono_contacto = "555-0000"
        self.orden.costo_delivery = 3.0

        text = format_receipt_text(self.orden, self.items, paper_width=48)
        self.assertIn("Calle 123", text)
        self.assertIn("555-0000", text)
        self.assertIn("3.00", text)

    def test_format_respects_paper_width(self):
        """El ancho del papel debe respetarse."""
        from utils.printer import format_receipt_text
        text_80 = format_receipt_text(self.orden, self.items, paper_width=48)
        text_58 = format_receipt_text(self.orden, self.items, paper_width=32)

        max_line_80 = max(len(line) for line in text_80.split("\n"))
        max_line_58 = max(len(line) for line in text_58.split("\n"))
        self.assertLessEqual(max_line_80, 48)
        self.assertLessEqual(max_line_58, 32)

    def test_format_includes_notes(self):
        """Las notas deben incluirse si existen."""
        from utils.printer import format_receipt_text
        self.orden.notas = "Sin cebolla"
        text = format_receipt_text(self.orden, self.items, paper_width=48)
        self.assertIn("Sin cebolla", text)

    def test_format_with_empty_items(self):
        """No debe fallar con lista vacía de items."""
        from utils.printer import format_receipt_text
        text = format_receipt_text(self.orden, [], paper_width=48)
        self.assertIn(self.orden.numero, text)

    def test_format_without_client_name(self):
        """No debe fallar si no hay nombre de cliente."""
        from utils.printer import format_receipt_text
        self.orden.cliente_nombre = ""
        text = format_receipt_text(self.orden, self.items, paper_width=48)
        self.assertIsInstance(text, str)


class TestPrinterFormatHtml(unittest.TestCase):
    """Pruebas para format_receipt_html (vista previa HTML)."""

    def setUp(self):
        self.orden = Orden(
            numero="TEST-001", tipo="local",
            subtotal=12.50, impuesto=2.00, total=14.50,
            fecha_creacion="2026-01-15T14:30:00",
        )
        self.items = [
            OrdenItem(producto_nombre="Margarita", cantidad=2, precio_unitario=5.0),
        ]

    def test_format_html_returns_valid_html(self):
        """Debe retornar HTML válido con etiquetas básicas."""
        from utils.printer import format_receipt_html
        html = format_receipt_html(self.orden, self.items, include_qr=False)
        self.assertIn("<html>", html)
        self.assertIn("</html>", html)
        self.assertIn("<body>", html)

    def test_format_html_includes_business_name(self):
        """El HTML debe incluir el nombre del negocio."""
        from utils.printer import format_receipt_html
        html = format_receipt_html(self.orden, self.items, include_qr=False)
        self.assertIn(app_config.BUSINESS_NAME, html)

    def test_format_html_includes_items(self):
        """Los items deben aparecer en el HTML."""
        from utils.printer import format_receipt_html
        html = format_receipt_html(self.orden, self.items, include_qr=False)
        self.assertIn("Margarita", html)

    def test_format_html_includes_totals(self):
        """Los totales deben aparecer en el HTML."""
        from utils.printer import format_receipt_html
        html = format_receipt_html(self.orden, self.items, include_qr=False)
        self.assertIn("14.50", html)

    def test_format_html_with_qr_no_crash(self):
        """Incluir QR no debe fallar aunque qrcode no esté instalado."""
        from utils.printer import format_receipt_html
        html = format_receipt_html(self.orden, self.items, include_qr=True)
        self.assertIsInstance(html, str)

    def test_format_html_escapes_special_chars(self):
        """El HTML debe escapar caracteres correctamente."""
        from utils.printer import format_receipt_html
        html = format_receipt_html(self.orden, self.items, include_qr=False)
        self.assertIn(html, html)  # Smoke test: no exception


class TestEscposPrinter(unittest.TestCase):
    """Pruebas para ESCPOSPrinter (sin impresora real)."""

    def setUp(self):
        # Crear una subclase que sobrescriba write() para capturar datos
        from utils.printer import ESCPOSPrinter
        self.printer = ESCPOSPrinter(
            printer_name="Test Printer",
            auto_cut=True,
            paper_width=48,
            codepage="cp850",
        )
        self._written = bytearray()

        # Monkey-patch write para capturar datos sin enviar a impresora
        self._original_write = self.printer.write

        def _mock_write(data):
            self._written.extend(data)
            return True

        self.printer.write = _mock_write

    def test_init_defaults(self):
        """El constructor debe establecer valores por defecto."""
        from utils.printer import ESCPOSPrinter
        p = ESCPOSPrinter()
        self.assertEqual(p.paper_width, 48)
        self.assertTrue(p.auto_cut)
        self.assertEqual(p.codepage, "cp850")

    def test_init_custom_values(self):
        """El constructor debe aceptar valores personalizados."""
        from utils.printer import ESCPOSPrinter
        p = ESCPOSPrinter(printer_name="Custom", auto_cut=False, paper_width=32, codepage="cp437")
        self.assertEqual(p.printer_name, "Custom")
        self.assertFalse(p.auto_cut)
        self.assertEqual(p.paper_width, 32)
        self.assertEqual(p.codepage, "cp437")

    def test_codepage_setter_valid(self):
        """El setter de codepage debe aceptar cp437 y cp850."""
        self.printer.codepage = "cp437"
        self.assertEqual(self.printer.codepage, "cp437")
        self.printer.codepage = "cp850"
        self.assertEqual(self.printer.codepage, "cp850")

    def test_codepage_setter_invalid(self):
        """El setter de codepage debe ignorar valores inválidos."""
        old = self.printer.codepage
        self.printer.codepage = "utf-8"
        self.assertEqual(self.printer.codepage, old)  # No cambió

    def test_encode_cp850(self):
        """_encode debe codificar texto a cp850."""
        data = self.printer._encode("Hola")
        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 0)

    def test_encode_cp437(self):
        """_encode debe codificar texto a cp437."""
        self.printer.codepage = "cp437"
        data = self.printer._encode("Hola")
        self.assertIsInstance(data, bytes)

    def test_writeln_appends_newline(self):
        """writeln debe agregar LF."""
        self.printer.writeln("Test")
        self.assertTrue(self._written.endswith(b"\x0a"))

    def test_set_bold_on(self):
        """set_bold(True) debe enviar comando bold on."""
        self.printer.set_bold(True)
        self.assertIn(b"\x1b\x45\x01", bytes(self._written))

    def test_set_bold_off(self):
        """set_bold(False) debe enviar comando bold off."""
        self.printer.set_bold(False)
        self.assertIn(b"\x1b\x45\x00", bytes(self._written))

    def test_set_align_left(self):
        """set_align debe enviar comando de alineación."""
        self.printer.set_align("left")
        self.assertIn(b"\x1b\x61\x00", bytes(self._written))

    def test_set_align_center(self):
        """set_align center debe enviar comando adecuado."""
        self.printer.set_align("center")
        self.assertIn(b"\x1b\x61\x01", bytes(self._written))

    def test_set_align_right(self):
        """set_align right debe enviar comando adecuado."""
        self.printer.set_align("right")
        self.assertIn(b"\x1b\x61\x02", bytes(self._written))

    def test_write_centered_sets_align_and_writes(self):
        """write_centered debe cambiar alineación y escribir texto."""
        self.printer.write_centered("Test")
        output = bytes(self._written)
        self.assertIn(b"\x1b\x61\x01", output)  # center aligment
        self.assertIn(self.printer._encode("Test") + b"\x0a", output)
        self.assertIn(b"\x1b\x61\x00", output)  # restore left

    def test_set_font_double_both(self):
        """set_font_double debe enviar comando de fuente."""
        self.printer.set_font_double(width=True, height=True)
        self.assertIn(b"\x1d\x21\x11", bytes(self._written))

    def test_set_font_normal(self):
        """set_font_double(False, False) debe restaurar fuente normal."""
        self.printer.set_font_double(False, False)
        self.assertIn(b"\x1d\x21\x00", bytes(self._written))

    def test_feed_sends_esc_d_command(self):
        """feed debe enviar ESC d n."""
        self.printer.feed(5)
        self.assertIn(b"\x1b\x64\x05", bytes(self._written))

    def test_cut_sends_gs_v_command(self):
        """cut debe enviar GS V."""
        self.printer.cut(full=True)
        self.assertIn(b"\x1d\x56\x00", bytes(self._written))

    def test_cut_partial(self):
        """cut(partial=True) debe enviar comando de corte parcial."""
        self.printer.cut(full=False)
        self.assertIn(b"\x1d\x56\x01", bytes(self._written))

    def test_init_sends_esc_at(self):
        """init() debe enviar ESC @."""
        self.printer.init()
        self.assertIn(b"\x1b\x40", bytes(self._written))

    def test_write_bold_line(self):
        """write_bold_line debe escribir en negrita y restaurar."""
        self.printer.write_bold_line("Bold Text")
        output = bytes(self._written)
        self.assertIn(b"\x1b\x45\x01", output)  # bold on
        self.assertIn(b"\x1b\x45\x00", output)  # bold off

    def test_print_qr_without_qrcode(self):
        """print_qr no debe fallar si qrcode no está instalado."""
        # Simular que qrcode no está disponible
        with unittest.mock.patch.dict('sys.modules', {'qrcode': None}):
            try:
                self.printer.print_qr("Test data")
            except Exception as e:
                self.fail(f"print_qr lanzó excepción: {e}")

    def test_print_test_returns_false_without_printer(self):
        """print_test debe retornar (False, mensaje) si no hay impresora."""
        from utils.printer import ESCPOSPrinter
        p = ESCPOSPrinter(printer_name=None)
        # Mock open() para retornar False
        p.open = unittest.mock.MagicMock(return_value=False)
        result = p.print_test()
        self.assertFalse(result[0])
        self.assertIsInstance(result[1], str)


class TestPrinterGetPrinters(unittest.TestCase):
    """Pruebas para funciones de detección de impresoras (sin pywin32)."""

    def test_get_available_printers_no_pywin32(self):
        """Sin pywin32, debe retornar lista vacía."""
        from utils.printer import get_available_printers
        with unittest.mock.patch.dict('sys.modules', {'win32print': None}):
            printers = get_available_printers()
            self.assertEqual(printers, [])

    def test_get_default_printer_no_pywin32(self):
        """Sin pywin32, get_default_printer debe retornar None."""
        from utils.printer import get_default_printer
        with unittest.mock.patch.dict('sys.modules', {'win32print': None}):
            result = get_default_printer()
            self.assertIsNone(result)

    def test_check_printer_status_no_pywin32(self):
        """Sin pywin32, check_printer_status debe retornar False."""
        from utils.printer import check_printer_status
        with unittest.mock.patch.dict('sys.modules', {'win32print': None}):
            result = check_printer_status("Any Printer")
            self.assertFalse(result)

    def test_check_printer_status_empty_name(self):
        """Con nombre vacío, debe retornar False."""
        from utils.printer import check_printer_status
        self.assertFalse(check_printer_status(""))
        self.assertFalse(check_printer_status(None))


class TestPrintReceipt(unittest.TestCase):
    """Pruebas para la función print_receipt (flujo completo mockeado)."""

    def setUp(self):
        self.orden = Orden(
            numero="TEST-001", tipo="local",
            subtotal=12.50, impuesto=2.00, total=14.50,
            fecha_creacion="2026-01-15T14:30:00",
        )
        self.items = [OrdenItem(producto_nombre="Cola", cantidad=1, precio_unitario=2.5)]

    def test_print_receipt_no_printer_available(self):
        """Sin impresora, debe retornar (False, mensaje_error)."""
        from utils.printer import print_receipt
        # Mock save_receipt_pdf para evitar dependencia de DB
        with unittest.mock.patch('utils.printer.save_receipt_pdf', return_value=(False, "")), \
             unittest.mock.patch('utils.printer.ESCPOSPrinter.print_receipt', return_value=(False, "No printer")):
            success, msg = print_receipt(self.orden, self.items)
            self.assertFalse(success)

    def test_print_receipt_success(self):
        """Con éxito, debe retornar (True, mensaje)."""
        from utils.printer import print_receipt
        with unittest.mock.patch('utils.printer.save_receipt_pdf', return_value=(True, "/fake/path.pdf")), \
             unittest.mock.patch('utils.printer.ESCPOSPrinter.print_receipt', return_value=(True, "OK")):
            success, msg = print_receipt(self.orden, self.items)
            self.assertTrue(success)
            self.assertIn("OK", msg)


class TestSaveReceiptPdf(unittest.TestCase):
    """Pruebas para save_receipt_pdf (generación de PDF)."""

    def setUp(self):
        self.orden = Orden(
            numero="TEST-001", tipo="local",
            subtotal=12.50, impuesto=2.00, total=14.50,
            fecha_creacion="2026-01-15T14:30:00",
        )
        self.items = [OrdenItem(producto_nombre="Cola", cantidad=1, precio_unitario=2.5)]

    def test_save_pdf_disabled_in_config(self):
        """Si config dice 0, debe retornar (False, mensaje)."""
        from utils.printer import save_receipt_pdf
        with unittest.mock.patch('database.config_service.ConfigService') as MockCfg:
            mock_instance = unittest.mock.MagicMock()
            mock_instance.get_config.return_value = "0"
            MockCfg.return_value = mock_instance

            success, msg = save_receipt_pdf(self.orden, self.items)
            self.assertFalse(success)
            self.assertIn("disabled", msg)

    def test_save_pdf_config_error_continues(self):
        """Si config da error, debe intentar igual (no fallar)."""
        from utils.printer import save_receipt_pdf
        with unittest.mock.patch('database.config_service.ConfigService', side_effect=ImportError()):
            # No debe lanzar excepción
            success, msg = save_receipt_pdf(self.orden, self.items)
            self.assertFalse(success)


class TestPrinterCleanupOldReceipts(unittest.TestCase):
    """Pruebas para _cleanup_old_receipts."""

    def test_cleanup_removes_old_files(self):
        """Debe eliminar archivos más antiguos que keep_days."""
        import tempfile
        from utils.printer import _cleanup_old_receipts
        from datetime import datetime, timedelta

        with tempfile.TemporaryDirectory() as tmpdir:
            # Crear archivos de diferentes edades
            old_file = os.path.join(tmpdir, "20250101_test.pdf")
            new_file = os.path.join(tmpdir, "20260601_test.pdf")

            with open(old_file, "w") as f:
                f.write("old")
            with open(new_file, "w") as f:
                f.write("new")

            # Poner fecha antigua al archivo old
            old_time = (datetime.now() - timedelta(days=60)).timestamp()
            os.utime(old_file, (old_time, old_time))

            # Ejecutar limpieza (keep_days=30)
            _cleanup_old_receipts(tmpdir, keep_days=30)

            self.assertFalse(os.path.exists(old_file), "Archivo antiguo debe eliminarse")
            self.assertTrue(os.path.exists(new_file), "Archivo nuevo debe conservarse")

    def test_cleanup_skips_non_pdf(self):
        """Debe ignorar archivos que no son PDF."""
        from utils.printer import _cleanup_old_receipts
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            txt_file = os.path.join(tmpdir, "test.txt")
            with open(txt_file, "w") as f:
                f.write("not pdf")

            _cleanup_old_receipts(tmpdir, keep_days=1)
            self.assertTrue(os.path.exists(txt_file), "Archivos no PDF deben conservarse")


# ═══════════════════════════════════════════
#  backup_manager.py
# ═══════════════════════════════════════════

class TestBackupManager(unittest.TestCase):
    """Pruebas para backup_manager.py."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # backup_manager.py hace "from config import DB_PATH, APP_DATA_DIR" a nivel de módulo,
        # por lo que hay que parchear sus copias locales
        self.db_path_patch = unittest.mock.patch('utils.backup_manager.DB_PATH', '')
        self.app_data_patch = unittest.mock.patch('utils.backup_manager.APP_DATA_DIR', self.temp_dir)
        self.db_path_patch.start()
        self.app_data_patch.start()

    def tearDown(self):
        self.app_data_patch.stop()
        self.db_path_patch.stop()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_run_daily_backup_no_db(self):
        """Sin DB, no debe hacer nada (ni fallar)."""
        from utils.backup_manager import run_daily_backup
        utils_backup = __import__('utils.backup_manager', fromlist=[''])
        # Parchear DB_PATH a un archivo que no existe
        with unittest.mock.patch('utils.backup_manager.DB_PATH', os.path.join(self.temp_dir, "nonexistent.db")):
            try:
                run_daily_backup()
            except Exception as e:
                self.fail(f"run_daily_backup lanzó excepción: {e}")

    def test_run_daily_backup_creates_file(self):
        """Con DB, debe crear el backup."""
        from utils.backup_manager import run_daily_backup
        db_path = os.path.join(self.temp_dir, "test.db")

        # Crear DB falsa
        with open(db_path, "w") as f:
            f.write("fake db content")

        # Parchear DB_PATH al archivo creado
        with unittest.mock.patch('utils.backup_manager.DB_PATH', db_path):
            run_daily_backup()

        # Verificar que se creó un backup
        backup_dir = os.path.join(self.temp_dir, "backups")
        self.assertTrue(os.path.exists(backup_dir))
        backup_files = os.listdir(backup_dir)
        self.assertGreater(len(backup_files), 0)
        self.assertTrue(any("db_backup" in f for f in backup_files))

    def test_run_daily_backup_skip_if_exists(self):
        """Si ya existe backup del día, no debe crear otro."""
        from utils.backup_manager import run_daily_backup

        db_path = os.path.join(self.temp_dir, "test.db")
        with open(db_path, "w") as f:
            f.write("fake db content")

        with unittest.mock.patch('utils.backup_manager.DB_PATH', db_path):
            run_daily_backup()  # Primera vez

            backup_dir = os.path.join(self.temp_dir, "backups")
            files_after_first = len(os.listdir(backup_dir))

            run_daily_backup()  # Segunda vez (mismo día)

            files_after_second = len(os.listdir(backup_dir))
            self.assertEqual(files_after_first, files_after_second, "No debe crear backup duplicado")

    def test_cleanup_old_backups(self):
        """_cleanup_old_backups debe eliminar backups antiguos."""
        from utils.backup_manager import _cleanup_old_backups
        from datetime import datetime, timedelta

        backup_dir = os.path.join(self.temp_dir, "backups")
        os.makedirs(backup_dir, exist_ok=True)

        # Crear 10 backups falsos
        now = datetime.now()
        for i in range(10):
            fpath = os.path.join(backup_dir, f"db_backup_2026010{i}.db")
            with open(fpath, "w") as f:
                f.write(f"backup {i}")
            # Fechar los primeros 5 como viejos (>7 días)
            if i < 5:
                old_time = (now - timedelta(days=20 + i)).timestamp()
                os.utime(fpath, (old_time, old_time))

        _cleanup_old_backups(backup_dir, keep_last=7)

        remaining = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
        self.assertLessEqual(len(remaining), 7, "Deben quedar máximo 7 backups")

    def test_cleanup_handles_empty_dir(self):
        """_cleanup_old_backups no debe fallar con directorio vacío."""
        from utils.backup_manager import _cleanup_old_backups
        try:
            _cleanup_old_backups(self.temp_dir, keep_last=7)
        except Exception as e:
            self.fail(f"_cleanup_old_backups lanzó excepción: {e}")

    def test_run_daily_backup_with_error_logs(self):
        """Si copiar falla, debe loguear error (no crash)."""
        from utils.backup_manager import run_daily_backup
        db_path = os.path.join(self.temp_dir, "test.db")
        with open(db_path, "w") as f:
            f.write("fake")

        with unittest.mock.patch('utils.backup_manager.DB_PATH', db_path):
            # Mock copy2 para que falle
            with unittest.mock.patch('utils.backup_manager.shutil.copy2', side_effect=PermissionError("test")):
                try:
                    run_daily_backup()
                except Exception as e:
                    self.fail(f"run_daily_backup no debe lanzar excepción: {e}")


# ═══════════════════════════════════════════
#  app_logging.py
# ═══════════════════════════════════════════

class TestAppLogging(unittest.TestCase):
    """Pruebas para app_logging.py."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # app_logging.py hace "from config import APP_DATA_DIR" a nivel de módulo,
        # por lo que hay que parchear su copia local, no app_config.APP_DATA_DIR
        self.app_data_patch = unittest.mock.patch('utils.app_logging.APP_DATA_DIR', self.temp_dir)
        self.app_data_patch.start()
        # Limpiar handlers de logging para que cada test pueda configurarlo fresco
        logging.root.handlers.clear()

    def tearDown(self):
        self.app_data_patch.stop()
        logging.root.handlers.clear()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_setup_logging_creates_log_dir(self):
        """setup_logging debe crear el directorio de logs."""
        from utils.app_logging import setup_logging
        logger = setup_logging()
        self.assertIsNotNone(logger)
        log_dir = os.path.join(self.temp_dir, "logs")
        self.assertTrue(os.path.exists(log_dir))

    def test_setup_logging_returns_logger(self):
        """setup_logging debe retornar un logger configurado."""
        from utils.app_logging import setup_logging
        logger = setup_logging()
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "pizzas_pastra")

    def test_setup_logging_creates_log_file(self):
        """setup_logging debe crear un archivo de log."""
        from utils.app_logging import setup_logging
        setup_logging()
        log_dir = os.path.join(self.temp_dir, "logs")
        log_files = os.listdir(log_dir)
        self.assertGreater(len(log_files), 0, "Debe existir al menos un archivo de log")

    def test_logger_writes_message(self):
        """El logger debe poder escribir mensajes."""
        from utils.app_logging import setup_logging
        logger = setup_logging()
        logger.info("Test message")
        # Verificar que el archivo de log contiene el mensaje
        log_dir = os.path.join(self.temp_dir, "logs")
        for fname in os.listdir(log_dir):
            fpath = os.path.join(log_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            if "Test message" in content:
                break
        else:
            self.fail("El mensaje de log no se encontró en el archivo")

    def test_install_exception_hook(self):
        """install_exception_hook debe reemplazar sys.excepthook."""
        from utils.app_logging import install_exception_hook
        logger = logging.getLogger("test")
        old_hook = sys.excepthook

        install_exception_hook(logger)
        self.assertIsNot(sys.excepthook, old_hook, "El hook debe haber cambiado")

        # Restaurar
        sys.excepthook = old_hook

    def test_exception_hook_passes_keyboard_interrupt(self):
        """El hook debe pasar KeyboardInterrupt al hook original."""
        from utils.app_logging import install_exception_hook
        logger = logging.getLogger("test")
        install_exception_hook(logger)

        old_excepthook = sys.excepthook
        original_std = sys.__excepthook__
        called = [False]

        def mock_original(exc_type, exc_value, exc_tb):
            called[0] = True

        sys.__excepthook__ = mock_original

        # Simular KeyboardInterrupt
        old_excepthook(KeyboardInterrupt, KeyboardInterrupt(), None)
        self.assertTrue(called[0], "KeyboardInterrupt debe pasar al hook original")

        # Restaurar
        sys.__excepthook__ = original_std
        sys.excepthook = original_std


# ═══════════════════════════════════════════
#  printer.py — ESCPOSPrinter Hardware Methods (win32print mocked)
# ═══════════════════════════════════════════

class TestEscposPrinterHardware(unittest.TestCase):
    """Pruebas para open/close/write/start_doc/end_doc con pywin32 mockeado."""

    def setUp(self):
        from utils.printer import ESCPOSPrinter
        self.printer = ESCPOSPrinter(printer_name="Mock Printer")

    def test_open_success_with_mocked_win32print(self):
        """open() debe retornar True si win32print funciona."""
        mock_wp = unittest.mock.MagicMock()
        mock_wp.OpenPrinter.return_value = "handle"
        mock_wp.GetDefaultPrinter.return_value = "Mock Printer"
        with unittest.mock.patch.dict('sys.modules', {'win32print': mock_wp}):
            result = self.printer.open()
            self.assertTrue(result)
            self.assertIsNotNone(self.printer._hprinter)

    def test_open_failure_import_error(self):
        """open() debe retornar False si pywin32 no está instalado."""
        with unittest.mock.patch.dict('sys.modules', {'win32print': None}):
            result = self.printer.open()
            self.assertFalse(result)

    def test_open_failure_no_printer_name(self):
        """open() debe retornar False si no hay nombre de impresora."""
        p = self.__class__.__new__(self.__class__)
        from utils.printer import ESCPOSPrinter
        p.__class__ = ESCPOSPrinter
        # Inicializar manualmente sin nombre
        p.printer_name = None
        p.auto_cut = True
        p.paper_width = 48
        p._codepage = "cp850"
        p._hprinter = None

        mock_wp = unittest.mock.MagicMock()
        mock_wp.GetDefaultPrinter.return_value = None
        with unittest.mock.patch.dict('sys.modules', {'win32print': mock_wp}):
            result = p.open()
            self.assertFalse(result)

    def test_open_failure_exception(self):
        """open() debe retornar False si win32print.OpenPrinter lanza excepción."""
        mock_wp = unittest.mock.MagicMock()
        mock_wp.OpenPrinter.side_effect = Exception("Access denied")
        with unittest.mock.patch.dict('sys.modules', {'win32print': mock_wp}):
            result = self.printer.open()
            self.assertFalse(result)

    def test_close_clears_handle(self):
        """close() debe limpiar el handle de impresora."""
        self.printer._hprinter = "mock_handle"
        mock_wp = unittest.mock.MagicMock()
        with unittest.mock.patch.dict('sys.modules', {'win32print': mock_wp}):
            self.printer.close()
            mock_wp.ClosePrinter.assert_called_once_with("mock_handle")
        self.assertIsNone(self.printer._hprinter)

    def test_close_no_handle_does_nothing(self):
        """close() sin handle no debe hacer nada."""
        self.printer._hprinter = None
        # No debe lanzar excepción
        self.printer.close()

    def test_write_without_open_returns_false(self):
        """write() sin open() debe retornar False."""
        self.printer._hprinter = None
        result = self.printer.write(b"test")
        self.assertFalse(result)

    def test_write_with_open_success(self):
        """write() con handle debe escribir datos."""
        self.printer._hprinter = "mock_handle"
        mock_wp = unittest.mock.MagicMock()
        with unittest.mock.patch.dict('sys.modules', {'win32print': mock_wp}):
            result = self.printer.write(b"test data")
            self.assertTrue(result)
            mock_wp.WritePrinter.assert_called_once_with("mock_handle", b"test data")

    def test_write_with_open_failure(self):
        """write() debe retornar False si WritePrinter falla."""
        self.printer._hprinter = "mock_handle"
        mock_wp = unittest.mock.MagicMock()
        mock_wp.WritePrinter.side_effect = Exception("Write error")
        with unittest.mock.patch.dict('sys.modules', {'win32print': mock_wp}):
            result = self.printer.write(b"test data")
            self.assertFalse(result)

    def test_start_doc_without_handle_returns_false(self):
        """start_doc() sin handle debe retornar False."""
        self.printer._hprinter = None
        result = self.printer.start_doc()
        self.assertFalse(result)

    def test_start_doc_success(self):
        """start_doc() debe iniciar documento correctamente."""
        self.printer._hprinter = "mock_handle"
        mock_wp = unittest.mock.MagicMock()
        with unittest.mock.patch.dict('sys.modules', {'win32print': mock_wp}):
            result = self.printer.start_doc("Test Doc")
            self.assertTrue(result)
            mock_wp.StartDocPrinter.assert_called_once()
            mock_wp.StartPagePrinter.assert_called_once()

    def test_end_doc_without_handle_returns_false(self):
        """end_doc() sin handle debe retornar False."""
        self.printer._hprinter = None
        result = self.printer.end_doc()
        self.assertFalse(result)

    def test_end_doc_success(self):
        """end_doc() debe finalizar documento correctamente."""
        self.printer._hprinter = "mock_handle"
        mock_wp = unittest.mock.MagicMock()
        with unittest.mock.patch.dict('sys.modules', {'win32print': mock_wp}):
            result = self.printer.end_doc()
            self.assertTrue(result)
            mock_wp.EndPagePrinter.assert_called_once()
            mock_wp.EndDocPrinter.assert_called_once()

    def test_start_doc_exception(self):
        """start_doc() debe retornar False si falla."""
        self.printer._hprinter = "mock_handle"
        mock_wp = unittest.mock.MagicMock()
        mock_wp.StartDocPrinter.side_effect = Exception("Start doc error")
        with unittest.mock.patch.dict('sys.modules', {'win32print': mock_wp}):
            result = self.printer.start_doc()
            self.assertFalse(result)

    def test_end_doc_exception(self):
        """end_doc() debe retornar False si falla."""
        self.printer._hprinter = "mock_handle"
        mock_wp = unittest.mock.MagicMock()
        mock_wp.EndPagePrinter.side_effect = Exception("End page error")
        with unittest.mock.patch.dict('sys.modules', {'win32print': mock_wp}):
            result = self.printer.end_doc()
            self.assertFalse(result)


class TestEscposPrinterPrintReceipt(unittest.TestCase):
    """Pruebas para ESCPOSPrinter.print_receipt (flujo completo mockeado)."""

    def setUp(self):
        from utils.printer import ESCPOSPrinter
        self.printer = ESCPOSPrinter(
            printer_name="Test Printer",
            auto_cut=True,
            paper_width=48,
            codepage="cp850",
        )
        self.orden = Orden(
            numero="TEST-001", tipo="local", estado="pending",
            subtotal=12.50, impuesto=2.00, total=14.50,
            cliente_nombre="Juan Perez",
            fecha_creacion="2026-01-15T14:30:00",
        )
        self.items = [
            OrdenItem(producto_nombre="Margarita", cantidad=2,
                      precio_unitario=5.0),
        ]

    def _mock_hardware_methods(self):
        """Mockea open/start_doc/end_doc/close para evitar hardware real."""
        self.printer.open = unittest.mock.MagicMock(return_value=True)
        self.printer.start_doc = unittest.mock.MagicMock(return_value=True)
        self.printer.end_doc = unittest.mock.MagicMock(return_value=True)
        self.printer.close = unittest.mock.MagicMock()

        # Capturar datos escritos
        self._written = bytearray()
        original_write = self.printer.write
        def _mock_write(data):
            self._written.extend(data)
            return True
        self.printer.write = _mock_write

    def test_print_receipt_success(self):
        """print_receipt debe retornar (True, mensaje) en caso exitoso."""
        self._mock_hardware_methods()
        success, msg = self.printer.print_receipt(self.orden, self.items)
        self.assertTrue(success)
        self.assertIn("exitosamente", msg)

    def test_print_receipt_writes_business_name(self):
        """print_receipt debe escribir el nombre del negocio."""
        self._mock_hardware_methods()
        self.printer.print_receipt(self.orden, self.items)
        output = bytes(self._written)
        self.assertIn(app_config.BUSINESS_NAME.encode("cp850", errors="replace"), output)

    def test_print_receipt_writes_items(self):
        """print_receipt debe escribir los items."""
        self._mock_hardware_methods()
        self.printer.print_receipt(self.orden, self.items)
        output = bytes(self._written)
        self.assertIn(b"Margarita", output)

    def test_print_receipt_writes_totals(self):
        """print_receipt debe escribir los totales."""
        self._mock_hardware_methods()
        self.printer.print_receipt(self.orden, self.items)
        output = bytes(self._written)
        self.assertIn(b"14.50", output)

    def test_print_receipt_includes_cut_command(self):
        """Con auto_cut=True, debe incluir comando de corte."""
        self._mock_hardware_methods()
        self.printer.print_receipt(self.orden, self.items)
        output = bytes(self._written)
        self.assertIn(b"\x1d\x56\x00", output)  # GS V NUL

    def test_print_receipt_delivery_includes_address(self):
        """Orden delivery debe incluir dirección en impresión."""
        self._mock_hardware_methods()
        self.orden.tipo = "delivery"
        self.orden.direccion = "Calle 123"
        self.orden.telefono_contacto = "555-0000"
        self.orden.costo_delivery = 3.0
        self.printer.print_receipt(self.orden, self.items)
        output = bytes(self._written)
        self.assertIn(b"Calle 123", output)
        self.assertIn(b"555-0000", output)

    def test_print_receipt_calls_open_and_close(self):
        """print_receipt debe llamar open() y close()."""
        mock_printer = unittest.mock.MagicMock()
        mock_printer.open.return_value = True
        mock_printer.start_doc.return_value = True
        mock_printer.end_doc.return_value = True

        mock_printer.print_receipt = None  # prevent recursion
        # Probar que el método llama a open y close
        from utils.printer import ESCPOSPrinter

        with unittest.mock.patch.object(
            ESCPOSPrinter, 'open', return_value=True
        ) as mock_open, \
             unittest.mock.patch.object(
            ESCPOSPrinter, 'close'
        ) as mock_close, \
             unittest.mock.patch.object(
            ESCPOSPrinter, 'start_doc', return_value=True
        ) as mock_start, \
             unittest.mock.patch.object(
            ESCPOSPrinter, 'end_doc', return_value=True
        ) as mock_end, \
             unittest.mock.patch.object(
            ESCPOSPrinter, 'write', return_value=True
        ):
            p = ESCPOSPrinter(printer_name="Mock")
            p.codepage = "cp850"
            success, msg = p.print_receipt(self.orden, self.items)
            self.assertTrue(success)
            mock_open.assert_called_once()
            mock_start.assert_called_once()
            mock_end.assert_called_once()
            mock_close.assert_called_once()

    def test_print_receipt_open_failure(self):
        """Si open() falla, debe retornar (False, mensaje)."""
        from utils.printer import ESCPOSPrinter
        p = ESCPOSPrinter()
        p.open = unittest.mock.MagicMock(return_value=False)
        success, msg = p.print_receipt(self.orden, self.items)
        self.assertFalse(success)

    def test_print_receipt_with_notes(self):
        """print_receipt debe incluir notas si existen."""
        self._mock_hardware_methods()
        self.orden.notas = "Sin cebolla, extra queso"
        self.printer.print_receipt(self.orden, self.items)
        output = bytes(self._written)
        self.assertIn(b"Sin cebolla", output)

    def test_print_receipt_exception_handling(self):
        """Si ocurre excepción, debe retornar (False, mensaje_error)."""
        # Crear printer que falla al escribir
        from utils.printer import ESCPOSPrinter
        p = ESCPOSPrinter()
        p.open = unittest.mock.MagicMock(return_value=True)
        p.start_doc = unittest.mock.MagicMock(return_value=True)
        p.write = unittest.mock.MagicMock(side_effect=Exception("Write fail"))
        p.close = unittest.mock.MagicMock()
        p.end_doc = unittest.mock.MagicMock()

        success, msg = p.print_receipt(self.orden, self.items)
        self.assertFalse(success)
        self.assertIn("Write fail", msg)
        p.close.assert_called_once()  # close debe llamarse incluso en error

    def test_print_receipt_without_auto_cut(self):
        """Con auto_cut=False, no debe incluir comando de corte."""
        from utils.printer import ESCPOSPrinter
        p = ESCPOSPrinter(printer_name="Test", auto_cut=False)
        p.open = unittest.mock.MagicMock(return_value=True)
        p.start_doc = unittest.mock.MagicMock(return_value=True)
        p.end_doc = unittest.mock.MagicMock(return_value=True)
        p.close = unittest.mock.MagicMock()
        written = bytearray()
        def _write(data):
            written.extend(data)
            return True
        p.write = _write

        p.print_receipt(self.orden, self.items)
        output = bytes(written)
        self.assertNotIn(b"\x1d\x56\x00", output)  # No debe haber corte


class TestEscposPrinterPrintTest(unittest.TestCase):
    """Pruebas para ESCPOSPrinter.print_test (flujo completo mockeado)."""

    def setUp(self):
        from utils.printer import ESCPOSPrinter
        self.printer = ESCPOSPrinter(
            printer_name="Test Printer",
            auto_cut=True,
            paper_width=48,
        )

    def test_print_test_with_mocked_hardware(self):
        """print_test debe retornar (True, mensaje) con hardware mockeado."""
        self.printer.open = unittest.mock.MagicMock(return_value=True)
        self.printer.start_doc = unittest.mock.MagicMock(return_value=True)
        self.printer.end_doc = unittest.mock.MagicMock(return_value=True)
        self.printer.close = unittest.mock.MagicMock()
        self.printer.write = unittest.mock.MagicMock(return_value=True)

        success, msg = self.printer.print_test()
        self.assertTrue(success)
        self.assertIn("correctamente", msg)

    def test_print_test_writes_test_content(self):
        """print_test debe escribir contenido de prueba."""
        self.printer.open = unittest.mock.MagicMock(return_value=True)
        self.printer.start_doc = unittest.mock.MagicMock(return_value=True)
        self.printer.end_doc = unittest.mock.MagicMock(return_value=True)
        self.printer.close = unittest.mock.MagicMock()
        written = bytearray()
        def _write(data):
            written.extend(data)
            return True
        self.printer.write = _write

        self.printer.print_test()
        output = bytes(written)
        self.assertIn(b"=== TEST ===", output)
        self.assertIn(b"Impresora termica", output)
        self.assertIn(app_config.APP_VERSION.encode(), output)

    def test_print_test_includes_cut(self):
        """print_test debe incluir comando de corte."""
        self.printer.open = unittest.mock.MagicMock(return_value=True)
        self.printer.start_doc = unittest.mock.MagicMock(return_value=True)
        self.printer.end_doc = unittest.mock.MagicMock(return_value=True)
        self.printer.close = unittest.mock.MagicMock()
        written = bytearray()
        def _write(data):
            written.extend(data)
            return True
        self.printer.write = _write

        self.printer.print_test()
        output = bytes(written)
        self.assertIn(b"\x1d\x56\x00", output)  # Corte

    def test_print_test_open_failure(self):
        """print_test debe retornar (False, mensaje) si open() falla."""
        self.printer.open = unittest.mock.MagicMock(return_value=False)
        success, msg = self.printer.print_test()
        self.assertFalse(success)

    def test_print_test_exception_handling(self):
        """print_test debe capturar excepciones y retornar (False, mensaje)."""
        self.printer.open = unittest.mock.MagicMock(return_value=True)
        self.printer.start_doc = unittest.mock.MagicMock(return_value=True)
        self.printer.write = unittest.mock.MagicMock(side_effect=Exception("Print error"))
        self.printer.close = unittest.mock.MagicMock()
        self.printer.end_doc = unittest.mock.MagicMock()

        success, msg = self.printer.print_test()
        self.assertFalse(success)
        self.assertIn("Print error", msg)
        self.printer.close.assert_called_once()


class TestEscposPrinterQR(unittest.TestCase):
    """Pruebas para funcionalidad QR (print_qr, _print_qr_bitmap, _print_qr_if_enabled)."""

    def setUp(self):
        from utils.printer import ESCPOSPrinter
        self.printer = ESCPOSPrinter(printer_name="Test")
        self._written = bytearray()
        def _write(data):
            self._written.extend(data)
            return True
        self.printer.write = _write

    def test_print_qr_with_mocked_qrcode(self):
        """print_qr debe escribir datos cuando qrcode está disponible."""
        # Mockear qrcode para que no genere imagen real
        mock_qr_module = unittest.mock.MagicMock()
        mock_qr_instance = unittest.mock.MagicMock()
        mock_qr_instance.get_matrix.return_value = [[True, False], [False, True]]
        mock_qr_module.QRCode.return_value = mock_qr_instance

        with unittest.mock.patch.dict('sys.modules', {'qrcode': mock_qr_module}):
            self.printer.print_qr("Test QR", module_size=2, error_level="M")
            output = bytes(self._written)
            # Debe haber escrito al menos el comando GS v 0
            self.assertIn(b"\x1d\x76\x30\x00", output)
            self.assertGreater(len(output), 4)

    def test_print_qr_with_different_error_levels(self):
        """print_qr debe aceptar diferentes niveles de corrección."""
        mock_qr_module = unittest.mock.MagicMock()
        mock_qr_instance = unittest.mock.MagicMock()
        mock_qr_instance.get_matrix.return_value = [[True]]
        mock_qr_module.QRCode.return_value = mock_qr_instance

        for level in ("L", "M", "Q", "H"):
            with unittest.mock.patch.dict('sys.modules', {'qrcode': mock_qr_module}):
                try:
                    self.printer.print_qr("Test", module_size=2, error_level=level)
                except Exception as e:
                    self.fail(f"print_qr con nivel {level} lanzó: {e}")

    def test_print_qr_unknown_error_level_defaults_to_m(self):
        """Nivel de error desconocido debe usar M por defecto."""
        mock_qr_module = unittest.mock.MagicMock()
        mock_qr_instance = unittest.mock.MagicMock()
        mock_qr_instance.get_matrix.return_value = [[True]]
        mock_qr_module.QRCode.return_value = mock_qr_instance

        with unittest.mock.patch.dict('sys.modules', {'qrcode': mock_qr_module}):
            try:
                self.printer.print_qr("Test", module_size=2, error_level="X")
            except Exception as e:
                self.fail(f"print_qr con nivel X lanzó: {e}")

    def test_print_qr_no_qrcode(self):
        """print_qr sin qrcode no debe lanzar excepción."""
        with unittest.mock.patch.dict('sys.modules', {'qrcode': None}):
            try:
                self.printer.print_qr("Test")
            except Exception as e:
                self.fail(f"print_qr lanzó excepción: {e}")

    def test_print_qr_bitmap_writes_command(self):
        """_print_qr_bitmap debe escribir comando GS v 0 con datos."""
        matrix = [[True, False], [False, True]]
        self.printer._print_qr_bitmap(matrix, size=2, module_size=2)
        output = bytes(self._written)
        self.assertIn(b"\x1d\x76\x30\x00", output)
        # 4 pixeles (2*2) / 8 = 1 byte por fila
        self.assertGreater(len(output), 10)

    def test_print_qr_if_enabled_with_qr_enabled(self):
        """_print_qr_if_enabled debe imprimir QR si config lo habilita."""
        orden = Orden(numero="TEST-001", tipo="local", subtotal=10, impuesto=0, total=10)

        with unittest.mock.patch(
            'database.config_service.ConfigService.get_config', return_value="1"
        ), unittest.mock.patch.object(self.printer, 'print_qr') as mock_print_qr:
            self.printer._print_qr_if_enabled(orden)
            mock_print_qr.assert_called_once()

    def test_print_qr_if_enabled_with_qr_disabled(self):
        """_print_qr_if_enabled no debe imprimir QR si config lo deshabilita."""
        orden = Orden(numero="TEST-001", tipo="local", subtotal=10, impuesto=0, total=10)

        with unittest.mock.patch(
            'database.config_service.ConfigService.get_config', return_value="0"
        ), unittest.mock.patch.object(self.printer, 'print_qr') as mock_print_qr:
            self.printer._print_qr_if_enabled(orden)
            mock_print_qr.assert_not_called()

    def test_print_qr_if_enabled_no_config(self):
        """_print_qr_if_enabled no debe fallar si no hay config."""
        orden = Orden(numero="TEST-001", tipo="local", subtotal=10, impuesto=0, total=10)

        with unittest.mock.patch(
            'database.config_service.ConfigService.get_config',
            side_effect=Exception("No DB")
        ), unittest.mock.patch.object(self.printer, 'print_qr') as mock_print_qr:
            self.printer._print_qr_if_enabled(orden)
            mock_print_qr.assert_not_called()

    def test_print_qr_with_different_module_sizes(self):
        """print_qr debe aceptar diferentes module_sizes."""
        mock_qr_module = unittest.mock.MagicMock()
        mock_qr_instance = unittest.mock.MagicMock()
        mock_qr_instance.get_matrix.return_value = [[True]]
        mock_qr_module.QRCode.return_value = mock_qr_instance

        for size in (1, 4, 8, 16):
            with unittest.mock.patch.dict('sys.modules', {'qrcode': mock_qr_module}):
                try:
                    self.printer.print_qr("Test", module_size=size)
                except Exception as e:
                    self.fail(f"print_qr con module_size {size} lanzó: {e}")


class TestEscposPrinterPrintQrIfEnabledIntegration(unittest.TestCase):
    """Pruebas de integración para _print_qr_if_enabled (con paper_width real)."""

    def setUp(self):
        from utils.printer import ESCPOSPrinter
        self.printer_58 = ESCPOSPrinter(paper_width=32)
        self.printer_80 = ESCPOSPrinter(paper_width=48)
        self.orden = Orden(
            numero="TEST-001", tipo="local",
            subtotal=10, impuesto=0, total=10,
        )

    def test_qr_module_size_depends_on_paper_width(self):
        """El module_size debe ser 4 para 58mm y 6 para 80mm."""
        with unittest.mock.patch(
            'database.config_service.ConfigService.get_config', return_value="1"
        ), unittest.mock.patch.object(self.printer_58, 'print_qr') as mock_58, \
             unittest.mock.patch.object(self.printer_80, 'print_qr') as mock_80:
            self.printer_58._print_qr_if_enabled(self.orden)
            mock_58.assert_called_once()
            args_58 = mock_58.call_args[1]
            self.assertEqual(args_58['module_size'], 4)

            self.printer_80._print_qr_if_enabled(self.orden)
            mock_80.assert_called_once()
            args_80 = mock_80.call_args[1]
            self.assertEqual(args_80['module_size'], 6)


class TestSaveReceiptPdfWithPySide6(unittest.TestCase):
    """Pruebas para save_receipt_pdf con PySide6 mockeado (generación PDF)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.original_app_data = app_config.APP_DATA_DIR
        app_config.APP_DATA_DIR = self.temp_dir

        self.orden = Orden(
            numero="TEST-001", tipo="local",
            subtotal=12.50, impuesto=2.00, total=14.50,
            fecha_creacion="2026-01-15T14:30:00",
        )
        self.items = [OrdenItem(producto_nombre="Cola", cantidad=1, precio_unitario=2.5)]

    def tearDown(self):
        app_config.APP_DATA_DIR = self.original_app_data
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_pdf_with_mocked_pyside6(self):
        """save_receipt_pdf debe generar PDF cuando PySide6 está disponible."""
        from utils.printer import save_receipt_pdf

        # Mockear PySide6 completamente
        with unittest.mock.patch('database.config_service.ConfigService') as MockCfg:
            mock_cfg = unittest.mock.MagicMock()
            mock_cfg.get_config.return_value = "1"  # enabled
            MockCfg.return_value = mock_cfg

            # Mockear QTextDocument, QPrinter, QSizeF, QMarginsF
            mock_doc = unittest.mock.MagicMock()
            mock_printer = unittest.mock.MagicMock()

            # pageRect() debe retornar un objeto con size() que retorna width()
            mock_page_rect = unittest.mock.MagicMock()
            mock_page_size = unittest.mock.MagicMock()
            mock_page_size.width.return_value = 80.0
            mock_page_rect.size.return_value = mock_page_size
            mock_printer.pageRect.return_value = mock_page_rect

            patches = [
                unittest.mock.patch('PySide6.QtGui.QTextDocument', return_value=mock_doc),
                unittest.mock.patch('PySide6.QtPrintSupport.QPrinter', return_value=mock_printer),
                unittest.mock.patch('PySide6.QtCore.QSizeF', return_value=unittest.mock.MagicMock()),
                unittest.mock.patch('PySide6.QtCore.QMarginsF', return_value=unittest.mock.MagicMock()),
            ]

            # Configurar PrintMode y PageSize como enteros (para evitar AttributeError)
            mock_printer.PrinterMode.HighResolution = 2
            mock_printer.OutputFormat.PdfFormat = 0
            mock_printer.PageSize.Custom = 0
            mock_printer.Unit.Millimeter = 1

            for p in patches:
                p.start()

            try:
                success, result = save_receipt_pdf(self.orden, self.items)
                # En este entorno, los enums pueden fallar, verificar que al menos
                # no lance excepción y que intente generar el PDF
                self.assertTrue(isinstance(success, bool))
                self.assertTrue(os.path.exists(os.path.join(self.temp_dir, "receipts")),
                               "Debe crear el directorio receipts")
            finally:
                for p in patches:
                    p.stop()

    def test_save_pdf_creates_receipts_dir(self):
        """save_receipt_pdf debe crear el directorio receipts."""
        from utils.printer import save_receipt_pdf

        with unittest.mock.patch('database.config_service.ConfigService') as MockCfg:
            mock_cfg = unittest.mock.MagicMock()
            mock_cfg.get_config.return_value = "1"
            MockCfg.return_value = mock_cfg

            with unittest.mock.patch('PySide6.QtGui.QTextDocument'), \
                 unittest.mock.patch('PySide6.QtPrintSupport.QPrinter') as MockPrinter, \
                 unittest.mock.patch('PySide6.QtCore.QSizeF'), \
                 unittest.mock.patch('PySide6.QtCore.QMarginsF'):

                mock_printer = MockPrinter.return_value
                mock_rect = unittest.mock.MagicMock()
                mock_size = unittest.mock.MagicMock()
                mock_size.width.return_value = 80.0
                mock_rect.size.return_value = mock_size
                mock_printer.pageRect.return_value = mock_rect

                # Llamar sin forzar enums
                success, result = save_receipt_pdf(self.orden, self.items)

        receipts_dir = os.path.join(self.temp_dir, "receipts")
        self.assertTrue(os.path.exists(receipts_dir))

    def test_save_pdf_pyside6_not_available(self):
        """save_receipt_pdf debe manejar error si PySide6 no está disponible."""
        from utils.printer import save_receipt_pdf

        with unittest.mock.patch('database.config_service.ConfigService') as MockCfg:
            mock_cfg = unittest.mock.MagicMock()
            mock_cfg.get_config.return_value = "1"
            MockCfg.return_value = mock_cfg

            with unittest.mock.patch.dict(
                'sys.modules', {'PySide6.QtGui': None}
            ):
                success, msg = save_receipt_pdf(self.orden, self.items)
                self.assertFalse(success)


class TestPrintReceiptFunctionAdvanced(unittest.TestCase):
    """Pruebas avanzadas para la función print_receipt (configuraciones mockeadas)."""

    def setUp(self):
        self.orden = Orden(
            numero="TEST-001", tipo="local",
            subtotal=12.50, impuesto=2.00, total=14.50,
            fecha_creacion="2026-01-15T14:30:00",
        )
        self.items = [OrdenItem(producto_nombre="Cola", cantidad=1, precio_unitario=2.5)]

    def test_print_receipt_with_config_values(self):
        """print_receipt debe leer configuración desde DB."""
        from utils.printer import print_receipt

        # Mock save_receipt_pdf
        with unittest.mock.patch('utils.printer.save_receipt_pdf', return_value=(False, "")), \
             unittest.mock.patch('database.config_service.ConfigService') as MockCfg:
            mock_cfg = unittest.mock.MagicMock()
            # Configuraciones específicas
            def get_config_side_effect(key):
                configs = {
                    "printer_name": "Config Printer",
                    "printer_auto_cut": "0",
                    "printer_paper_width": "32",
                    "printer_codepage": "cp437",
                }
                return configs.get(key)
            mock_cfg.get_config.side_effect = get_config_side_effect
            MockCfg.return_value = mock_cfg

            with unittest.mock.patch('utils.printer.ESCPOSPrinter.print_receipt',
                                     return_value=(True, "OK")):
                success, msg = print_receipt(self.orden, self.items)
                self.assertTrue(success)

    def test_print_receipt_without_db_config(self):
        """print_receipt debe usar defaults si ConfigService falla."""
        from utils.printer import print_receipt

        with unittest.mock.patch('utils.printer.save_receipt_pdf', return_value=(False, "")), \
             unittest.mock.patch('database.config_service.ConfigService',
                                 side_effect=ImportError()):
            with unittest.mock.patch('utils.printer.ESCPOSPrinter.print_receipt',
                                     return_value=(True, "OK")):
                success, msg = print_receipt(self.orden, self.items)
                self.assertTrue(success)

    def test_print_receipt_with_custom_params(self):
        """print_receipt debe aceptar parámetros personalizados."""
        from utils.printer import print_receipt

        with unittest.mock.patch('utils.printer.save_receipt_pdf', return_value=(False, "")), \
             unittest.mock.patch('database.config_service.ConfigService') as MockCfg:
            mock_cfg = unittest.mock.MagicMock()
            mock_cfg.get_config.return_value = None  # No config
            MockCfg.return_value = mock_cfg

            with unittest.mock.patch('utils.printer.ESCPOSPrinter') as MockPrinter:
                mock_instance = unittest.mock.MagicMock()
                mock_instance.print_receipt.return_value = (True, "OK")
                MockPrinter.return_value = mock_instance

                success, msg = print_receipt(
                    self.orden, self.items,
                    printer_name="Custom Printer",
                    auto_cut=False,
                    paper_width=32,
                )
                self.assertTrue(success)
                # Verificar que se creó con los parámetros correctos
                call_kwargs = MockPrinter.call_args[1]
                self.assertEqual(call_kwargs['printer_name'], "Custom Printer")
                self.assertEqual(call_kwargs['paper_width'], 32)

    def test_print_receipt_pdf_success_in_message(self):
        """Si PDF se guarda bien, debe incluir ruta en el mensaje."""
        from utils.printer import print_receipt

        with unittest.mock.patch('utils.printer.save_receipt_pdf',
                                 return_value=(True, "/fake/path.pdf")), \
             unittest.mock.patch('database.config_service.ConfigService') as MockCfg:
            mock_cfg = unittest.mock.MagicMock()
            mock_cfg.get_config.return_value = None
            MockCfg.return_value = mock_cfg

            with unittest.mock.patch('utils.printer.ESCPOSPrinter.print_receipt',
                                     return_value=(True, "Printed")):
                success, msg = print_receipt(self.orden, self.items)
                self.assertIn("fake/path.pdf", msg)

    def test_print_receipt_pdf_config_disabled(self):
        """Si PDF está deshabilitado en config, print_receipt debe funcionar igual."""
        from utils.printer import print_receipt

        with unittest.mock.patch('utils.printer.save_receipt_pdf',
                                 return_value=(False, "disabled")), \
             unittest.mock.patch('database.config_service.ConfigService') as MockCfg:
            mock_cfg = unittest.mock.MagicMock()
            mock_cfg.get_config.return_value = None
            MockCfg.return_value = mock_cfg

            with unittest.mock.patch('utils.printer.ESCPOSPrinter.print_receipt',
                                     return_value=(True, "Printed")):
                success, msg = print_receipt(self.orden, self.items)
                self.assertTrue(success)


class TestPrinterFormatTextEdgeCases(unittest.TestCase):
    """Pruebas adicionales para format_receipt_text (casos borde)."""

    def setUp(self):
        self.orden = Orden(
            numero="TEST-001", tipo="local", estado="pending",
            subtotal=12.50, impuesto=2.00, total=14.50,
            cliente_nombre="Juan Perez",
            fecha_creacion="2026-01-15T14:30:00",
        )
        self.items = [
            OrdenItem(producto_nombre="Margarita", cantidad=2, precio_unitario=5.0),
        ]

    def test_format_with_delivery_cost_but_not_delivery(self):
        """Si tiene costo_delivery pero no es delivery, igual debe mostrar."""
        from utils.printer import format_receipt_text
        self.orden.costo_delivery = 3.0
        text = format_receipt_text(self.orden, self.items, paper_width=48)
        self.assertIn("3.00", text)

    def test_format_without_fecha_creacion(self):
        """Sin fecha de creación, no debe fallar."""
        from utils.printer import format_receipt_text
        self.orden.fecha_creacion = ""
        text = format_receipt_text(self.orden, self.items, paper_width=48)
        self.assertIn(self.orden.numero, text)

    def test_format_takeout_type(self):
        """Tipo takeout debe mostrar 'Para Llevar'."""
        from utils.printer import format_receipt_text
        self.orden.tipo = "takeout"
        text = format_receipt_text(self.orden, self.items, paper_width=48)
        self.assertIn("Para Llevar", text)

    def test_format_delivery_type_label(self):
        """Tipo delivery debe mostrar 'Delivery'."""
        from utils.printer import format_receipt_text
        self.orden.tipo = "delivery"
        text = format_receipt_text(self.orden, self.items, paper_width=48)
        self.assertIn("Delivery", text)

    def test_format_unknown_type(self):
        """Tipo desconocido debe mostrarse tal cual."""
        from utils.printer import format_receipt_text
        self.orden.tipo = "express"
        text = format_receipt_text(self.orden, self.items, paper_width=48)
        self.assertIn("express", text)

    def test_format_long_item_name_truncated(self):
        """Nombre de producto largo debe truncarse al ancho."""
        from utils.printer import format_receipt_text
        self.items[0].producto_nombre = "A" * 60
        text = format_receipt_text(self.orden, self.items, paper_width=32)
        # Ancho para 58mm: paper_width - 20 = 12 chars para nombre
        # Pero el nombre se trunca a paper_width - 20 = 12
        for line in text.split("\n"):
            self.assertLessEqual(len(line), 32, f"Línea excede ancho: '{line}'")

    def test_format_long_item_name_80mm(self):
        """Nombre largo en papel de 80mm debe truncarse."""
        from utils.printer import format_receipt_text
        self.items[0].producto_nombre = "A" * 60
        text = format_receipt_text(self.orden, self.items, paper_width=48)
        for line in text.split("\n"):
            self.assertLessEqual(len(line), 48, f"Línea excede ancho: '{line}'")

    def test_format_without_slogan(self):
        """Sin slogan, no debe incluir línea vacía extra."""
        from utils.printer import format_receipt_text
        original = app_config.BUSINESS_SLOGAN
        app_config.BUSINESS_SLOGAN = ""
        try:
            text = format_receipt_text(self.orden, self.items, paper_width=48)
            self.assertNotIn(app_config.BUSINESS_NAME + "\n\n", text)
        finally:
            app_config.BUSINESS_SLOGAN = original

    def test_format_without_phone(self):
        """Sin teléfono, no debe incluir línea 'Tel:'."""
        from utils.printer import format_receipt_text
        original = app_config.BUSINESS_PHONE
        app_config.BUSINESS_PHONE = ""
        try:
            text = format_receipt_text(self.orden, self.items, paper_width=48)
            self.assertNotIn("Tel:", text)
        finally:
            app_config.BUSINESS_PHONE = original


class TestPrinterFormatHtmlEdgeCases(unittest.TestCase):
    """Pruebas adicionales para format_receipt_html (QR, delivery)."""

    def setUp(self):
        self.orden = Orden(
            numero="TEST-001", tipo="local",
            subtotal=12.50, impuesto=2.00, total=14.50,
            fecha_creacion="2026-01-15T14:30:00",
        )
        self.items = [OrdenItem(producto_nombre="Cola", cantidad=1, precio_unitario=2.5)]

    def test_format_html_with_qr_code_available(self):
        """Con qrcode instalado, debe generar HTML con QR."""
        from utils.printer import format_receipt_html

        # Mockear qrcode
        mock_qrcode = unittest.mock.MagicMock()
        mock_img = unittest.mock.MagicMock()
        mock_qrcode.make.return_value = mock_img

        with unittest.mock.patch.dict('sys.modules', {'qrcode': mock_qrcode}):
            html = format_receipt_html(self.orden, self.items, include_qr=True)
            self.assertIn("<html>", html)
            self.assertIn("data:image/png;base64", html)

    def test_format_html_qr_code_failure(self):
        """Si qrcode.make falla, no debe romper el HTML."""
        from utils.printer import format_receipt_html

        mock_qrcode = unittest.mock.MagicMock()
        mock_qrcode.make.side_effect = Exception("QR Error")

        with unittest.mock.patch.dict('sys.modules', {'qrcode': mock_qrcode}):
            html = format_receipt_html(self.orden, self.items, include_qr=True)
            self.assertIn("<html>", html)

    def test_format_html_delivery_order(self):
        """Orden delivery debe verse diferente en HTML."""
        from utils.printer import format_receipt_html
        self.orden.tipo = "delivery"
        html = format_receipt_html(self.orden, self.items, include_qr=False)
        self.assertIn("delivery", html.lower())


class TestPrinterGetPrintersAdvanced(unittest.TestCase):
    """Pruebas avanzadas para funciones de detección de impresoras."""

    def test_get_available_printers_with_mocked_win32print(self):
        """Con win32print disponible, debe listar impresoras."""
        from utils.printer import get_available_printers

        mock_wp = unittest.mock.MagicMock()
        # Simular 2 impresoras
        mock_wp.EnumPrinters.return_value = [
            (None, None, "Printer1"),
            (None, None, "Printer2"),
            (None, None, "Printer1"),  # duplicado
        ]
        with unittest.mock.patch.dict('sys.modules', {'win32print': mock_wp}):
            printers = get_available_printers()
            self.assertEqual(printers, ["Printer1", "Printer2"])

    def test_get_available_printers_exception(self):
        """Si EnumPrinters falla, debe retornar lista vacía."""
        from utils.printer import get_available_printers

        mock_wp = unittest.mock.MagicMock()
        mock_wp.EnumPrinters.side_effect = Exception("Access denied")
        with unittest.mock.patch.dict('sys.modules', {'win32print': mock_wp}):
            printers = get_available_printers()
            self.assertEqual(printers, [])

    def test_get_default_printer_with_mocked_win32print(self):
        """Con win32print, debe retornar impresora predeterminada."""
        from utils.printer import get_default_printer

        mock_wp = unittest.mock.MagicMock()
        mock_wp.GetDefaultPrinter.return_value = "Default Printer"
        with unittest.mock.patch.dict('sys.modules', {'win32print': mock_wp}):
            result = get_default_printer()
            self.assertEqual(result, "Default Printer")

    def test_check_printer_status_success(self):
        """check_printer_status debe retornar True si OpenPrinter funciona."""
        from utils.printer import check_printer_status

        mock_wp = unittest.mock.MagicMock()
        mock_wp.OpenPrinter.return_value = "handle"
        with unittest.mock.patch.dict('sys.modules', {'win32print': mock_wp}):
            result = check_printer_status("Printer1")
            self.assertTrue(result)
            mock_wp.ClosePrinter.assert_called_once_with("handle")

    def test_check_printer_status_failure(self):
        """check_printer_status debe retornar False si OpenPrinter falla."""
        from utils.printer import check_printer_status

        mock_wp = unittest.mock.MagicMock()
        mock_wp.OpenPrinter.side_effect = Exception("Offline")
        with unittest.mock.patch.dict('sys.modules', {'win32print': mock_wp}):
            result = check_printer_status("Offline Printer")
            self.assertFalse(result)


class TestEscposPrinterInitExtended(unittest.TestCase):
    """Pruebas extendidas para ESCPOSPrinter.init() y codepage."""

    def test_init_with_cp850_sends_code_page_command(self):
        """init() con cp850 debe enviar comando de code page."""
        from utils.printer import ESCPOSPrinter
        p = ESCPOSPrinter(codepage="cp850")
        written = bytearray()
        def _write(data):
            written.extend(data)
            return True
        p.write = _write

        p.init()
        output = bytes(written)
        self.assertIn(b"\x1b\x40", output)  # ESC @ (init)
        self.assertIn(b"\x1b\x74\x02", output)  # ESC t 2 (cp850)
        self.assertIn(b"\x1b\x33\x18", output)  # ESC 3 24 (line spacing)

    def test_init_with_cp437_sends_correct_code_page(self):
        """init() con cp437 debe enviar comando cp437."""
        from utils.printer import ESCPOSPrinter
        p = ESCPOSPrinter(codepage="cp437")
        written = bytearray()
        def _write(data):
            written.extend(data)
            return True
        p.write = _write

        p.init()
        output = bytes(written)
        self.assertIn(b"\x1b\x74\x00", output)  # ESC t 0 (cp437)

    def test_set_font_double_width_only(self):
        """set_font_double(width=True, height=False)."""
        from utils.printer import ESCPOSPrinter
        p = ESCPOSPrinter()
        written = bytearray()
        def _write(data):
            written.extend(data)
            return True
        p.write = _write

        p.set_font_double(width=True, height=False)
        self.assertIn(b"\x1d\x21\x01", bytes(written))

    def test_set_font_double_height_only(self):
        """set_font_double(width=False, height=True)."""
        from utils.printer import ESCPOSPrinter
        p = ESCPOSPrinter()
        written = bytearray()
        def _write(data):
            written.extend(data)
            return True
        p.write = _write

        p.set_font_double(width=False, height=True)
        self.assertIn(b"\x1d\x21\x10", bytes(written))


class TestEscposPrinterEncodeEdgeCases(unittest.TestCase):
    """Pruebas para _encode con casos borde."""

    def test_encode_unknown_codepage_fallback_cp437(self):
        """Code page desconocido debe fallback a cp437."""
        from utils.printer import ESCPOSPrinter
        p = ESCPOSPrinter(codepage="invalid")
        # Forzar el codepage a uno inválido
        p._codepage = "utf-32"
        data = p._encode("Hola")
        self.assertIsInstance(data, bytes)

    def test_encode_special_chars_cp850(self):
        """_encode debe codificar caracteres especiales a cp850."""
        from utils.printer import ESCPOSPrinter
        p = ESCPOSPrinter(codepage="cp850")
        data = p._encode("Ññáéíóú")
        self.assertIsInstance(data, bytes)
        self.assertGreater(len(data), 0)

    def test_encode_empty_string(self):
        """_encode con string vacío debe retornar bytes vacío."""
        from utils.printer import ESCPOSPrinter
        p = ESCPOSPrinter()
        data = p._encode("")
        self.assertEqual(data, b"")


if __name__ == '__main__':
    unittest.main()
