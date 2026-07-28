"""Panel lateral de orden actual para el POS."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QComboBox, QTextEdit, QLineEdit,
    QDoubleSpinBox,
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
try:
    from PySide6.QtWidgets import QGraphicsOpacityEffect
except ImportError:
    from PySide6.QtGui import QGraphicsOpacityEffect

import config as app_config
from config import ORDER_TYPES
from .icon_button import IconButton


class ToastWidget(QLabel):
    """Notificación toast temporal con auto-fadeout."""

    TYPES = {
        "success": {"bg": "#065f46", "border": "#34d399", "icon": "✅"},
        "info": {"bg": "#1e3a5f", "border": "#3b82f6", "icon": "ℹ️"},
        "warning": {"bg": "#5c4a1a", "border": "#f59e0b", "icon": "⚠️"},
    }

    def __init__(self, parent, message, msg_type="success", duration=2200):
        super().__init__(parent)
        cfg = self.TYPES.get(msg_type, self.TYPES["success"])
        self.setText(f" {cfg['icon']}  {message}")
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {cfg['bg']};
                color: #ffffff;
                border: 1px solid {cfg['border']};
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }}
        """)
        self.adjustSize()
        # Posicionar arriba-centro del panel
        parent_rect = parent.rect()
        x = (parent_rect.width() - self.width()) // 2
        self.move(max(8, x), 12)
        self.setFixedWidth(min(self.width(), parent_rect.width() - 16))

        # Opacidad inicial 0, animar entrada
        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._effect.setOpacity(0.0)
        self.show()

        # Fade in
        self._anim_in = QPropertyAnimation(self._effect, b"opacity")
        self._anim_in.setDuration(180)
        self._anim_in.setStartValue(0.0)
        self._anim_in.setEndValue(1.0)
        self._anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim_in.start()

        # Auto-fade out
        QTimer.singleShot(duration, self._fade_out)

    def _fade_out(self):
        self._anim_out = QPropertyAnimation(self._effect, b"opacity")
        self._anim_out.setDuration(300)
        self._anim_out.setStartValue(1.0)
        self._anim_out.setEndValue(0.0)
        self._anim_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._anim_out.finished.connect(self.deleteLater)
        self._anim_out.start()


class OrderItemWidget(QFrame):
    """Widget para un ítem individual en la orden."""

    quantity_changed = Signal()
    removed = Signal()

    def __init__(self, item, parent=None, animate=False):
        super().__init__(parent)
        self.item = item
        self.setProperty("class", "order-item-card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # Fila 1: nombre + subtotal
        top = QHBoxLayout()
        name = QLabel(item.producto_nombre)
        name.setProperty("class", "caption")
        name.setWordWrap(True)
        top.addWidget(name, 1)

        self._subtotal_lbl = QLabel(f"{app_config.CURRENCY_SYMBOL}{item.subtotal:.2f}")
        self._subtotal_lbl.setProperty("class", "badge-info")
        top.addWidget(self._subtotal_lbl)
        layout.addLayout(top)

        # Si el nombre incluye detalles de variante (contiene paréntesis o •), mostrar precio unitario
        if "(" in item.producto_nombre or "•" in item.producto_nombre:
            detail = QLabel(f"@ {app_config.CURRENCY_SYMBOL}{item.precio_unitario:.2f} c/u")
            detail.setProperty("class", "caption")
            detail.setStyleSheet("font-size: 10px;")
            layout.addWidget(detail)

        # Fila 2: controles de cantidad
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        btn_minus = IconButton("−", size=28)
        btn_minus.clicked.connect(self._decrease)
        bottom.addWidget(btn_minus)

        self._qty_lbl = QLabel(str(item.cantidad))
        self._qty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._qty_lbl.setFixedWidth(32)
        self._qty_lbl.setProperty("class", "title")
        bottom.addWidget(self._qty_lbl)

        btn_plus = IconButton("+", size=28)
        btn_plus.clicked.connect(self._increase)
        bottom.addWidget(btn_plus)

        bottom.addStretch()

        price_each = QLabel(f"{app_config.CURRENCY_SYMBOL}{item.precio_unitario:.2f} c/u")
        price_each.setProperty("class", "caption")
        bottom.addWidget(price_each)

        btn_del = IconButton("🗑", size=28)
        btn_del.setProperty("class", "danger-ghost")
        btn_del.clicked.connect(self.removed.emit)
        bottom.addWidget(btn_del)

        layout.addLayout(bottom)

        # Animación de entrada si es nuevo item
        if animate:
            self._animate_entry()

    def _animate_entry(self):
        """Animación sutil de fade-in + slide al agregar un ítem."""
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        eff.setOpacity(0.0)

        anim = QPropertyAnimation(eff, b"opacity")
        anim.setDuration(250)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._entry_anim = anim

    def _increase(self):
        self.item.cantidad += 1
        self._update_display()
        self.quantity_changed.emit()

    def _decrease(self):
        if self.item.cantidad > 1:
            self.item.cantidad -= 1
            self._update_display()
            self.quantity_changed.emit()
        else:
            self.removed.emit()

    def _update_display(self):
        self._qty_lbl.setText(str(self.item.cantidad))
        self._subtotal_lbl.setText(f"{app_config.CURRENCY_SYMBOL}{self.item.subtotal:.2f}")


class OrderPanel(QFrame):
    """Panel lateral derecho con el resumen de la orden actual."""

    order_confirmed = Signal(object)
    order_cleared = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.setObjectName("orderPanel")
        self.setFixedWidth(340)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("🛒  Orden Actual")
        title.setProperty("class", "section")
        header.addWidget(title)
        header.addStretch()

        # Indicador atajos
        shortcuts_lbl = QLabel("Ctrl+Enter Cobrar • Ctrl+N Nuevo")
        shortcuts_lbl.setProperty("class", "caption")
        shortcuts_lbl.setStyleSheet("font-size: 9px;")
        shortcuts_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        header.addWidget(shortcuts_lbl)

        btn_clear = QPushButton("Limpiar")
        btn_clear.setProperty("class", "ghost")
        btn_clear.clicked.connect(self.clear_order)
        header.addWidget(btn_clear)
        layout.addLayout(header)

        # Tipo de pedido
        self.tipo_combo = QComboBox()
        for key, val in ORDER_TYPES.items():
            self.tipo_combo.addItem(val, key)
        self.tipo_combo.currentIndexChanged.connect(self._on_tipo_changed)
        layout.addWidget(self.tipo_combo)

        # ─── Campos de Delivery (visibles solo si tipo = delivery) ───
        self._delivery_frame = QFrame()
        self._delivery_frame.setProperty("class", "card-light")
        dl_layout = QVBoxLayout(self._delivery_frame)
        dl_layout.setContentsMargins(10, 8, 10, 8)
        dl_layout.setSpacing(6)

        dl_title = QLabel("🛵  Datos de Delivery")
        dl_title.setProperty("class", "section")
        dl_layout.addWidget(dl_title)

        self._dl_direccion = QLineEdit()
        self._dl_direccion.setPlaceholderText("Dirección de entrega *")
        dl_layout.addWidget(self._dl_direccion)

        self._dl_telefono = QLineEdit()
        self._dl_telefono.setPlaceholderText("Teléfono de contacto *")
        dl_layout.addWidget(self._dl_telefono)

        costo_row = QHBoxLayout()
        costo_lbl = QLabel("Costo envío:")
        costo_lbl.setProperty("class", "caption")
        costo_row.addWidget(costo_lbl)
        self._dl_costo = QDoubleSpinBox()
        self._dl_costo.setPrefix(f"{app_config.CURRENCY_SYMBOL} ")
        self._dl_costo.setRange(0.0, 999999.99)
        self._dl_costo.setDecimals(2)
        self._dl_costo.setValue(2.00)
        self._dl_costo.setFixedHeight(32)
        self._dl_costo.valueChanged.connect(self._update_totals)
        costo_row.addWidget(self._dl_costo, 1)
        dl_layout.addLayout(costo_row)

        tiempo_row = QHBoxLayout()
        tiempo_lbl = QLabel("Tiempo est.:")
        tiempo_lbl.setProperty("class", "caption")
        tiempo_row.addWidget(tiempo_lbl)
        self._dl_tiempo = QLabel("30 min")
        self._dl_tiempo.setProperty("class", "bold")
        tiempo_row.addWidget(self._dl_tiempo)
        tiempo_row.addStretch()
        dl_layout.addLayout(tiempo_row)

        self._delivery_frame.setVisible(False)
        layout.addWidget(self._delivery_frame)

        # Notas de la orden
        notas_label = QLabel("Notas:")
        notas_label.setProperty("class", "caption")
        layout.addWidget(notas_label)

        self.notas_text = QTextEdit()
        self.notas_text.setPlaceholderText("Ej: sin cebolla, extra queso...")
        self.notas_text.setMaximumHeight(60)
        layout.addWidget(self.notas_text)

        # Lista de items (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setObjectName("order-items-scroll-area")

        self._items_container = QWidget()
        self._items_layout = QVBoxLayout(self._items_container)
        self._items_layout.setContentsMargins(0, 0, 0, 0)
        self._items_layout.setSpacing(8)
        self._items_layout.addStretch()
        scroll.setWidget(self._items_container)
        layout.addWidget(scroll, 1)

        # Empty state
        self._empty_lbl = QLabel("Agrega productos\npara comenzar 🍕")
        self._empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_lbl.setProperty("class", "subtitle")
        self._items_layout.insertWidget(0, self._empty_lbl)

        # Totales
        totals_frame = QFrame()
        totals_frame.setProperty("class", "card-light")
        totals_layout = QVBoxLayout(totals_frame)
        totals_layout.setContentsMargins(16, 12, 16, 12)
        totals_layout.setSpacing(8)

        self._subtotal_lbl = self._create_total_row(totals_layout, "Subtotal", "$0.00")
        self._tax_lbl = self._create_total_row(totals_layout, f"IVA ({int(app_config.TAX_RATE*100)}%)", "$0.00")

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setObjectName("order-panel-separator")
        totals_layout.addWidget(sep)

        total_row = QHBoxLayout()
        t_label = QLabel("TOTAL")
        t_label.setProperty("class", "section")
        total_row.addWidget(t_label)
        self._total_lbl = QLabel("$0.00")
        self._total_lbl.setObjectName("order-panel-total-value")
        self._total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        total_row.addWidget(self._total_lbl)
        totals_layout.addLayout(total_row)

        layout.addWidget(totals_frame)

        # Botón cobrar
        self._btn_confirm = QPushButton(f"💰  Cobrar  {app_config.CURRENCY_SYMBOL}0.00")
        self._btn_confirm.setFixedHeight(48)
        self._btn_confirm.setProperty("class", "success")
        self._btn_confirm.setEnabled(False)
        self._btn_confirm.clicked.connect(self._confirm_order)
        layout.addWidget(self._btn_confirm)

    def _on_tipo_changed(self, index):
        """Muestra/oculta campos de delivery según el tipo de pedido."""
        es_delivery = self.tipo_combo.itemData(index) == "delivery"
        self._delivery_frame.setVisible(es_delivery)
        self._update_totals()

    def show_toast(self, message, msg_type="success"):
        """Muestra una notificación toast en la parte superior del panel."""
        ToastWidget(self, message, msg_type)

    def _create_total_row(self, parent_layout, label_text, value_text):
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setProperty("class", "caption")
        row.addWidget(lbl)
        val = QLabel(value_text)
        val.setObjectName("order-panel-total-row-value")
        val.setAlignment(Qt.AlignmentFlag.AlignRight)
        row.addWidget(val)
        parent_layout.addLayout(row)
        return val

    def add_item(self, orden_item):
        """Agrega un item a la orden con feedback visual."""
        # Agregar como nuevo ítem solo si no hay otro con mismo producto Y mismo precio
        # (esto permite tener variantes distintas del mismo producto en la misma orden)
        for existing in self.items:
            if (existing.producto_id == orden_item.producto_id and
                    existing.precio_unitario == orden_item.precio_unitario):
                existing.cantidad += 1
                self._rebuild_items_ui()
                self._update_totals()
                self.show_toast(f"+1 {orden_item.producto_nombre}", "info")
                return

        self.items.append(orden_item)
        self._rebuild_items_ui(animate_new=True)
        self._update_totals()
        self.show_toast(f"✓ {orden_item.producto_nombre} agregado", "success")

    def _rebuild_items_ui(self, animate_new=False):
        for i in reversed(range(self._items_layout.count())):
            child = self._items_layout.itemAt(i)
            widget = child.widget()
            if widget and widget is not self._empty_lbl:
                self._items_layout.takeAt(i)
                widget.deleteLater()

        self._empty_lbl.setVisible(len(self.items) == 0)

        for i, item in enumerate(self.items):
            is_new = animate_new and i == len(self.items) - 1
            widget = OrderItemWidget(item, animate=is_new)
            widget.quantity_changed.connect(self._update_totals)
            # Pasar referencia directa al objeto para evitar bugs con índices stale
            widget.removed.connect(lambda checked=False, it=item: self._remove_item_by_ref(it))
            self._items_layout.insertWidget(i + 1, widget)

    def _remove_item_by_ref(self, item):
        """Elimina un ítem usando referencia directa al objeto (evita bugs con índices)."""
        if item in self.items:
            removed_name = item.producto_nombre
            self.items.remove(item)
            self._rebuild_items_ui()
            self._update_totals()
            self.show_toast(f"✕ {removed_name} eliminado", "warning")

    def _remove_item(self, index):
        """Elimina un ítem por índice (mantenido por compatibilidad)."""
        if 0 <= index < len(self.items):
            removed_name = self.items[index].producto_nombre
            self.items.pop(index)
            self._rebuild_items_ui()
            self._update_totals()
            self.show_toast(f"✕ {removed_name} eliminado", "warning")

    def _get_delivery_cost(self) -> float:
        """Retorna el costo de delivery si aplica."""
        if self.tipo_combo.currentData() == "delivery":
            return self._dl_costo.value()
        return 0.0

    def _update_totals(self):
        subtotal = sum(item.subtotal for item in self.items)
        delivery = self._get_delivery_cost()
        tax = round(subtotal * app_config.TAX_RATE, 2)
        total_con_envio = round(subtotal + delivery + tax, 2)

        self._subtotal_lbl.setText(f"{app_config.CURRENCY_SYMBOL}{subtotal:.2f}")
        self._tax_lbl.setText(f"{app_config.CURRENCY_SYMBOL}{tax:.2f}")
        self._total_lbl.setText(f"{app_config.CURRENCY_SYMBOL}{total_con_envio:.2f}")

        if delivery > 0:
            envio_text = f" + {app_config.CURRENCY_SYMBOL}{delivery:.2f} envío"
        else:
            envio_text = ""
        self._btn_confirm.setText(f"💰  Cobrar  {app_config.CURRENCY_SYMBOL}{total_con_envio:.2f}{envio_text}")
        self._btn_confirm.setEnabled(len(self.items) > 0)

    def _confirm_order(self):
        # ─── Validar campos obligatorios de delivery ───
        if self.tipo_combo.currentData() == "delivery":
            if not self._dl_direccion.text().strip():
                self.show_toast("⚠️  Ingresa la dirección de entrega", "warning")
                self._dl_direccion.setFocus()
                return
            if not self._dl_telefono.text().strip():
                self.show_toast("⚠️  Ingresa el teléfono de contacto", "warning")
                self._dl_telefono.setFocus()
                return

        subtotal = sum(item.subtotal for item in self.items)
        delivery = self._get_delivery_cost()
        tax = round(subtotal * app_config.TAX_RATE, 2)
        total = round(subtotal + delivery + tax, 2)

        data = {
            'tipo': self.tipo_combo.currentData(),
            'items': self.items.copy(),
            'subtotal': subtotal,
            'impuesto': tax,
            'total': total,
            'notas': self.notas_text.toPlainText().strip(),
        }

        # Incluir datos de delivery si aplica
        if self.tipo_combo.currentData() == "delivery":
            data['direccion'] = self._dl_direccion.text().strip()
            data['telefono_contacto'] = self._dl_telefono.text().strip()
            data['costo_delivery'] = delivery
            data['tiempo_estimado'] = 30

        self.order_confirmed.emit(data)

    def clear_order(self):
        self.items.clear()
        self._rebuild_items_ui()
        self._update_totals()
        self.notas_text.clear()
        self._dl_direccion.clear()
        self._dl_telefono.clear()
        self._dl_costo.setValue(2.00)
        self.order_cleared.emit()
