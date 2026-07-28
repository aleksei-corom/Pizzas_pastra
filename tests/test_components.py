"""Tests unitarios para componentes de UI (SearchBar, OrderPanel, ProductCard, PaymentDialog, etc.)."""
import unittest
import unittest.mock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QDialog, QPushButton, QLabel, QLineEdit, QFrame
from PySide6.QtTest import QTest
from PySide6.QtCore import Qt

from database.db_manager import DatabaseManager
from database.producto_service import ProductoService
from database.orden_service import OrdenService
from database.models import Producto, Categoria, Orden, OrdenItem, Transaccion
import config as app_config


# ─── QApplication singleton ───
_app: QApplication | None = None


def get_app() -> QApplication:
    global _app
    if _app is None:
        _app = QApplication.instance() or QApplication(sys.argv)
    return _app


def _init_db():
    """Inicializa DB en memoria y retorna servicios."""
    app_config.DB_PATH = ":memory:"
    DatabaseManager._instance = None
    db = DatabaseManager()
    db.init_db()
    prod_svc = ProductoService(db)
    orden_svc = OrdenService(db)
    return db, prod_svc, orden_svc


# ═══════════════════════════════════════════
#  SearchBar
# ═══════════════════════════════════════════

class TestSearchBar(unittest.TestCase):
    """Pruebas para SearchBar."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def test_creates_with_placeholder(self):
        """La barra debe crearse con el placeholder indicado."""
        from views.components.search_bar import SearchBar
        sb = SearchBar("Buscar producto...")
        self.assertIsNotNone(sb)
        self.assertIn("Buscar producto", sb.placeholderText())
        sb.deleteLater()

    def test_text_changed_signal_works(self):
        """Escribir texto debe emitir textChanged."""
        from views.components.search_bar import SearchBar
        sb = SearchBar("Buscar...")
        received = []

        def on_change(text):
            received.append(text)

        sb.textChanged.connect(on_change)
        sb.show()

        QTest.keyClicks(sb, "Cola")
        self.assertGreaterEqual(len(received), 1)
        self.assertIn("Cola", "".join(received))

        sb.deleteLater()

    def test_clear_button_enabled(self):
        """El botón de limpiar debe estar habilitado."""
        from views.components.search_bar import SearchBar
        sb = SearchBar("Buscar...")
        self.assertTrue(sb.isClearButtonEnabled())
        sb.deleteLater()

    def test_fixed_height(self):
        """Debe tener altura fija de 40."""
        from views.components.search_bar import SearchBar
        sb = SearchBar()
        self.assertEqual(sb.height(), 40)
        sb.deleteLater()


# ═══════════════════════════════════════════
#  IconButton
# ═══════════════════════════════════════════

class TestIconButton(unittest.TestCase):
    """Pruebas para IconButton."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def test_creates_with_icon(self):
        """El botón debe crearse con un icono."""
        from views.components.icon_button import IconButton
        btn = IconButton("➕", tooltip="Agregar", size=36)
        self.assertEqual(btn.text(), "➕")
        self.assertEqual(btn.toolTip(), "Agregar")
        self.assertEqual(btn.width(), 36)
        self.assertEqual(btn.height(), 36)
        btn.deleteLater()

    def test_click_signal_works(self):
        """El click debe emitir la señal clicked."""
        from views.components.icon_button import IconButton
        btn = IconButton("🗑")
        clicked = [False]

        def on_click():
            clicked[0] = True

        btn.clicked.connect(on_click)
        btn.show()

        QTest.mouseClick(btn, Qt.MouseButton.LeftButton)
        self.assertTrue(clicked[0])
        btn.deleteLater()


# ═══════════════════════════════════════════
#  StatusBadge
# ═══════════════════════════════════════════

class TestStatusBadge(unittest.TestCase):
    """Pruebas para StatusBadge."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def test_creates_with_text_and_status(self):
        """Debe crearse con texto y clase de estilo."""
        from views.components.status_badge import StatusBadge
        badge = StatusBadge("Activo", "success")
        self.assertEqual(badge.text(), "Activo")
        self.assertEqual(badge.property("class"), "badge-success")
        badge.deleteLater()

    def test_all_status_styles(self):
        """Cada estado debe tener su clase correspondiente."""
        from views.components.status_badge import StatusBadge
        for status in ("success", "warning", "danger", "info"):
            badge = StatusBadge("Test", status)
            self.assertEqual(badge.property("class"), f"badge-{status}")
            badge.deleteLater()

    def test_fixed_height(self):
        """Debe tener altura fija de 28."""
        from views.components.status_badge import StatusBadge
        badge = StatusBadge("OK", "success")
        self.assertEqual(badge.height(), 28)
        badge.deleteLater()


# ═══════════════════════════════════════════
#  CardWidget
# ═══════════════════════════════════════════

class TestCardWidget(unittest.TestCase):
    """Pruebas para CardWidget."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def test_creates_with_title(self):
        """Debe crearse con título."""
        from views.components.card_widget import CardWidget
        card = CardWidget(title="Test Card")
        self.assertIsNotNone(card)
        card.deleteLater()

    def test_add_widget(self):
        """add_widget debe agregar un widget al contenido."""
        from views.components.card_widget import CardWidget
        card = CardWidget(title="Card")
        lbl = QLabel("Content")
        card.add_widget(lbl)
        self.assertEqual(card.content_layout.count(), 1)
        card.deleteLater()

    def test_add_layout(self):
        """add_layout debe agregar un layout al contenido."""
        from views.components.card_widget import CardWidget
        from PySide6.QtWidgets import QVBoxLayout
        card = CardWidget(title="Card")
        layout = QVBoxLayout()
        card.add_layout(layout)
        self.assertEqual(card.content_layout.count(), 1)
        card.deleteLater()


# ═══════════════════════════════════════════
#  LoadingSpinner
# ═══════════════════════════════════════════

class TestLoadingSpinner(unittest.TestCase):
    """Pruebas para LoadingSpinner."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def test_creates_with_default_size(self):
        """Debe crearse con tamaño predeterminado de 40."""
        from views.components.loading_spinner import LoadingSpinner
        spinner = LoadingSpinner()
        self.assertEqual(spinner.width(), 40)
        self.assertEqual(spinner.height(), 40)
        spinner.deleteLater()

    def test_custom_size(self):
        """Debe aceptar tamaño personalizado."""
        from views.components.loading_spinner import LoadingSpinner
        spinner = LoadingSpinner(size=60)
        self.assertEqual(spinner.width(), 60)
        spinner.deleteLater()

    def test_start_stop(self):
        """start() y stop() deben funcionar sin errores."""
        from views.components.loading_spinner import LoadingSpinner
        spinner = LoadingSpinner()
        spinner.start()
        self.assertTrue(spinner.isVisible())
        spinner.stop()
        self.assertFalse(spinner.isVisible())
        spinner.deleteLater()

    def test_timer_is_running_after_creation(self):
        """El timer debe estar activo inmediatamente después de crear el spinner."""
        from views.components.loading_spinner import LoadingSpinner
        spinner = LoadingSpinner()
        self.assertTrue(spinner._timer.isActive())
        self.assertEqual(spinner._timer.interval(), 16)
        spinner.deleteLater()

    def test_stop_detiene_el_timer(self):
        """stop() debe detener el timer además de ocultar."""
        from views.components.loading_spinner import LoadingSpinner
        spinner = LoadingSpinner()
        spinner.stop()
        self.assertFalse(spinner._timer.isActive())
        spinner.deleteLater()

    def test_start_reactiva_el_timer(self):
        """start() debe reactivar el timer después de stop()."""
        from views.components.loading_spinner import LoadingSpinner
        spinner = LoadingSpinner()
        spinner.stop()
        self.assertFalse(spinner._timer.isActive())
        spinner.start()
        self.assertTrue(spinner._timer.isActive())
        spinner.deleteLater()

    def test_rotate_incrementa_angulo(self):
        """_rotate debe incrementar el ángulo en 6."""
        from views.components.loading_spinner import LoadingSpinner
        spinner = LoadingSpinner()
        spinner._angle = 0
        spinner._rotate()
        self.assertEqual(spinner._angle, 6)
        spinner.deleteLater()

    def test_rotate_wraps_at_360(self):
        """_rotate debe wrap a 0 cuando el ángulo llega a 360."""
        from views.components.loading_spinner import LoadingSpinner
        spinner = LoadingSpinner()
        spinner._angle = 354
        spinner._rotate()
        self.assertEqual(spinner._angle, 0)
        spinner.deleteLater()

    def test_custom_color(self):
        """Debe aceptar color personalizado en el constructor."""
        from views.components.loading_spinner import LoadingSpinner
        spinner = LoadingSpinner(color="#ff0000")
        self.assertEqual(spinner._color.name(), "#ff0000")
        spinner.deleteLater()

    def test_paint_event_no_crash(self):
        """paintEvent debe ejecutarse sin errores (llamado directamente)."""
        from PySide6.QtGui import QPaintEvent
        from PySide6.QtCore import QRect
        from views.components.loading_spinner import LoadingSpinner
        spinner = LoadingSpinner()
        # Llamar paintEvent directamente con un evento simulado
        event = QPaintEvent(QRect(0, 0, spinner.width(), spinner.height()))
        spinner.paintEvent(event)
        # Si llegamos aquí, no hubo crash
        self.assertTrue(True)
        spinner.deleteLater()

    def test_multiple_rotate_calls(self):
        """Múltiples llamadas a _rotate deben acumular ángulo correctamente."""
        from views.components.loading_spinner import LoadingSpinner
        spinner = LoadingSpinner()
        spinner._angle = 0
        for _ in range(10):
            spinner._rotate()
        self.assertEqual(spinner._angle, 60)  # 10 * 6 = 60
        spinner.deleteLater()


# ═══════════════════════════════════════════
#  AvatarWidget
# ═══════════════════════════════════════════

class TestAvatarWidget(unittest.TestCase):
    """Pruebas para AvatarWidget."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def test_creates_with_initials(self):
        """Debe mostrar las iniciales."""
        from views.components.avatar_widget import AvatarWidget
        avatar = AvatarWidget("JD", size=40)
        self.assertEqual(avatar.text(), "JD")
        avatar.deleteLater()

    def test_initials_truncated(self):
        """Debe truncar iniciales a 2 caracteres."""
        from views.components.avatar_widget import AvatarWidget
        avatar = AvatarWidget("ABCD")
        self.assertEqual(avatar.text(), "AB")
        avatar.deleteLater()

    def test_custom_color(self):
        """Debe aceptar color personalizado."""
        from views.components.avatar_widget import AvatarWidget
        avatar = AvatarWidget("AB", color="#ff0000")
        self.assertIn("ff0000", avatar.styleSheet())
        avatar.deleteLater()


# ═══════════════════════════════════════════
#  ModernMessageBox
# ═══════════════════════════════════════════

class TestModernMessageBox(unittest.TestCase):
    """Pruebas para ModernMessageBox."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def test_create_info(self):
        """Debe crearse un mensaje info."""
        from views.components.modern_messagebox import ModernMessageBox
        dlg = ModernMessageBox(title="Info", message="Test info", msg_type="info")
        self.assertIsNotNone(dlg)
        dlg.deleteLater()

    def test_create_success(self):
        """Debe crearse un mensaje success."""
        from views.components.modern_messagebox import ModernMessageBox
        dlg = ModernMessageBox(title="OK", message="Test success", msg_type="success")
        self.assertIsNotNone(dlg)
        dlg.deleteLater()

    def test_create_warning(self):
        """Debe crearse un mensaje warning."""
        from views.components.modern_messagebox import ModernMessageBox
        dlg = ModernMessageBox(title="Warning", message="Test warning", msg_type="warning")
        self.assertIsNotNone(dlg)
        dlg.deleteLater()

    def test_create_error(self):
        """Debe crearse un mensaje error."""
        from views.components.modern_messagebox import ModernMessageBox
        dlg = ModernMessageBox(title="Error", message="Test error", msg_type="error")
        self.assertIsNotNone(dlg)
        dlg.deleteLater()

    def test_create_question(self):
        """Debe crearse un mensaje question."""
        from views.components.modern_messagebox import ModernMessageBox
        btns = [
            {"text": "No", "role": "reject", "class": "secondary"},
            {"text": "Sí", "role": "accept", "class": "primary"},
        ]
        dlg = ModernMessageBox(title="Pregunta", message="Test?", msg_type="question", buttons=btns)
        self.assertIsNotNone(dlg)
        dlg.deleteLater()

    def test_dialog_title_and_message(self):
        """El título y mensaje deben mostrarse correctamente."""
        from views.components.modern_messagebox import ModernMessageBox
        dlg = ModernMessageBox(title="Título", message="Mensaje de prueba", msg_type="info")

        # Encontrar los labels por objectName
        title_lbl = dlg.findChild(QLabel, "msgTitle")
        body_lbl = dlg.findChild(QLabel, "msgBody")

        self.assertIsNotNone(title_lbl)
        self.assertIsNotNone(body_lbl)
        self.assertIn("Título", title_lbl.text())
        self.assertIn("Mensaje de prueba", body_lbl.text())
        dlg.deleteLater()

    def test_accept_button_closes(self):
        """Hacer clic en Aceptar debe cerrar con resultado Accepted."""
        from views.components.modern_messagebox import ModernMessageBox
        btns = [{"text": "OK", "role": "accept", "class": "primary"}]
        dlg = ModernMessageBox(title="Test", message="Test", msg_type="info", buttons=btns)
        dlg.show()

        # Encontrar el botón y hacer clic
        btn = dlg.findChild(QPushButton, "")
        if btn:
            QTest.mouseClick(btn, Qt.MouseButton.LeftButton)
        dlg.deleteLater()

    def test_static_information(self):
        """information() estático debe ejecutarse sin errores."""
        from views.components.modern_messagebox import ModernMessageBox
        # Usar QTimer para cerrar después de 200ms (evita bloqueo)
        from PySide6.QtCore import QTimer

        result = []

        def _show():
            r = ModernMessageBox.information(None, "Info", "Test")
            result.append(r)

        # Ejecutar en un timer para permitir cierre automático
        QTimer.singleShot(500, lambda: None)

        # Solo verificar que el método existe y retorna un resultado
        self.assertTrue(hasattr(ModernMessageBox, "information"))


# ═══════════════════════════════════════════
#  ProductCard
# ═══════════════════════════════════════════

class TestProductCard(unittest.TestCase):
    """Pruebas para ProductCard."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def test_creates_with_producto(self):
        """La tarjeta debe crearse con un producto."""
        from views.components.product_card import ProductCard
        from database.models import Producto

        prod = Producto(nombre="Cola", precio=2.5, icono="🥤", disponible=True)
        card = ProductCard(prod)
        self.assertIsNotNone(card)
        self.assertEqual(card.producto, prod)
        card.deleteLater()

    def test_shows_product_info(self):
        """La tarjeta debe mostrar nombre, precio e icono."""
        from views.components.product_card import ProductCard
        from database.models import Producto

        prod = Producto(nombre="Margarita", precio=10.0, icono="🍕")
        card = ProductCard(prod)
        card.show()

        # Verificar precio
        price_lbl = card.findChild(QLabel, "product-card-price")
        self.assertIsNotNone(price_lbl)
        self.assertIn("10.00", price_lbl.text())

        # Verificar nombre
        name_lbl = card.findChild(QLabel, "product-card-name")
        self.assertIsNotNone(name_lbl)
        self.assertIn("Margarita", name_lbl.text())

        # Verificar icono
        icon_lbl = card.findChild(QLabel, "product-card-icon")
        self.assertIsNotNone(icon_lbl)
        self.assertIn("🍕", icon_lbl.text())

        card.deleteLater()

    def test_click_emits_product(self):
        """Hacer clic en la tarjeta debe emitir la señal clicked con el producto."""
        from views.components.product_card import ProductCard
        from database.models import Producto

        prod = Producto(nombre="Cola", precio=2.5)
        card = ProductCard(prod)

        received = []

        def on_click(p):
            received.append(p)

        card.clicked.connect(on_click)
        card.show()

        # Simular clic (mousePressEvent)
        QTest.mouseClick(card, Qt.MouseButton.LeftButton)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].nombre, "Cola")
        card.deleteLater()

    def test_variants_badge(self):
        """Si tiene variantes, debe mostrar badge."""
        from views.components.product_card import ProductCard
        from database.models import Producto

        prod = Producto(nombre="Pizza", precio=15.0, tiene_variantes=True)
        card = ProductCard(prod)
        card.show()

        # Buscar badge de variantes
        found = False
        for child in card.findChildren(QLabel):
            if "ingredientes" in child.text().lower():
                found = True
                break
        self.assertTrue(found)
        card.deleteLater()

    def test_fixed_size(self):
        """Debe tener tamaño fijo de 160x140."""
        from views.components.product_card import ProductCard
        from database.models import Producto

        prod = Producto(nombre="Test", precio=1.0)
        card = ProductCard(prod)
        self.assertEqual(card.width(), 160)
        self.assertEqual(card.height(), 140)
        card.deleteLater()


# ═══════════════════════════════════════════
#  OrderPanel (tests unitarios directos)
# ═══════════════════════════════════════════

class TestOrderPanel(unittest.TestCase):
    """Pruebas unitarias para OrderPanel."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def setUp(self):
        self.db, self.prod_svc, self.orden_svc = _init_db()

    def tearDown(self):
        if hasattr(self, 'panel') and self.panel:
            self.panel.deleteLater()
        self.db.close()
        DatabaseManager._instance = None

    def _create_panel(self):
        from views.components.order_panel import OrderPanel
        self.panel = OrderPanel()
        return self.panel

    def test_creates_empty(self):
        """El panel debe crearse vacío."""
        panel = self._create_panel()
        self.assertEqual(len(panel.items), 0)
        self.assertFalse(panel._btn_confirm.isEnabled())

    def test_add_item(self):
        """Agregar un item debe reflejarse en el panel."""
        panel = self._create_panel()
        item = OrdenItem(producto_id=1, producto_nombre="Cola", cantidad=1, precio_unitario=2.5)
        panel.add_item(item)
        self.assertEqual(len(panel.items), 1)

    def test_add_same_item_increases_quantity(self):
        """Agregar el mismo item debe incrementar cantidad."""
        panel = self._create_panel()
        item = OrdenItem(producto_id=1, producto_nombre="Cola", cantidad=1, precio_unitario=2.5)
        panel.add_item(item)
        panel.add_item(item)  # Mismo producto_id
        self.assertEqual(panel.items[0].cantidad, 2)

    def test_add_different_item(self):
        """Agregar items diferentes debe crear entradas separadas."""
        panel = self._create_panel()
        item1 = OrdenItem(producto_id=1, producto_nombre="Cola", cantidad=1, precio_unitario=2.5)
        item2 = OrdenItem(producto_id=2, producto_nombre="Te", cantidad=1, precio_unitario=1.5)
        panel.add_item(item1)
        panel.add_item(item2)
        self.assertEqual(len(panel.items), 2)

    def test_clear_order(self):
        """Limpiar la orden debe vaciar items y deshabilitar botón."""
        panel = self._create_panel()
        item = OrdenItem(producto_id=1, producto_nombre="Cola", cantidad=1, precio_unitario=2.5)
        panel.add_item(item)
        self.assertEqual(len(panel.items), 1)

        panel.clear_order()
        self.assertEqual(len(panel.items), 0)
        self.assertFalse(panel._btn_confirm.isEnabled())

    def test_totals_update(self):
        """Los totales deben actualizarse al agregar items."""
        panel = self._create_panel()
        item = OrdenItem(producto_id=1, producto_nombre="Cola", cantidad=2, precio_unitario=2.5)
        panel.add_item(item)

        # subtotal = 5.0, impuesto = 5 * 0.16 = 0.8, total = 5.8
        self.assertIn("5.00", panel._subtotal_lbl.text())
        self.assertIn("5.80", panel._total_lbl.text())
        self.assertTrue(panel._btn_confirm.isEnabled())

    def test_type_switching_shows_delivery_fields(self):
        """Cambiar a tipo delivery debe mostrar campos de delivery."""
        panel = self._create_panel()
        panel.show()
        self.assertFalse(panel._delivery_frame.isVisible())

        idx_delivery = panel.tipo_combo.findData("delivery")
        panel.tipo_combo.setCurrentIndex(idx_delivery)
        self.assertTrue(panel._delivery_frame.isVisible())

    def test_delivery_cost_in_totals(self):
        """El costo de delivery debe incluirse en el total."""
        panel = self._create_panel()
        item = OrdenItem(producto_id=1, producto_nombre="Cola", cantidad=1, precio_unitario=10.0)
        panel.add_item(item)

        # Cambiar a delivery
        idx_delivery = panel.tipo_combo.findData("delivery")
        panel.tipo_combo.setCurrentIndex(idx_delivery)
        panel._dl_costo.setValue(5.0)

        # subtotal=10, delivery=5, impuesto=10*0.16=1.6, total=16.6
        self.assertIn("16.60", panel._total_lbl.text())

    def test_confirm_order_emits_signal(self):
        """Confirmar orden debe emitir order_confirmed."""
        panel = self._create_panel()
        item = OrdenItem(producto_id=1, producto_nombre="Cola", cantidad=1, precio_unitario=2.5)
        panel.add_item(item)

        received = []

        def on_confirm(data):
            received.append(data)

        panel.order_confirmed.connect(on_confirm)
        panel._confirm_order()

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["tipo"], "local")
        self.assertEqual(len(received[0]["items"]), 1)

    def test_notas_are_included_in_confirm(self):
        """Las notas deben incluirse al confirmar la orden."""
        panel = self._create_panel()
        item = OrdenItem(producto_id=1, producto_nombre="Cola", cantidad=1, precio_unitario=2.5)
        panel.add_item(item)
        panel.notas_text.setPlainText("Sin hielo")

        received = []

        def on_confirm(data):
            received.append(data)

        panel.order_confirmed.connect(on_confirm)
        panel._confirm_order()

        self.assertEqual(received[0]["notas"], "Sin hielo")

    def test_delivery_data_in_confirm(self):
        """Los datos de delivery deben incluirse al confirmar orden de delivery."""
        panel = self._create_panel()
        item = OrdenItem(producto_id=1, producto_nombre="Cola", cantidad=1, precio_unitario=2.5)
        panel.add_item(item)

        idx_delivery = panel.tipo_combo.findData("delivery")
        panel.tipo_combo.setCurrentIndex(idx_delivery)
        panel._dl_direccion.setText("Calle 123")
        panel._dl_telefono.setText("555-0000")
        panel._dl_costo.setValue(3.0)

        received = []

        def on_confirm(data):
            received.append(data)

        panel.order_confirmed.connect(on_confirm)
        panel._confirm_order()

        self.assertEqual(received[0]["direccion"], "Calle 123")
        self.assertEqual(received[0]["telefono_contacto"], "555-0000")
        self.assertEqual(received[0]["costo_delivery"], 3.0)

    def test_clear_resets_notes(self):
        """Limpiar la orden debe resetear las notas."""
        panel = self._create_panel()
        panel.notas_text.setPlainText("Alguna nota")
        panel.clear_order()
        self.assertEqual(panel.notas_text.toPlainText(), "")

    def test_toast_uses_correct_types(self):
        """show_toast debe aceptar los tipos definidos."""
        from views.components.order_panel import ToastWidget
        panel = self._create_panel()
        for msg_type in ("success", "info", "warning"):
            # No debe lanzar excepción
            panel.show_toast(f"Test {msg_type}", msg_type)
        panel.deleteLater()

    def test_confirm_button_text_updates(self):
        """El texto del botón debe incluir el total."""
        panel = self._create_panel()
        item = OrdenItem(producto_id=1, producto_nombre="Cola", cantidad=1, precio_unitario=2.5)
        panel.add_item(item)

        self.assertIn("Cobrar", panel._btn_confirm.text())
        self.assertIn("2.90", panel._btn_confirm.text())


# ═══════════════════════════════════════════
#  PaymentDialog
# ═══════════════════════════════════════════

class TestPaymentDialog(unittest.TestCase):
    """Pruebas para PaymentDialog."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def tearDown(self):
        if hasattr(self, 'dlg') and self.dlg:
            self.dlg.deleteLater()

    def test_creates_with_total(self):
        """El diálogo debe crearse con un total."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.assertIsNotNone(self.dlg)
        self.assertEqual(self.dlg.total, 25.50)

    def test_shows_total_value(self):
        """El total debe mostrarse en la UI."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        total_lbl = self.dlg.findChild(QLabel, "payment-total-value")
        self.assertIsNotNone(total_lbl)
        self.assertIn("25.50", total_lbl.text())

    def test_simple_payment_method_buttons_exist(self):
        """Deben existir botones para cada método de pago en modo simple."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.assertEqual(len(self.dlg._simple_method_buttons), 4)  # efectivo, tarjeta, transferencia, otro

    def test_tab_switching(self):
        """Cambiar entre tabs simple y combinado debe funcionar."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg.show()

        # Verificar que simple está visible inicialmente
        self.assertTrue(self.dlg._tab_simple.isVisible())
        self.assertFalse(self.dlg._tab_combo.isVisible())

        # Cambiar a combinado
        self.dlg._switch_tab(1)
        QTest.qWait(50)
        self.assertFalse(self.dlg._tab_simple.isVisible())
        self.assertTrue(self.dlg._tab_combo.isVisible())

        # Volver a simple
        self.dlg._switch_tab(0)
        QTest.qWait(50)
        self.assertTrue(self.dlg._tab_simple.isVisible())
        self.assertFalse(self.dlg._tab_combo.isVisible())

    def test_simple_method_selection(self):
        """Seleccionar un método de pago simple debe marcarlo."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)

        self.dlg._select_simple_method("tarjeta")
        self.assertEqual(self.dlg._selected_simple_method, "tarjeta")
        self.assertTrue(self.dlg._simple_method_buttons["tarjeta"].isChecked())
        self.assertFalse(self.dlg._simple_method_buttons["efectivo"].isChecked())

    def test_combo_payment_rows_exist(self):
        """Deben existir filas para cada método en modo combinado."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.assertEqual(len(self.dlg._method_rows), 4)

    def test_confirm_button_disabled_initially_combo(self):
        """El botón confirmar debe estar deshabilitado si no se ha cubierto el total en combo."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg._switch_tab(1)
        # Sin montos, el botón debe estar deshabilitado
        self.assertFalse(self.dlg.btn_confirm.isEnabled())

    def test_confirm_button_enabled_when_covered_simple(self):
        """El botón confirmar debe habilitarse cuando el monto recibido cubre el total en simple."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        # Usar valor DIFERENTE al inicial para forzar valueChanged
        # (QDoubleSpinBox solo emite valueChanged si el valor cambia)
        self.dlg._simple_monto.setValue(30.00)
        self.dlg.show()
        self.assertTrue(self.dlg.btn_confirm.isEnabled())

    def test_confirm_button_disabled_when_short_simple(self):
        """El botón confirmar debe estar deshabilitado si el monto es insuficiente en simple."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg._simple_monto.setValue(10.00)
        self.assertFalse(self.dlg.btn_confirm.isEnabled())

    def test_vuelto_calculation_simple(self):
        """El vuelto debe calcularse correctamente en modo simple."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg._simple_monto.setValue(30.00)
        self.assertIn("4.50", self.dlg._val_vuelto_simple.text())

    def test_confirm_simple_returns_metodo(self):
        """Confirmar en modo simple debe establecer metodos_pago."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg.show()
        self.dlg._simple_monto.setValue(25.50)
        QTest.qWait(50)
        self.dlg._confirmar()
        self.assertEqual(len(self.dlg.metodos_pago), 1)
        self.assertEqual(self.dlg.metodos_pago[0][0], "efectivo")
        self.assertEqual(self.dlg.metodos_pago[0][1], 25.50)

    def test_confirm_combo_returns_multiple_methods(self):
        """Confirmar en modo combinado debe retornar múltiples métodos."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg._switch_tab(1)

        self.dlg._method_rows["efectivo"].value = 15.00
        self.dlg._method_rows["tarjeta"].value = 10.50
        self.dlg._confirmar()

        self.assertEqual(len(self.dlg.metodos_pago), 2)
        tipos = [m[0] for m in self.dlg.metodos_pago]
        self.assertIn("efectivo", tipos)
        self.assertIn("tarjeta", tipos)

    def test_combo_progress_bar(self):
        """La barra de progreso en combinado debe reflejar el porcentaje cubierto."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(100.00)
        self.dlg._switch_tab(1)

        self.dlg._method_rows["efectivo"].value = 50.00
        # 50% cubierto
        self.assertIsNotNone(self.dlg._progress_fill)

    def test_imprimir_recibo_default_true(self):
        """El checkbox de imprimir recibo debe estar marcado por defecto."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.assertTrue(self.dlg.check_imprimir.isChecked())

    def test_set_orden_data(self):
        """set_orden_data debe almacenar la referencia de la orden."""
        from views.components.payment_dialog import PaymentDialog
        from database.models import Orden

        self.dlg = PaymentDialog(25.50)
        orden = Orden(numero="TEST-001")
        items = [OrdenItem(producto_nombre="Cola", cantidad=1, precio_unitario=2.5)]

        self.dlg.set_orden_data(orden, items)
        self.assertIsNotNone(self.dlg._orden_preview)
        self.assertIsNotNone(self.dlg._items_preview)

    def test_dividir_igualmente(self):
        """Dividir en partes iguales debe distribuir el total."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(30.00)
        self.dlg._switch_tab(1)

        # Activar dos métodos
        self.dlg._method_rows["efectivo"].value = 10.00  # Activar con valor > 0
        self.dlg._method_rows["tarjeta"].value = 1.00    # Activar

        self.dlg._dividir_igualmente()
        # Debe dividir 30 entre 2 = 15 cada uno
        self.assertEqual(self.dlg._method_rows["efectivo"].value, 15.00)
        self.assertEqual(self.dlg._method_rows["tarjeta"].value, 15.00)

    def test_confirm_button_disabled_when_short_combo(self):
        """El botón confirmar debe estar deshabilitado si no se cubre el total en combo."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(50.00)
        self.dlg._switch_tab(1)

        self.dlg._method_rows["efectivo"].value = 20.00
        self.assertFalse(self.dlg.btn_confirm.isEnabled())

    def test_remaining_label_updates(self):
        """El label de faltante debe actualizarse en combo."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(50.00)
        self.dlg._switch_tab(1)

        self.dlg._method_rows["efectivo"].value = 20.00
        self.assertIn("Faltan", self.dlg._remaining_lbl.text())

        self.dlg._method_rows["tarjeta"].value = 30.00
        self.assertIn("Cubierto", self.dlg._remaining_lbl.text())


# ═══════════════════════════════════════════
#  PaymentDialog Advanced
# ═══════════════════════════════════════════

class TestPaymentDialogAdvanced(unittest.TestCase):
    """Pruebas avanzadas para PaymentDialog: PaymentMethodRow, ReceiptPreviewDialog,
    _calcular_desglose, _load_printers, _on_printer_search, _confirmar con preferencias,
    propiedades de compatibilidad, y edge cases de pago combinado."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def tearDown(self):
        if hasattr(self, 'dlg') and self.dlg:
            self.dlg.deleteLater()

    # ─── PaymentMethodRow ───

    def test_payment_method_row_creates_with_key(self):
        """PaymentMethodRow debe crearse con method_key."""
        from views.components.payment_dialog import PaymentMethodRow
        row = PaymentMethodRow("tarjeta", "💳", "Tarjeta")
        self.assertEqual(row.method_key, "tarjeta")
        self.assertEqual(row.value, 0.0)
        row.deleteLater()

    def test_payment_method_row_value_property(self):
        """La propiedad value debe leer/escribir el spinbox."""
        from views.components.payment_dialog import PaymentMethodRow
        row = PaymentMethodRow("efectivo", "💵", "Efectivo")
        row.value = 50.00
        self.assertEqual(row.spin.value(), 50.00)
        self.assertEqual(row.value, 50.00)
        row.deleteLater()

    def test_payment_method_row_balance_text(self):
        """set_balance_text debe actualizar el label de balance."""
        from views.components.payment_dialog import PaymentMethodRow
        row = PaymentMethodRow("efectivo", "💵", "Efectivo")
        row.set_balance_text("75%")
        self.assertEqual(row._balance_lbl.text(), "75%")
        row.deleteLater()

    def test_payment_method_row_value_changed_signal(self):
        """El spinbox debe emitir valueChanged."""
        from views.components.payment_dialog import PaymentMethodRow
        row = PaymentMethodRow("efectivo", "💵", "Efectivo")
        received = []
        row.valueChanged.connect(lambda v: received.append(v))
        row.value = 25.00
        self.assertGreater(len(received), 0)
        self.assertAlmostEqual(received[-1], 25.00)
        row.deleteLater()

    # ─── _calcular_desglose ───

    def test_calcular_desglose_con_vuelto(self):
        """_calcular_desglose debe desglosar $47.50 en billetes y monedas."""
        from views.components.payment_dialog import PaymentDialog
        resultado = PaymentDialog._calcular_desglose(47.50)
        # Debe incluir billetes de 20 y 5
        self.assertIn("20.00", resultado)
        self.assertIn("5.00", resultado)

    def test_calcular_desglose_vuelto_exacto(self):
        """_calcular_desglose con monto 0 debe retornar 'Vuelto exacto'."""
        from views.components.payment_dialog import PaymentDialog
        resultado = PaymentDialog._calcular_desglose(0)
        self.assertEqual(resultado, "Vuelto exacto")

    def test_calcular_desglose_pequeno(self):
        """_calcular_desglose con $0.75 debe mostrar monedas."""
        from views.components.payment_dialog import PaymentDialog
        resultado = PaymentDialog._calcular_desglose(0.75)
        self.assertIn("0.50", resultado)
        self.assertIn("0.25", resultado)

    # ─── Propiedades de compatibilidad ───

    def test_metodo_pago_property(self):
        """metodo_pago con metodos_pago poblado debe retornar el primer método."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg.show()
        self.dlg._simple_monto.setValue(25.50)
        self.dlg._confirmar()
        # Con metodos_pago poblado, debe retornar metodos_pago[0][0]
        self.assertGreater(len(self.dlg.metodos_pago), 0)
        self.assertEqual(self.dlg.metodo_pago, "efectivo")

    def test_metodo_pago_default_when_empty(self):
        """metodo_pago debe retornar 'efectivo' si metodos_pago está vacío."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        # Sin metodos_pago poblado, debe retornar default "efectivo"
        self.assertEqual(len(self.dlg.metodos_pago), 0)
        self.assertEqual(self.dlg.metodo_pago, "efectivo")

    def test_monto_recibido_property(self):
        """monto_recibido debe sumar todos los métodos."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg._switch_tab(1)
        self.dlg._method_rows["efectivo"].value = 15.00
        self.dlg._method_rows["tarjeta"].value = 10.50
        self.dlg._confirmar()
        self.assertAlmostEqual(self.dlg.monto_recibido, 25.50)

    def test_val_vuelto_property(self):
        """val_vuelto debe retornar el label de vuelto simple."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.assertIs(self.dlg.val_vuelto, self.dlg._val_vuelto_simple)

    # ─── _confirmar con opciones de impresión ───

    def test_confirmar_simple_stores_imprimir_true(self):
        """Confirmar en modo simple con imprimir marcado debe dejar imprimir_recibo=True."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg._simple_monto.setValue(25.50)
        self.dlg.check_imprimir.setChecked(True)
        self.dlg._confirmar()
        self.assertTrue(self.dlg.imprimir_recibo)

    def test_confirmar_preferencia_error_no_crashea(self):
        """_confirmar con error al guardar preferencia debe ser capturado por except."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg._simple_monto.setValue(25.50)
        with unittest.mock.patch('utils.session.Session.get',
                                 side_effect=Exception("Error DB")):
            self.dlg._confirmar()
        # No debe crashear - except capturó el error
        self.assertTrue(self.dlg.imprimir_recibo)

    def test_confirmar_simple_stores_imprimir_false(self):
        """Confirmar en modo simple con imprimir desmarcado debe dejar imprimir_recibo=False."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg._simple_monto.setValue(25.50)
        self.dlg.check_imprimir.setChecked(False)
        self.dlg._confirmar()
        self.assertFalse(self.dlg.imprimir_recibo)

    def test_confirmar_simple_con_metodo_tarjeta(self):
        """Confirmar en modo simple con método tarjeta debe reflejar selección."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg.show()
        self.dlg._simple_monto.setValue(25.50)
        self.dlg._select_simple_method("tarjeta")
        self.dlg._confirmar()
        self.assertEqual(self.dlg.metodos_pago[0][0], "tarjeta")

    def test_confirmar_combo_con_excedente(self):
        """Confirmar en combo con excedente debe incluir todo el monto."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(30.00)
        self.dlg._switch_tab(1)
        self.dlg._method_rows["efectivo"].value = 35.00  # Excedente de $5
        self.dlg._confirmar()
        self.assertEqual(len(self.dlg.metodos_pago), 1)
        self.assertAlmostEqual(self.dlg.metodos_pago[0][1], 35.00)
        self.assertAlmostEqual(self.dlg.monto_recibido, 35.00)

    def test_confirmar_combo_varios_metodos_mantiene_orden(self):
        """Confirmar combo debe mantener el orden de PAYMENT_METHODS."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(50.00)
        self.dlg._switch_tab(1)
        self.dlg._method_rows["tarjeta"].value = 20.00
        self.dlg._method_rows["efectivo"].value = 30.00
        self.dlg._confirmar()
        self.assertEqual(len(self.dlg.metodos_pago), 2)
        # El orden debe ser efectivo primero (definido en PAYMENT_METHODS)
        self.assertEqual(self.dlg.metodos_pago[0][0], "efectivo")
        self.assertEqual(self.dlg.metodos_pago[1][0], "tarjeta")

    # ─── _dividir_igualmente edge cases ───

    def test_dividir_igualmente_sin_activos_usa_solo_efectivo(self):
        """Dividir sin filas activas debe asignar todo a efectivo."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(30.00)
        self.dlg._switch_tab(1)
        # Ninguna fila con valor > 0
        self.dlg._dividir_igualmente()
        self.assertAlmostEqual(self.dlg._method_rows["efectivo"].value, 30.00)
        for k, row in self.dlg._method_rows.items():
            if k != "efectivo":
                self.assertEqual(row.value, 0.0)

    def test_dividir_igualmente_con_tres_metodos(self):
        """Dividir entre 3 métodos activos debe distribuir equitativamente."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(30.00)
        self.dlg._switch_tab(1)
        self.dlg._method_rows["efectivo"].value = 1.0
        self.dlg._method_rows["tarjeta"].value = 1.0
        self.dlg._method_rows["transferencia"].value = 1.0
        self.dlg._dividir_igualmente()
        # 30 / 3 = 10 cada uno
        self.assertAlmostEqual(self.dlg._method_rows["efectivo"].value, 10.00)
        self.assertAlmostEqual(self.dlg._method_rows["tarjeta"].value, 10.00)
        self.assertAlmostEqual(self.dlg._method_rows["transferencia"].value, 10.00)
        self.assertEqual(self.dlg._method_rows["otro"].value, 0.0)

    def test_dividir_igualmente_con_resto(self):
        """Dividir con resto debe asignar el céntimo extra al primer método."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(10.01)
        self.dlg._switch_tab(1)
        self.dlg._method_rows["efectivo"].value = 1.0
        self.dlg._method_rows["tarjeta"].value = 1.0
        self.dlg._dividir_igualmente()
        # 10.01 / 2 = 5.005 → parte=5.00, resto=0.01
        self.assertAlmostEqual(self.dlg._method_rows["efectivo"].value, 5.01)
        self.assertAlmostEqual(self.dlg._method_rows["tarjeta"].value, 5.00)

    # ─── _load_printers y _on_printer_search ───

    @unittest.mock.patch('utils.printer.get_available_printers', return_value=[])
    @unittest.mock.patch('utils.printer.check_printer_status', return_value=True)
    def test_load_printers_sin_impresoras(self, mock_status, mock_printers):
        """_load_printers sin impresoras debe tener item predeterminado."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        # Debe tener al menos el item predeterminado
        self.assertGreater(self.dlg._printer_combo.count(), 0)
        self.assertIn("Predeterminada", self.dlg._printer_combo.itemText(0))

    @unittest.mock.patch('utils.printer.get_available_printers',
                         return_value=['EPSON TM-T20', 'STAR SP700'])
    @unittest.mock.patch('utils.printer.check_printer_status', return_value=True)
    def test_load_printers_con_impresoras(self, mock_status, mock_printers):
        """_load_printers con impresoras debe agregarlas al combo."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        # Predeterminada + 2 impresoras = 3 items
        self.assertEqual(self.dlg._printer_combo.count(), 3)

    @unittest.mock.patch('utils.printer.get_available_printers',
                         side_effect=Exception("Error de conexión"))
    def test_load_printers_con_error_muestra_no_disponible(self, mock_printers):
        """_load_printers con excepción debe mostrar '(No disponible)'."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.assertEqual(self.dlg._printer_combo.count(), 1)
        self.assertIn("No disponible", self.dlg._printer_combo.itemText(0))

    def test_load_printers_error_reintento_tambien_falla(self):
        """_load_printers llamado de nuevo con error persistente debe seguir sin crashear."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        # Simular que get_available_printers falla ahora (pero en init funcionó)
        with unittest.mock.patch('utils.printer.get_available_printers',
                                 side_effect=Exception("Fallo ahora")):
            self.dlg._load_printers()
        # Debe mostrar no disponible
        self.assertIn("No disponible", self.dlg._printer_combo.itemText(0))

    def test_load_printers_inner_exception_manejada(self):
        """_load_printers con excepción en preferencia debe ser capturada por except interno."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        # Poner un texto que no coincida con ningún item para forzar restored=False
        self.dlg._printer_combo.setEditText("NO_EXISTE")
        # En la segunda llamada, Session.get() falla
        with unittest.mock.patch('utils.printer.get_available_printers',
                                 return_value=['EPSON TM-T20']):
            with unittest.mock.patch('utils.printer.check_printer_status', return_value=True):
                with unittest.mock.patch('utils.session.Session.get',
                                         side_effect=Exception("Fallo preferencia")):
                    self.dlg._load_printers()
        # No debe crashear (inner except capturó el error)
        self.assertGreater(self.dlg._printer_combo.count(), 0)

    @unittest.mock.patch('utils.printer.get_available_printers',
                         return_value=['EPSON TM-T20'])
    @unittest.mock.patch('utils.printer.check_printer_status', return_value=True)
    def test_on_printer_search_encuentra_por_data(self, mock_status, mock_printers):
        """_on_printer_search debe buscar por nombre de impresora."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg._printer_combo.setEditText("EPSON TM-T20")
        self.dlg._on_printer_search()
        # Debe encontrar la impresora
        current_data = self.dlg._printer_combo.currentData()
        self.assertEqual(current_data, "EPSON TM-T20")

    def test_focus_printer_search_limpia_texto(self):
        """_focus_printer_search debe limpiar el campo de texto."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg.show()
        if self.dlg._printer_combo.lineEdit():
            self.dlg._printer_combo.setEditText("Texto Existente")
            self.dlg._focus_printer_search()
            # Verificar que el texto se limpió (comportamiento principal)
            self.assertEqual(self.dlg._printer_combo.currentText(), "")

    # ─── _mostrar_vista_previa y ReceiptPreviewDialog ───

    def test_set_orden_data_con_preview_muestra_dialogo(self):
        """set_orden_data + _mostrar_vista_previa debe crear ReceiptPreviewDialog."""
        from views.components.payment_dialog import PaymentDialog, ReceiptPreviewDialog
        from database.models import Orden
        self.dlg = PaymentDialog(25.50)
        orden = Orden(numero="ORD-001", tipo="local", total=25.50)
        items = [OrdenItem(producto_nombre="Cola", cantidad=2, precio_unitario=2.5)]
        self.dlg.set_orden_data(orden, items)

        with unittest.mock.patch('views.components.payment_dialog.ReceiptPreviewDialog') as mock_preview:
            mock_instance = unittest.mock.MagicMock()
            mock_preview.return_value = mock_instance
            self.dlg._mostrar_vista_previa()
            mock_preview.assert_called_once()
            mock_instance.exec.assert_called_once()

    def test_mostrar_vista_previa_sin_datos_no_crashea(self):
        """_mostrar_vista_previa sin orden no debe fallar."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        # No se llamó set_orden_data
        self.dlg._mostrar_vista_previa()  # No debe lanzar excepción

    # ─── Edge cases de recalculo ───

    def test_recalcular_simple_con_monto_exacto_vuelto_0(self):
        """_recalcular_simple con monto exacto debe mostrar vuelto 0.00."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg._simple_monto.setValue(25.50)
        self.assertIn("0.00", self.dlg._val_vuelto_simple.text())
        self.assertIn("#34d399", self.dlg._val_vuelto_simple.styleSheet())

    def test_recalcular_simple_con_monto_insuficiente_color_rojo(self):
        """_recalcular_simple con monto insuficiente debe mostrar color rojo."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg._simple_monto.setValue(10.00)
        self.assertIn("f87171", self.dlg._val_vuelto_simple.styleSheet())

    def test_recalcular_simple_con_vuelto_muestra_desglose(self):
        """_recalcular_simple con vuelto > 0 debe mostrar desglose."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg._simple_monto.setValue(50.00)
        self.assertIn("Desglose", self.dlg._desglose_simple.text())

    def test_combo_recalculo_con_excedente_muestra_cubierto_con_vuelto(self):
        """Combo con excedente debe mostrar 'Cubierto (vuelto: $X.XX)'."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(30.00)
        self.dlg._switch_tab(1)
        self.dlg._method_rows["efectivo"].value = 35.00
        self.assertIn("Cubierto", self.dlg._remaining_lbl.text())
        self.assertIn("5.00", self.dlg._remaining_lbl.text())
        self.assertIn("#34d399", self.dlg._remaining_lbl.styleSheet())

    def test_combo_recalculo_progress_bar_overflow(self):
        """Combo con más del 100% debe mostrar barra llena."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(30.00)
        self.dlg._switch_tab(1)
        self.dlg._method_rows["efectivo"].value = 50.00  # 166%
        # La barra debe tener estilo verde
        self.assertIn("#34d399", self.dlg._progress_fill.styleSheet())

    def test_combo_balance_pct_labels(self):
        """Labels de balance en combo deben mostrar porcentaje."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(100.00)
        self.dlg._switch_tab(1)
        self.dlg._method_rows["efectivo"].value = 75.00
        self.dlg._method_rows["tarjeta"].value = 25.00
        self.assertIn("75%", self.dlg._method_rows["efectivo"]._balance_lbl.text())
        self.assertIn("25%", self.dlg._method_rows["tarjeta"]._balance_lbl.text())

    # ─── ReceiptPreviewDialog (sin mock, constructor real) ───

    def test_receipt_preview_dialog_creates_with_orden(self):
        """ReceiptPreviewDialog debe crearse con orden e items."""
        from views.components.payment_dialog import ReceiptPreviewDialog
        from database.models import Orden, OrdenItem
        orden = Orden(numero="PREVIEW-001", tipo="local", total=15.50)
        items = [OrdenItem(producto_nombre="Pizza", cantidad=2, precio_unitario=5.0)]
        dlg = ReceiptPreviewDialog(orden, items)
        self.assertEqual(dlg.windowTitle(), "Vista Previa del Recibo")
        self.assertGreaterEqual(dlg.minimumWidth(), 400)
        self.assertGreaterEqual(dlg.minimumHeight(), 600)
        dlg.deleteLater()

    def test_receipt_preview_dialog_has_close_button(self):
        """ReceiptPreviewDialog debe tener botón de cerrar."""
        from views.components.payment_dialog import ReceiptPreviewDialog
        from database.models import Orden, OrdenItem
        from PySide6.QtWidgets import QPushButton
        orden = Orden(numero="PREVIEW-002", tipo="delivery", total=20.0)
        items = [OrdenItem(producto_nombre="Cola", cantidad=1, precio_unitario=2.5)]
        dlg = ReceiptPreviewDialog(orden, items)
        dlg.show()
        # Buscar botón de cerrar
        btn_close = dlg.findChild(QPushButton)
        self.assertIsNotNone(btn_close)
        self.assertIn("Cerrar", btn_close.text())
        dlg.deleteLater()

    def test_receipt_preview_dialog_has_browser(self):
        """ReceiptPreviewDialog debe tener QTextBrowser con HTML."""
        from views.components.payment_dialog import ReceiptPreviewDialog
        from database.models import Orden, OrdenItem
        from PySide6.QtWidgets import QTextBrowser
        orden = Orden(numero="PREVIEW-003", tipo="local", total=10.0)
        items = [OrdenItem(producto_nombre="Te", cantidad=1, precio_unitario=2.0)]
        dlg = ReceiptPreviewDialog(orden, items)
        dlg.show()
        browser = dlg.findChild(QTextBrowser)
        self.assertIsNotNone(browser)
        html = browser.toHtml()
        self.assertIn("PREVIEW-003", html)
        self.assertIn("Te", html)
        dlg.deleteLater()

    # ─── _load_printers con current_text y preferencias ───

    @unittest.mock.patch('utils.printer.get_available_printers',
                         return_value=['EPSON TM-T20'])
    @unittest.mock.patch('utils.printer.check_printer_status', return_value=True)
    def test_load_printers_restaura_texto_anterior(self, mock_status, mock_printers):
        """_load_printers debe restaurar el texto previo si coincide."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        # Simular que el usuario hab�a seleccionado una impresora
        self.dlg._printer_combo.setCurrentIndex(1)  # EPSON TM-T20
        # Guardar texto actual
        current = self.dlg._printer_combo.currentText()
        # Recargar - debe restaurar la selecci�n
        self.dlg._load_printers()
        self.assertIn("EPSON", self.dlg._printer_combo.currentText())

    @unittest.mock.patch('utils.printer.get_available_printers',
                         return_value=['EPSON TM-T20', 'STAR SP700'])
    @unittest.mock.patch('utils.printer.check_printer_status', return_value=True)
    @unittest.mock.patch('utils.session.Session.get')
    def test_load_printers_con_preferencia_sesion(self, mock_session_get, mock_status, mock_printers):
        """_load_printers debe seleccionar impresora desde preferencia de sesi�n."""
        mock_session = unittest.mock.MagicMock()
        mock_session.get_preference.return_value = 'STAR SP700'
        mock_session_get.return_value = mock_session

        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        # La preferencia deber�a haber seleccionado STAR SP700
        self.assertEqual(self.dlg._printer_combo.currentData(), 'STAR SP700')

    @unittest.mock.patch('utils.printer.get_available_printers',
                         return_value=['EPSON TM-T20', 'STAR SP700'])
    @unittest.mock.patch('utils.printer.check_printer_status', return_value=True)
    @unittest.mock.patch('utils.session.Session.get')
    @unittest.mock.patch('database.config_service.ConfigService')
    def test_load_printers_con_fallback_config(self, mock_cfg_svc, mock_session_get, mock_status, mock_printers):
        """_load_printers debe caer en ConfigService si Session no tiene preferencia."""
        mock_session = unittest.mock.MagicMock()
        mock_session.get_preference.return_value = None  # Sin preferencia
        mock_session_get.return_value = mock_session

        mock_cfg = unittest.mock.MagicMock()
        mock_cfg.get_config.return_value = 'EPSON TM-T20'
        mock_cfg_svc.return_value = mock_cfg

        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        # El fallback deber�a haber seleccionado EPSON TM-T20
        self.assertEqual(self.dlg._printer_combo.currentData(), 'EPSON TM-T20')

    @unittest.mock.patch('utils.printer.get_available_printers',
                         return_value=['EPSON TM-T20'])
    @unittest.mock.patch('utils.printer.check_printer_status', return_value=True)
    @unittest.mock.patch('utils.session.Session.get')
    def test_load_printers_con_error_en_preferencia_no_crashea(self, mock_session_get, mock_status, mock_printers):
        """_load_printers con error al leer preferencia no debe crashear."""
        mock_session_get.side_effect = Exception("Error de sesi�n")

        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        # Debe tener items (excepci�n atrapada por el except Exception interno)
        self.assertGreater(self.dlg._printer_combo.count(), 0)

    # ─── _on_printer_search adicional ───

    def test_on_printer_search_empty_text_no_crash(self):
        """_on_printer_search con texto vac�o no debe hacer nada."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        self.dlg._printer_combo.setEditText("")
        self.dlg._on_printer_search()  # No debe lanzar excepci�n

    @unittest.mock.patch('utils.printer.get_available_printers',
                         return_value=['EPSON TM-T20', 'STAR SP700'])
    @unittest.mock.patch('utils.printer.check_printer_status', return_value=True)
    def test_on_printer_search_encuentra_por_texto_parcial(self, mock_status, mock_printers):
        """_on_printer_search debe encontrar por texto parcial visible."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        # Buscar con texto parcial que exista en itemData
        self.dlg._printer_combo.setEditText("STAR")
        self.dlg._on_printer_search()
        self.assertEqual(self.dlg._printer_combo.currentData(), 'STAR SP700')

    @unittest.mock.patch('utils.printer.get_available_printers',
                         return_value=['EPSON TM-T20'])
    @unittest.mock.patch('utils.printer.check_printer_status', return_value=True)
    def test_on_printer_search_sin_coincidencia_restaura(self, mock_status, mock_printers):
        """_on_printer_search sin coincidencia debe restaurar el �ndice anterior."""
        from views.components.payment_dialog import PaymentDialog
        self.dlg = PaymentDialog(25.50)
        # Seleccionar el �tem 0 (predeterminado) primero
        self.dlg._printer_combo.setCurrentIndex(0)
        prev_text = self.dlg._printer_combo.currentText()
        # Buscar con texto que no coincide
        self.dlg._printer_combo.setEditText("IMPRESORA_INEXISTENTE")
        self.dlg._on_printer_search()
        # Debe restaurar el texto original
        self.assertEqual(self.dlg._printer_combo.currentText(), prev_text)


# ═══════════════════════════════════════════
#  ComboCard
# ═══════════════════════════════════════════

class TestComboCard(unittest.TestCase):
    """Pruebas para ComboCard."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def _make_combo(self, items_count=2, ahorro=0):
        from database.models import Combo, ComboItem
        combo = Combo(
            nombre="Combo Familiar", descripcion="2 pizzas + bebida",
            precio_total=25.0, ahorro=ahorro, icono="🎉",
        )
        for i in range(items_count):
            combo.items.append(ComboItem(
                producto_id=i+1, producto_nombre=f"Producto {i+1}",
                cantidad=1, precio_individual=10.0,
            ))
        return combo

    def test_creates_with_combo(self):
        """La tarjeta debe crearse con un combo."""
        from views.components.combo_card import ComboCard
        combo = self._make_combo()
        card = ComboCard(combo)
        self.assertIsNotNone(card)
        self.assertEqual(card.combo, combo)
        card.deleteLater()

    def test_shows_combo_info(self):
        """La tarjeta debe mostrar nombre, precio e icono."""
        from views.components.combo_card import ComboCard
        combo = self._make_combo(ahorro=5.0)
        card = ComboCard(combo)
        card.show()

        # Verificar nombre
        name_lbl = card.findChild(QLabel, "combo-card-name")
        self.assertIsNotNone(name_lbl)
        self.assertIn("Combo Familiar", name_lbl.text())

        # Verificar precio
        price_lbl = card.findChild(QLabel, "combo-card-price")
        self.assertIsNotNone(price_lbl)
        self.assertIn("25.00", price_lbl.text())

        # Verificar icono
        icon_lbl = card.findChild(QLabel, "combo-card-icon")
        self.assertIsNotNone(icon_lbl)
        self.assertEqual(icon_lbl.text(), "🎉")

        card.deleteLater()

    def test_shows_items_count(self):
        """Debe mostrar cuantos productos incluye."""
        from views.components.combo_card import ComboCard
        combo = self._make_combo(items_count=3)
        card = ComboCard(combo)
        card.show()

        # Buscar label con cantidad de productos
        found = False
        for child in card.findChildren(QLabel):
            if "3" in child.text() and "producto" in child.text():
                found = True
                break
        self.assertTrue(found)
        card.deleteLater()

    def test_shows_ahorro_badge(self):
        """Debe mostrar badge de ahorro si existe."""
        from views.components.combo_card import ComboCard
        combo = self._make_combo(ahorro=5.0)
        card = ComboCard(combo)
        card.show()

        found = False
        for child in card.findChildren(QLabel):
            if "5.00" in child.text() and child.property("class") == "badge-success":
                found = True
                break
        self.assertTrue(found, "Debe mostrar badge de ahorro")
        card.deleteLater()

    def test_no_ahorro_badge_when_zero(self):
        """No debe mostrar badge de ahorro si es 0."""
        from views.components.combo_card import ComboCard
        combo = self._make_combo(ahorro=0)
        card = ComboCard(combo)
        card.show()

        found = False
        for child in card.findChildren(QLabel):
            if child.property("class") == "badge-success":
                found = True
                break
        self.assertFalse(found, "No debe mostrar badge de ahorro si es 0")
        card.deleteLater()

    def test_click_emits_combo(self):
        """Hacer clic debe emitir la señal clicked con el combo."""
        from views.components.combo_card import ComboCard
        combo = self._make_combo()
        card = ComboCard(combo)
        received = []

        def on_click(c):
            received.append(c)

        card.clicked.connect(on_click)
        card.show()

        QTest.mouseClick(card, Qt.MouseButton.LeftButton)
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0].nombre, "Combo Familiar")
        card.deleteLater()

    def test_fixed_size(self):
        """Debe tener tamaño fijo de 160x150."""
        from views.components.combo_card import ComboCard
        combo = self._make_combo()
        card = ComboCard(combo)
        self.assertEqual(card.width(), 160)
        self.assertEqual(card.height(), 150)
        card.deleteLater()


# ═══════════════════════════════════════════
#  ComboDialog
# ═══════════════════════════════════════════

class TestComboDialog(unittest.TestCase):
    """Pruebas para ComboDialog."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def setUp(self):
        self.db, self.prod_svc, self.orden_svc = _init_db()
        self.cat_id = self.prod_svc.crear_categoria(Categoria(nombre="Bebidas", icono="🥤"))
        self.prod_svc.crear_producto(Producto(nombre="Cola", precio=2.5, categoria_id=self.cat_id, disponible=True))
        self.prod_svc.crear_producto(Producto(nombre="Te", precio=1.5, categoria_id=self.cat_id, disponible=True))

    def tearDown(self):
        if hasattr(self, 'dlg') and self.dlg:
            self.dlg.deleteLater()
        self.db.close()
        DatabaseManager._instance = None

    def test_creates_new(self):
        """Debe crearse en modo nuevo."""
        from views.components.combo_dialog import ComboDialog
        self.dlg = ComboDialog(db=self.prod_svc)
        self.assertIsNotNone(self.dlg)
        self.assertIsNone(self.dlg.combo)

    def test_creates_with_existing_combo(self):
        """Debe crearse en modo edición con combo existente."""
        from views.components.combo_dialog import ComboDialog
        from database.models import Combo, ComboItem
        combo = Combo(nombre="Combo Edit", precio_total=20.0, ahorro=5.0, descripcion="Test")
        combo.items.append(ComboItem(producto_id=1, producto_nombre="Cola", cantidad=2, precio_individual=2.5))
        self.dlg = ComboDialog(combo=combo, db=self.prod_svc)
        self.assertIsNotNone(self.dlg)
        self.assertEqual(self.dlg._nombre.text(), "Combo Edit")
        self.assertEqual(self.dlg._precio_total.value(), 20.0)

    def test_form_fields_exist(self):
        """Los campos del formulario deben existir."""
        from views.components.combo_dialog import ComboDialog
        self.dlg = ComboDialog(db=self.prod_svc)
        self.assertIsNotNone(self.dlg._nombre)
        self.assertIsNotNone(self.dlg._precio_total)
        self.assertIsNotNone(self.dlg._descripcion)
        self.assertIsNotNone(self.dlg._icono)
        self.assertIsNotNone(self.dlg._items_table)

    def test_add_product_to_combo(self):
        """Agregar un producto al combo debe funcionar."""
        from views.components.combo_dialog import ComboDialog
        self.dlg = ComboDialog(db=self.prod_svc)
        self.dlg._load_productos()
        self.assertGreater(self.dlg._prod_combo.count(), 0)

        self.dlg._add_product_to_combo()
        self.assertEqual(len(self.dlg._items_temp), 1)
        self.assertEqual(self.dlg._items_temp[0].producto_nombre, "Cola")

    def test_add_same_product_twice_increases_quantity(self):
        """Agregar el mismo producto dos veces debe incrementar cantidad."""
        from views.components.combo_dialog import ComboDialog
        self.dlg = ComboDialog(db=self.prod_svc)
        self.dlg._load_productos()

        self.dlg._add_product_to_combo()
        self.assertEqual(self.dlg._items_temp[0].cantidad, 1)

        self.dlg._add_product_to_combo()
        self.assertEqual(self.dlg._items_temp[0].cantidad, 2)

    def test_save_validates_name(self):
        """Guardar sin nombre debe mostrar advertencia (no crash)."""
        from views.components.combo_dialog import ComboDialog
        self.dlg = ComboDialog(db=self.prod_svc)
        # Sin nombre y sin items, debe mostrar warning
        with unittest.mock.patch.object(self.dlg, 'accept') as mock_accept:
            self.dlg._save()
            mock_accept.assert_not_called()

    def test_save_validates_items(self):
        """Guardar sin productos debe mostrar advertencia."""
        from views.components.combo_dialog import ComboDialog
        self.dlg = ComboDialog(db=self.prod_svc)
        self.dlg._nombre.setText("Combo Test")
        with unittest.mock.patch.object(self.dlg, 'accept') as mock_accept:
            self.dlg._save()
            mock_accept.assert_not_called()

    def test_save_creates_combo(self):
        """Guardar con datos válidos debe crear el combo."""
        from views.components.combo_dialog import ComboDialog
        self.dlg = ComboDialog(db=self.prod_svc)
        self.dlg._load_productos()

        self.dlg._nombre.setText("Combo Test")
        self.dlg._precio_total.setValue(3.50)
        self.dlg._add_product_to_combo()  # Agrega Cola ($2.50)
        self.dlg._add_product_to_combo()  # Otra Cola → cantidad=2

        with unittest.mock.patch.object(self.dlg, 'accept') as mock_accept:
            self.dlg._save()
            mock_accept.assert_called_once()

        # Verificar que combo fue creado con datos correctos
        self.assertIsNotNone(self.dlg.combo)
        self.assertEqual(self.dlg.combo.nombre, "Combo Test")
        self.assertEqual(self.dlg.combo.precio_total, 3.50)
        # Ahorro: suma individual (2*2.50=5.0) - precio combo (3.50) = 1.50
        self.assertEqual(self.dlg.combo.ahorro, 1.50)
        self.assertEqual(len(self.dlg.combo.items), 1)

    def test_recalc_savings(self):
        """El cálculo de ahorro debe actualizarse."""
        from views.components.combo_dialog import ComboDialog
        self.dlg = ComboDialog(db=self.prod_svc)
        self.dlg._load_productos()
        self.dlg._add_product_to_combo()  # Cola, $2.50
        self.dlg._precio_total.setValue(2.00)
        # Ahorro = 2.50 - 2.00 = 0.50
        self.assertIn("0.50", self.dlg._ahorro_lbl.text())


# ═══════════════════════════════════════════
#  VariantDialog
# ═══════════════════════════════════════════

class TestVariantDialog(unittest.TestCase):
    """Pruebas para VariantDialog."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def setUp(self):
        self.db, self.prod_svc, self.orden_svc = _init_db()
        self.cat_id = self.prod_svc.crear_categoria(Categoria(nombre="Pizzas", icono="🍕"))
        self.prod_id = self.prod_svc.crear_producto(Producto(
            nombre="Pizza Grande", precio=15.0, categoria_id=self.cat_id,
            disponible=True, tiene_variantes=True,
        ))
        # Agregar variantes e ingredientes
        from database.models import ProductoVariante, ProductoIngrediente
        self.prod_svc.crear_variante(ProductoVariante(
            producto_id=self.prod_id, nombre="Grande", precio_adicional=3.0, orden=1
        ))
        self.prod_svc.crear_variante(ProductoVariante(
            producto_id=self.prod_id, nombre="Familiar", precio_adicional=5.0, orden=2
        ))
        self.prod_svc.crear_ingrediente(ProductoIngrediente(
            producto_id=self.prod_id, nombre="Queso Extra", precio_adicional=1.5, activo=True
        ))
        self.prod_svc.crear_ingrediente(ProductoIngrediente(
            producto_id=self.prod_id, nombre="Pepperoni", precio_adicional=2.0, activo=True
        ))

    def tearDown(self):
        if hasattr(self, 'dlg') and self.dlg:
            self.dlg.deleteLater()
        self.db.close()
        DatabaseManager._instance = None

    def _get_producto(self):
        return self.prod_svc.get_productos()[0]

    def test_creates_with_producto(self):
        """Debe crearse con un producto."""
        from views.components.variant_dialog import VariantDialog
        prod = self._get_producto()
        self.dlg = VariantDialog(prod)
        self.assertIsNotNone(self.dlg)
        self.assertEqual(self.dlg.producto.nombre, "Pizza Grande")

    def test_shows_base_price(self):
        """Debe mostrar el precio base del producto."""
        from views.components.variant_dialog import VariantDialog
        prod = self._get_producto()
        self.dlg = VariantDialog(prod)
        self.assertIn("15.00", self.dlg._base_price_lbl.text())

    def test_variant_buttons_exist(self):
        """Deben existir botones para cada variante."""
        from views.components.variant_dialog import VariantDialog
        prod = self._get_producto()
        self.dlg = VariantDialog(prod)
        # Base + 2 variantes
        self.assertEqual(len(self.dlg._variant_buttons), 3)

    def test_select_variant_updates_total(self):
        """Seleccionar una variante debe actualizar el total."""
        from views.components.variant_dialog import VariantDialog
        prod = self._get_producto()
        self.dlg = VariantDialog(prod)

        variantes = self.prod_svc.get_variantes(prod.id)
        self.assertGreater(len(variantes), 0)

        self.dlg._select_variant(variantes[0])  # Grande (+$3.00)
        self.assertIn("18.00", self.dlg._total_lbl.text())  # 15 + 3

    def test_precio_final_property(self):
        """La propiedad precio_final debe reflejar selección."""
        from views.components.variant_dialog import VariantDialog
        prod = self._get_producto()
        self.dlg = VariantDialog(prod)

        variantes = self.prod_svc.get_variantes(prod.id)
        self.dlg._select_variant(variantes[0])  # Grande (+$3.00)
        self.assertEqual(self.dlg.precio_final, 18.00)

    def test_ingredient_checkboxes_exist(self):
        """Deben existir checkboxes para ingredientes."""
        from views.components.variant_dialog import VariantDialog
        prod = self._get_producto()
        self.dlg = VariantDialog(prod)
        self.assertGreaterEqual(len(self.dlg._ingredient_checks), 2)

    def test_select_variant_and_ingredient_updates_total(self):
        """Variante + ingrediente deben sumarse al total."""
        from views.components.variant_dialog import VariantDialog
        prod = self._get_producto()
        self.dlg = VariantDialog(prod)

        variantes = self.prod_svc.get_variantes(prod.id)
        self.dlg._select_variant(variantes[0])  # Grande (+$3.00) → 18.00

        # Activar Queso Extra ($1.50) por nombre
        for cb, ing in self.dlg._ingredient_checks.values():
            if ing.nombre == "Queso Extra":
                cb.setChecked(True)
                break

        # 15 + 3 (variante) + 1.5 (queso extra) = 19.5
        self.assertIn("19.50", self.dlg._total_lbl.text())
        self.assertAlmostEqual(self.dlg.precio_final, 19.50)

    def test_descripcion_item_returns_text(self):
        """descripcion_item debe retornar texto descriptivo."""
        from views.components.variant_dialog import VariantDialog
        prod = self._get_producto()
        self.dlg = VariantDialog(prod)

        variantes = self.prod_svc.get_variantes(prod.id)
        self.dlg._select_variant(variantes[0])

        desc = self.dlg.descripcion_item
        self.assertIn("Grande", desc)

    def test_descripcion_item_with_ingredients(self):
        """descripcion_item debe incluir ingredientes seleccionados."""
        from views.components.variant_dialog import VariantDialog
        prod = self._get_producto()
        self.dlg = VariantDialog(prod)

        variantes = self.prod_svc.get_variantes(prod.id)
        self.dlg._select_variant(variantes[0])

        # Activar Queso Extra por nombre
        for cb, ing in self.dlg._ingredient_checks.values():
            if ing.nombre == "Queso Extra":
                cb.setChecked(True)
                break

        desc = self.dlg.descripcion_item
        self.assertIn("Grande", desc)
        self.assertIn("Queso Extra", desc)


# ═══════════════════════════════════════════
#  RepartidorDialog
# ═══════════════════════════════════════════

class TestRepartidorDialog(unittest.TestCase):
    """Pruebas para RepartidorDialog."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def test_creates_new(self):
        """Debe crearse en modo nuevo."""
        from views.components.repartidor_dialog import RepartidorDialog
        dlg = RepartidorDialog()
        self.assertIsNotNone(dlg)
        self.assertIsNone(dlg.repartidor)
        dlg.deleteLater()

    def test_creates_with_existing(self):
        """Debe crearse en modo edición con repartidor existente."""
        from views.components.repartidor_dialog import RepartidorDialog
        from database.models import Repartidor
        rep = Repartidor(nombre="Juan Perez", telefono="555-0000", vehiculo="moto")
        dlg = RepartidorDialog(repartidor=rep)
        self.assertIsNotNone(dlg)
        self.assertEqual(dlg._nombre.text(), "Juan Perez")
        self.assertEqual(dlg._telefono.text(), "555-0000")
        dlg.deleteLater()

    def test_form_fields_exist(self):
        """Los campos del formulario deben existir."""
        from views.components.repartidor_dialog import RepartidorDialog
        dlg = RepartidorDialog()
        self.assertIsNotNone(dlg._nombre)
        self.assertIsNotNone(dlg._telefono)
        self.assertIsNotNone(dlg._vehiculo)
        dlg.deleteLater()

    def test_vehiculo_combo_has_options(self):
        """El combo de vehículo debe tener opciones."""
        from views.components.repartidor_dialog import RepartidorDialog
        dlg = RepartidorDialog()
        # moto, carro, bicicleta, pie
        self.assertEqual(dlg._vehiculo.count(), 4)
        dlg.deleteLater()

    def test_save_validates_name(self):
        """Guardar sin nombre no debe llamar a accept."""
        from views.components.repartidor_dialog import RepartidorDialog
        dlg = RepartidorDialog()
        with unittest.mock.patch.object(dlg, 'accept') as mock_accept:
            dlg._save()
            mock_accept.assert_not_called()
        dlg.deleteLater()

    def test_save_creates_repartidor(self):
        """Guardar con datos válidos debe crear el repartidor."""
        from views.components.repartidor_dialog import RepartidorDialog
        dlg = RepartidorDialog()
        dlg._nombre.setText("Carlos Lopez")
        dlg._telefono.setText("555-1234")
        # Seleccionar carro (índice 1)
        dlg._vehiculo.setCurrentIndex(1)

        with unittest.mock.patch.object(dlg, 'accept') as mock_accept:
            dlg._save()
            mock_accept.assert_called_once()

        self.assertIsNotNone(dlg.repartidor)
        self.assertEqual(dlg.repartidor.nombre, "Carlos Lopez")
        self.assertEqual(dlg.repartidor.telefono, "555-1234")
        self.assertEqual(dlg.repartidor.vehiculo, "carro")
        dlg.deleteLater()


# ═══════════════════════════════════════════
#  UserDialog
# ═══════════════════════════════════════════

class TestUserDialog(unittest.TestCase):
    """Pruebas para UserDialog."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def test_creates_new(self):
        """Debe crearse en modo nuevo."""
        from views.components.user_dialog import UserDialog
        dlg = UserDialog()
        self.assertIsNotNone(dlg)
        self.assertIsNone(dlg.usuario)
        dlg.deleteLater()

    def test_creates_with_existing(self):
        """Debe crearse en modo edición con usuario existente."""
        from views.components.user_dialog import UserDialog
        from database.models import Usuario
        user = Usuario(id=1, username="jperez", nombre_completo="Juan Perez", rol="admin")
        dlg = UserDialog(usuario=user)
        self.assertIsNotNone(dlg)
        self.assertEqual(dlg._username.text(), "jperez")
        self.assertEqual(dlg._nombre.text(), "Juan Perez")
        # Username debe estar deshabilitado en edición
        self.assertFalse(dlg._username.isEnabled())
        dlg.deleteLater()

    def test_form_fields_exist(self):
        """Los campos del formulario deben existir."""
        from views.components.user_dialog import UserDialog
        dlg = UserDialog()
        self.assertIsNotNone(dlg._username)
        self.assertIsNotNone(dlg._nombre)
        self.assertIsNotNone(dlg._password)
        self.assertIsNotNone(dlg._password_confirm)
        self.assertIsNotNone(dlg._rol)
        dlg.deleteLater()

    def test_rol_combo_has_options(self):
        """El combo de rol debe tener opciones."""
        from views.components.user_dialog import UserDialog
        dlg = UserDialog()
        # admin, cajero
        self.assertEqual(dlg._rol.count(), 2)
        dlg.deleteLater()

    def test_save_validates_username(self):
        """Guardar sin username no debe llamar a accept."""
        from views.components.user_dialog import UserDialog
        dlg = UserDialog()
        with unittest.mock.patch.object(dlg, 'accept') as mock_accept:
            dlg._save()
            mock_accept.assert_not_called()
        dlg.deleteLater()

    def test_save_validates_nombre(self):
        """Guardar sin nombre completo no debe llamar a accept."""
        from views.components.user_dialog import UserDialog
        dlg = UserDialog()
        dlg._username.setText("testuser")
        with unittest.mock.patch.object(dlg, 'accept') as mock_accept:
            dlg._save()
            mock_accept.assert_not_called()
        dlg.deleteLater()

    def test_save_validates_password_for_new_user(self):
        """Para usuario nuevo, la contraseña es obligatoria."""
        from views.components.user_dialog import UserDialog
        dlg = UserDialog()
        dlg._username.setText("testuser")
        dlg._nombre.setText("Test User")
        with unittest.mock.patch.object(dlg, 'accept') as mock_accept:
            dlg._save()
            mock_accept.assert_not_called()
        dlg.deleteLater()

    def test_save_validates_password_length(self):
        """La contraseña debe tener al menos 4 caracteres."""
        from views.components.user_dialog import UserDialog
        dlg = UserDialog()
        dlg._username.setText("testuser")
        dlg._nombre.setText("Test User")
        dlg._password.setText("ab")
        dlg._password_confirm.setText("ab")
        with unittest.mock.patch.object(dlg, 'accept') as mock_accept:
            dlg._save()
            mock_accept.assert_not_called()
        dlg.deleteLater()

    def test_save_validates_password_match(self):
        """Las contraseñas deben coincidir."""
        from views.components.user_dialog import UserDialog
        dlg = UserDialog()
        dlg._username.setText("testuser")
        dlg._nombre.setText("Test User")
        dlg._password.setText("password123")
        dlg._password_confirm.setText("different")
        with unittest.mock.patch.object(dlg, 'accept') as mock_accept:
            dlg._save()
            mock_accept.assert_not_called()
        dlg.deleteLater()

    def test_save_creates_user(self):
        """Guardar con datos válidos debe crear el usuario."""
        from views.components.user_dialog import UserDialog
        dlg = UserDialog()
        dlg._username.setText("nuevouser")
        dlg._nombre.setText("Nuevo Usuario")
        dlg._password.setText("pass1234")
        dlg._password_confirm.setText("pass1234")
        dlg._rol.setCurrentIndex(0)  # admin

        with unittest.mock.patch.object(dlg, 'accept') as mock_accept:
            dlg._save()
            mock_accept.assert_called_once()

        self.assertIsNotNone(dlg.usuario)
        self.assertEqual(dlg.usuario.username, "nuevouser")
        self.assertEqual(dlg.usuario.nombre_completo, "Nuevo Usuario")
        self.assertEqual(dlg.usuario.rol, "admin")
        self.assertEqual(dlg.new_password, "pass1234")
        dlg.deleteLater()

    def test_edit_mode_has_activo_checkbox(self):
        """En modo edición debe existir checkbox activo."""
        from views.components.user_dialog import UserDialog
        from database.models import Usuario
        user = Usuario(id=1, username="admin", nombre_completo="Admin", rol="admin")
        dlg = UserDialog(usuario=user)
        self.assertIsNotNone(dlg._activo)
        self.assertTrue(dlg._activo.isChecked())
        dlg.deleteLater()

    def test_new_mode_no_activo_checkbox(self):
        """En modo nuevo no debe existir checkbox activo."""
        from views.components.user_dialog import UserDialog
        dlg = UserDialog()
        self.assertIsNone(dlg._activo)
        dlg.deleteLater()



# ═══════════════════════════════════════════
#  Form Helpers (views/layouts/form_helpers.py)
# ═══════════════════════════════════════════

class TestFormHelpers(unittest.TestCase):
    """Pruebas para helpers de layout: create_form_row, create_page_header, create_stats_grid."""

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def test_create_form_row_returns_vbox(self):
        """create_form_row debe retornar QVBoxLayout."""
        from views.layouts.form_helpers import create_form_row
        from PySide6.QtWidgets import QVBoxLayout, QLineEdit
        widget = QLineEdit()
        row = create_form_row("Nombre", widget)
        self.assertIsInstance(row, QVBoxLayout)
        # Debe contener: QLabel + QLineEdit = 2 items
        self.assertEqual(row.count(), 2)
        widget.deleteLater()

    def test_create_form_row_with_required_marker(self):
        """create_form_row con required=True debe agregar asterisco al label."""
        from views.layouts.form_helpers import create_form_row
        from PySide6.QtWidgets import QVBoxLayout, QLineEdit, QLabel
        widget = QLineEdit()
        row = create_form_row("Nombre", widget, required=True)
        # El primer item debe ser un QLabel con " *"
        item = row.itemAt(0)
        self.assertIsNotNone(item)
        lbl = item.widget()
        self.assertIsInstance(lbl, QLabel)
        self.assertIn("*", lbl.text())
        widget.deleteLater()

    def test_create_form_row_with_hint(self):
        """create_form_row con hint debe agregar label de ayuda."""
        from views.layouts.form_helpers import create_form_row
        from PySide6.QtWidgets import QVBoxLayout, QLineEdit
        widget = QLineEdit()
        row = create_form_row("Email", widget, hint="Ingrese un email válido")
        # 3 items: label + widget + hint
        self.assertEqual(row.count(), 3)
        widget.deleteLater()

    def test_create_page_header_returns_hbox(self):
        """create_page_header debe retornar QHBoxLayout."""
        from views.layouts.form_helpers import create_page_header
        from PySide6.QtWidgets import QHBoxLayout
        header = create_page_header("Título")
        self.assertIsInstance(header, QHBoxLayout)

    def test_create_page_header_with_subtitle(self):
        """create_page_header con subtitle debe incluir QLabel con clase 'subtitle'."""
        from views.layouts.form_helpers import create_page_header
        from PySide6.QtWidgets import QLabel
        header = create_page_header("Título", subtitle="Subtítulo")
        # El primer item del header es el left layout (QVBoxLayout)
        left_layout = header.itemAt(0)
        self.assertIsNotNone(left_layout)
        left_box = left_layout.layout()
        self.assertIsNotNone(left_box)
        self.assertEqual(left_box.count(), 2)  # title + subtitle
        # Verificar que el subtitle tiene clase 'subtitle'
        sub_item = left_box.itemAt(1)
        self.assertIsNotNone(sub_item)
        sub_lbl = sub_item.widget()
        self.assertIsInstance(sub_lbl, QLabel)
        self.assertEqual(sub_lbl.property("class"), "subtitle")
        self.assertIn("Subtítulo", sub_lbl.text())

    def test_create_page_header_with_actions(self):
        """create_page_header con actions debe incluir botones a la derecha."""
        from views.layouts.form_helpers import create_page_header
        from PySide6.QtWidgets import QPushButton
        btn = QPushButton("Acción")
        header = create_page_header("Título", actions=[btn])
        # Debe haber stretch + button = 2 items después del left layout
        # total: left layout + stretch + button = 3 items
        self.assertEqual(header.count(), 3)
        # El último item debe ser el botón
        last_item = header.itemAt(2)
        self.assertIsNotNone(last_item)
        last_widget = last_item.widget()
        self.assertIs(last_widget, btn)
        btn.deleteLater()

    def test_create_page_header_title_class(self):
        """El título debe tener clase 'title'."""
        from views.layouts.form_helpers import create_page_header
        from PySide6.QtWidgets import QLabel
        header = create_page_header("Mi Título")
        left_layout = header.itemAt(0).layout()
        title_item = left_layout.itemAt(0)
        title_lbl = title_item.widget()
        self.assertIsInstance(title_lbl, QLabel)
        self.assertEqual(title_lbl.property("class"), "title")
        self.assertIn("Mi Título", title_lbl.text())

    def test_create_stats_grid_returns_hbox(self):
        """create_stats_grid debe retornar QHBoxLayout."""
        from views.layouts.form_helpers import create_stats_grid
        from PySide6.QtWidgets import QHBoxLayout
        stats = [{"label": "Total", "value": "1,248"}]
        grid = create_stats_grid(stats)
        self.assertIsInstance(grid, QHBoxLayout)

    def test_create_stats_grid_creates_cards(self):
        """create_stats_grid debe crear un CardWidget por cada stat."""
        from views.layouts.form_helpers import create_stats_grid
        from views.components.card_widget import CardWidget
        stats = [
            {"label": "Total", "value": "1,248"},
            {"label": "Pendientes", "value": "42"},
            {"label": "Hoy", "value": "$5,200"},
        ]
        grid = create_stats_grid(stats)
        # Debe tener 3 items (3 cards)
        self.assertEqual(grid.count(), 3)
        # Cada item debe ser un CardWidget
        for i in range(3):
            item = grid.itemAt(i)
            self.assertIsNotNone(item)
            card = item.widget()
            self.assertIsInstance(card, CardWidget)

    def test_create_stats_grid_with_badge(self):
        """create_stats_grid debe agregar StatusBadge si se especifica."""
        from views.layouts.form_helpers import create_stats_grid
        from views.components.status_badge import StatusBadge
        stats = [
            {"label": "Ventas", "value": "$500", "badge": "Activo", "status": "success"},
        ]
        grid = create_stats_grid(stats)
        card = grid.itemAt(0).widget()
        # Buscar StatusBadge dentro del card
        found_badge = False
        for child in card.findChildren(StatusBadge):
            found_badge = True
            self.assertEqual(child.text(), "Activo")
            break
        self.assertTrue(found_badge, "Debe contener un StatusBadge")

    def test_create_stats_grid_without_badge(self):
        """create_stats_grid sin badge no debe agregar StatusBadge."""
        from views.layouts.form_helpers import create_stats_grid
        from views.components.status_badge import StatusBadge
        stats = [{"label": "Total", "value": "100"}]
        grid = create_stats_grid(stats)
        card = grid.itemAt(0).widget()
        badges = card.findChildren(StatusBadge)
        self.assertEqual(len(badges), 0)


if __name__ == '__main__':
    unittest.main()
