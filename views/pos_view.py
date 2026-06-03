"""Vista Punto de Venta — Pantalla principal para tomar pedidos."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QGridLayout,
)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QShortcut, QKeySequence

from database.db_manager import DatabaseManager
from database.models import Orden, OrdenItem
from config import CURRENCY_SYMBOL
from views.components import ProductCard, OrderPanel, SearchBar, ModernMessageBox
from views.components.combo_card import ComboCard
from views.layouts import create_page_header


class POSView(QWidget):
    """Vista de punto de venta con grid de productos, panel de orden y atajos de teclado."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self._current_category = None
        self._cat_buttons = {}
        self._product_cards = []
        self._build_ui()
        self._setup_shortcuts()
        self.cargar_datos()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ─── Panel Izquierdo: Productos ───
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(24, 20, 16, 20)
        left_layout.setSpacing(16)

        # Header
        left_layout.addLayout(create_page_header("🛒  Punto de Venta"))

        # Barra de búsqueda
        self._search = SearchBar("Buscar producto...")
        self._search.textChanged.connect(self._on_search)
        left_layout.addWidget(self._search)

        # Categorías
        self._cat_scroll = QScrollArea()
        self._cat_scroll.setWidgetResizable(True)
        self._cat_scroll.setFixedHeight(52)
        self._cat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._cat_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._cat_scroll.setObjectName("category-scroll-area")

        self._cat_container = QWidget()
        self._cat_layout = QHBoxLayout(self._cat_container)
        self._cat_layout.setContentsMargins(0, 0, 0, 0)
        self._cat_layout.setSpacing(8)
        self._cat_layout.addStretch()
        self._cat_scroll.setWidget(self._cat_container)
        left_layout.addWidget(self._cat_scroll)

        # Grid de productos (scrollable)
        products_scroll = QScrollArea()
        products_scroll.setWidgetResizable(True)
        products_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        products_scroll.setObjectName("product-scroll-area")

        self._products_grid_widget = QWidget()
        self._products_grid = QGridLayout(self._products_grid_widget)
        self._products_grid.setContentsMargins(0, 0, 0, 0)
        self._products_grid.setSpacing(12)
        products_scroll.setWidget(self._products_grid_widget)
        left_layout.addWidget(products_scroll, 1)

        main_layout.addWidget(left_panel, 1)

        # ─── Panel Derecho: Orden ───
        self._order_panel = OrderPanel()
        self._order_panel.order_confirmed.connect(self._on_order_confirmed)
        main_layout.addWidget(self._order_panel)

    def _setup_shortcuts(self):
        """Configura todos los atajos de teclado del POS."""

        # Ctrl+Enter → Cobrar (confirmar orden)
        self._sc_confirm = QShortcut(QKeySequence("Ctrl+Return"), self)
        self._sc_confirm.activated.connect(self._shortcut_confirm)

        # Ctrl+N → Nueva orden (limpiar)
        self._sc_new = QShortcut(QKeySequence("Ctrl+N"), self)
        self._sc_new.activated.connect(self._shortcut_new_order)

        # Ctrl+F → Buscar (focus en search)
        self._sc_focus_search = QShortcut(QKeySequence("Ctrl+F"), self)
        self._sc_focus_search.activated.connect(self._shortcut_focus_search)

        # Escape → Limpiar búsqueda y volver a todas las categorías
        self._sc_escape = QShortcut(QKeySequence("Escape"), self)
        self._sc_escape.activated.connect(self._shortcut_escape)

        # F1 a F8 → Categorías (se asignan dinámicamente en _load_categories)
        self._category_shortcuts = {}
        for i in range(8):
            key = QKeySequence(f"F{i+1}")
            sc = QShortcut(key, self)
            idx = i
            sc.activated.connect(lambda checked=False, i=idx: self._shortcut_category(i))
            self._category_shortcuts[i] = sc

        # Ctrl+Q → Atajo rápido: agregar producto más frecuente
        self._sc_quick_add = QShortcut(QKeySequence("Ctrl+Q"), self)
        self._sc_quick_add.activated.connect(self._shortcut_quick_add)

    def _shortcut_confirm(self):
        """Ctrl+Enter: Activa el botón de cobrar si hay items."""
        if self._order_panel._btn_confirm.isEnabled():
            self._order_panel._confirm_order()

    def _shortcut_new_order(self):
        """Ctrl+N: Limpia la orden actual."""
        if len(self._order_panel.items) > 0:
            self._order_panel.clear_order()
            self._order_panel.show_toast("🧹  Orden limpiada", "info")

    def _shortcut_focus_search(self):
        """Ctrl+F: Enfoca la barra de búsqueda."""
        self._search.setFocus()
        self._search.selectAll()

    def _shortcut_escape(self):
        """Escape: Limpia búsqueda o deselecciona categoría."""
        if self._search.hasFocus() and self._search.text():
            self._search.clear()
        elif self._current_category is not None:
            self._filter_category(None)

    def _shortcut_category(self, index):
        """F1-F8: Selecciona la categoría en ese índice."""
        cat_ids = list(self._cat_buttons.keys())
        if 0 <= index < len(cat_ids):
            cat_id = cat_ids[index]
            if cat_id in self._cat_buttons:
                self._cat_buttons[cat_id].click()

    _COMBO_KEY = "__combos__"

    def _shortcut_quick_add(self):
        """Ctrl+Q: Agrega el primer producto visible al carrito."""
        if self._product_cards:
            card = self._product_cards[0]
            if hasattr(card, 'combo'):
                self._add_combo_to_order(card.combo)
            elif hasattr(card, 'producto'):
                self._add_to_order(card.producto)

    def cargar_datos(self):
        """Carga categorías y productos."""
        self._load_categories()
        self._load_products()

    def _load_categories(self):
        """Carga las categorías como botones de filtro, incluyendo Combos."""
        while self._cat_layout.count() > 1:
            child = self._cat_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._cat_buttons = {}

        btn_all = QPushButton("🏪 Todos")
        btn_all.setCheckable(True)
        btn_all.setChecked(True)
        btn_all.setProperty("class", "category-button")
        btn_all.clicked.connect(lambda: self._filter_category(None))
        self._cat_layout.insertWidget(0, btn_all)
        self._cat_buttons[None] = btn_all

        categorias = self.db.get_categorias()
        for i, cat in enumerate(categorias):
            btn = QPushButton(f"{cat.icono} {cat.nombre}")
            btn.setCheckable(True)
            btn.setProperty("class", "category-button")
            btn.clicked.connect(lambda checked, cid=cat.id: self._filter_category(cid))
            self._cat_layout.insertWidget(i + 1, btn)
            self._cat_buttons[cat.id] = btn

        # Botón de Combos (al final)
        btn_combos = QPushButton("🎉 Combos")
        btn_combos.setCheckable(True)
        btn_combos.setProperty("class", "category-button")
        btn_combos.clicked.connect(lambda: self._filter_category(self._COMBO_KEY))
        idx = len(categorias) + 1
        self._cat_layout.insertWidget(idx, btn_combos)
        self._cat_buttons[self._COMBO_KEY] = btn_combos

    def _filter_category(self, cat_id):
        """Filtra productos por categoría o muestra combos."""
        self._current_category = cat_id
        for cid, btn in self._cat_buttons.items():
            btn.setChecked(cid == cat_id)

        if cat_id == self._COMBO_KEY:
            self._load_combos()
        else:
            self._load_products()

    def _on_search(self, text):
        """Busca productos por texto."""
        if self._current_category == self._COMBO_KEY:
            # En modo combos, filtrar combos
            if text.strip():
                combos = self.db.get_combos(solo_activos=True)
                combos = [c for c in combos if text.lower() in c.nombre.lower()]
                self._display_combos(combos)
            else:
                self._load_combos()
            return

        if text.strip():
            productos = self.db.buscar_productos(text.strip())
        else:
            productos = self.db.get_productos(
                categoria_id=self._current_category,
                solo_disponibles=True
            )
        self._display_products(productos)

    def _load_products(self):
        """Carga productos de la categoría seleccionada."""
        productos = self.db.get_productos(
            categoria_id=self._current_category,
            solo_disponibles=True
        )
        self._display_products(productos)

    def _load_combos(self):
        """Carga combos activos y los muestra en el grid."""
        combos = self.db.get_combos(solo_activos=True)
        self._display_combos(combos)

    def _display_combos(self, combos: list):
        """Muestra combos en el grid."""
        while self._products_grid.count():
            child = self._products_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._product_cards = []

        if not combos:
            empty = QLabel("No hay combos disponibles")
            empty.setProperty("class", "caption")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._products_grid.addWidget(empty, 0, 0)
            return

        for i, combo in enumerate(combos):
            card = ComboCard(combo)
            card.clicked.connect(lambda c=combo: self._add_combo_to_order(c))
            self._product_cards.append(card)

            card_width = 160
            spacing = 12
            available = self._products_grid_widget.width()
            cols = max(1, (available + spacing) // (card_width + spacing))
            row = i // cols
            col = i % cols
            self._products_grid.addWidget(card, row, col)

    def _display_products(self, productos):
        """Muestra productos en el grid."""
        while self._products_grid.count():
            child = self._products_grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self._product_cards = []

        if not productos:
            empty = QLabel("No hay productos disponibles")
            empty.setProperty("class", "caption")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._products_grid.addWidget(empty, 0, 0)
            return

        for i, prod in enumerate(productos):
            card = ProductCard(prod)
            card.clicked.connect(lambda p=prod: self._add_to_order(p))
            self._product_cards.append(card)
            # Lógica de recolocación del grid
            card_width = 160
            spacing = 12
            available = self._products_grid_widget.width()
            cols = max(1, (available + spacing) // (card_width + spacing))
            row = i // cols
            col = i % cols
            self._products_grid.addWidget(card, row, col)

    def _add_combo_to_order(self, combo):
        """Agrega todos los items de un combo a la orden actual."""
        for item in combo.items:
            orden_item = OrdenItem(
                producto_id=item.producto_id,
                producto_nombre=f"🎉 {combo.nombre} • {item.producto_nombre}",
                cantidad=item.cantidad,
                precio_unitario=item.precio_individual,
            )
            self._order_panel.add_item(orden_item)
        self._order_panel.show_toast(f"🎉 Combo {combo.nombre} agregado ({CURRENCY_SYMBOL}{combo.precio_total:.2f})", "success")

    def _add_to_order(self, producto):
        """Agrega un producto a la orden actual, mostrando selector de variantes si aplica."""
        if producto.tiene_variantes:
            from views.components.variant_dialog import VariantDialog
            dlg = VariantDialog(producto, self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return
            precio = dlg.precio_final
            desc = dlg.descripcion_item
            nombre = f"{producto.nombre} ({desc})" if desc else producto.nombre
        else:
            precio = producto.precio
            nombre = producto.nombre

        item = OrdenItem(
            producto_id=producto.id,
            producto_nombre=nombre,
            cantidad=1,
            precio_unitario=precio,
        )
        self._order_panel.add_item(item)

    def _on_order_confirmed(self, order_data):
        """Procesa la confirmación de una orden."""
        try:
            from PySide6.QtWidgets import QDialog
            from views.components.payment_dialog import PaymentDialog

            dlg = PaymentDialog(order_data['total'], self)

            # Pasar datos de orden para vista previa de recibo
            orden_temp = Orden(
                tipo=order_data['tipo'],
                items=order_data['items'],
                notas=order_data.get('notas', ''),
            )
            dlg.set_orden_data(orden_temp, order_data['items'])

            if dlg.exec() != QDialog.DialogCode.Accepted:
                return  # El usuario canceló el pago

            imprimir = dlg.imprimir_recibo
            metodos_pago = dlg.metodos_pago

            orden = Orden(
                tipo=order_data['tipo'],
                items=order_data['items'],
                notas=order_data.get('notas', ''),
                direccion=order_data.get('direccion', ''),
                telefono_contacto=order_data.get('telefono_contacto', ''),
                costo_delivery=order_data.get('costo_delivery', 0.0),
                tiempo_estimado=order_data.get('tiempo_estimado', 0),
            )
            orden_guardada = self.db.crear_orden(orden)

            # Construir mensaje con detalle de métodos de pago
            if len(metodos_pago) == 1:
                metodo, monto = metodos_pago[0]
                pago_str = f"Método: {metodo.capitalize()}"
            else:
                pago_str = "Pago combinado: " + ", ".join(
                    f"{m.capitalize()}: {CURRENCY_SYMBOL}{v:.2f}"
                    for m, v in metodos_pago
                )

            msg = f"Orden #{orden_guardada.numero}\nTotal: {CURRENCY_SYMBOL}{orden_guardada.total:.2f}\n"
            msg += f"{pago_str}\n"
            msg += f"Cambio: {dlg.val_vuelto.text()}\n\nLa orden ha sido enviada a preparación."

            if imprimir:
                from utils.printer import print_receipt
                success, p_msg = print_receipt(
                    orden_guardada,
                    orden_guardada.items,
                    printer_name=dlg.printer_name,
                )
                if success:
                    msg += f"\n\n🖨️ {p_msg}"
                else:
                    msg += f"\n\n⚠️ Falló impresión: {p_msg}"

            ModernMessageBox.success(
                self,
                "¡Orden Registrada! 🎉",
                msg
            )
            self._order_panel.clear_order()

        except Exception as e:
            ModernMessageBox.error(
                self,
                "Error al Registrar Orden",
                f"No se pudo guardar la orden: {str(e)}"
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Debounce: recargar grid solo al dejar de redimensionar
        if not hasattr(self, '_resize_timer'):
            self._resize_timer = QTimer(self)
            self._resize_timer.setSingleShot(True)
            self._resize_timer.setInterval(200)
            self._resize_timer.timeout.connect(self._load_products)
        self._resize_timer.start()
