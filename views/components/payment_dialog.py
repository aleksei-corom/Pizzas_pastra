"""Diálogo de cobro rediseñado con pagos combinados, vista previa de recibo y desglose de vuelto."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDoubleSpinBox, QCheckBox, QFrame, QTextBrowser, QTabWidget,
    QComboBox, QCompleter,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from config import CURRENCY_SYMBOL


# ─── Métodos de pago disponibles ───
PAYMENT_METHODS = [
    ("efectivo", "💵", "Efectivo"),
    ("tarjeta", "💳", "Tarjeta"),
    ("transferencia", "🏦", "Transferencia"),
    ("otro", "🪙", "Otro"),
]

# Denominaciones para desglose de vuelto
DENOMINATIONS = [
    (100, "billete"), (50, "billete"), (20, "billete"),
    (10, "billete"), (5, "billete"), (2, "moneda"),
    (1, "moneda"), (0.50, "moneda"), (0.25, "moneda"),
    (0.10, "moneda"), (0.05, "moneda"), (0.01, "moneda"),
]


class PaymentMethodRow(QFrame):
    """Fila individual para un método de pago con monto."""

    def __init__(self, method_key, icon, label, parent=None):
        super().__init__(parent)
        self.method_key = method_key
        self.setProperty("class", "payment-method-row")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        lbl = QLabel(f"{icon}  {label}")
        lbl.setProperty("class", "bold")
        lbl.setMinimumWidth(140)
        layout.addWidget(lbl)

        self.spin = QDoubleSpinBox()
        self.spin.setPrefix(f"{CURRENCY_SYMBOL} ")
        self.spin.setRange(0.0, 999999.0)
        self.spin.setDecimals(2)
        self.spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.spin.setFixedHeight(38)
        layout.addWidget(self.spin, 1)

        self._balance_lbl = QLabel("")
        self._balance_lbl.setProperty("class", "caption")
        self._balance_lbl.setFixedWidth(100)
        self._balance_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._balance_lbl)

        self.valueChanged = self.spin.valueChanged

    @property
    def value(self):
        return self.spin.value()

    @value.setter
    def value(self, v):
        self.spin.setValue(v)

    def set_balance_text(self, text):
        self._balance_lbl.setText(text)


class ReceiptPreviewDialog(QDialog):
    """Diálogo que muestra una vista previa del recibo antes de imprimir."""

    def __init__(self, orden, items, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vista Previa del Recibo")
        self.setMinimumSize(400, 600)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QFrame(self)
        outer.setObjectName("dlgOuter")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(outer)

        layout = QVBoxLayout(outer)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("🧾  Vista Previa del Recibo")
        title.setProperty("class", "title")
        layout.addWidget(title)

        # Render HTML del recibo
        from utils.printer import format_receipt_html
        html = format_receipt_html(orden, items)

        browser = QTextBrowser()
        browser.setHtml(html)
        browser.setStyleSheet("""
            QTextBrowser {
                background-color: #f8f9fa;
                color: #000000;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                font-family: 'Courier New', monospace;
            }
        """)
        layout.addWidget(browser, 1)

        btn_close = QPushButton("🗙  Cerrar Vista Previa")
        btn_close.setFixedHeight(40)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)


class PaymentDialog(QDialog):
    """Diálogo para procesar pagos (soporta combinación de métodos)."""

    def __init__(self, total, parent=None):
        super().__init__(parent)
        self.total = total
        self.minimum_width = 520
        self.setMinimumWidth(self.minimum_width)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Aumentar duración del tooltip para que alcance a leer info detallada
        self.setStyleSheet("""
            QToolTip {
                background-color: #1e1e2e;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                font-family: 'Segoe UI', sans-serif;
            }
        """)

        # Datos de resultado
        self.imprimir_recibo = True
        self.metodos_pago = []  # [(tipo, monto), ...]
        self._build_ui()

    def _build_ui(self):
        outer = QFrame(self)
        outer.setObjectName("dlgOuter")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(outer)

        layout = QVBoxLayout(outer)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Título
        title = QLabel("💰  Procesar Pago")
        title.setProperty("class", "title")
        layout.addWidget(title)

        # ─── Total a Pagar ───
        total_frame = QFrame()
        total_frame.setProperty("class", "card-light")
        total_inner = QHBoxLayout(total_frame)
        total_inner.setContentsMargins(16, 12, 16, 12)

        lbl_total = QLabel("Total a Pagar:")
        lbl_total.setProperty("class", "subtitle")
        total_inner.addWidget(lbl_total)

        self._val_total = QLabel(f"{CURRENCY_SYMBOL}{self.total:.2f}")
        self._val_total.setProperty("class", "title")
        self._val_total.setObjectName("payment-total-value")
        total_inner.addWidget(self._val_total, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(total_frame)

        # ─── Tabs: Pago Simple | Pago Combinado ───
        # Creamos tabs sin usar QTabWidget (evita problemas de estilo)
        self._tab_buttons = QHBoxLayout()
        self._tab_buttons.setSpacing(4)

        self._btn_tab_simple = QPushButton("💳  Pago Único")
        self._btn_tab_simple.setCheckable(True)
        self._btn_tab_simple.setChecked(True)
        self._btn_tab_simple.setProperty("class", "payment-tab-btn")
        self._btn_tab_simple.clicked.connect(lambda: self._switch_tab(0))
        self._tab_buttons.addWidget(self._btn_tab_simple)

        self._btn_tab_combo = QPushButton("🔀  Pago Combinado")
        self._btn_tab_combo.setCheckable(True)
        self._btn_tab_combo.setProperty("class", "payment-tab-btn")
        self._btn_tab_combo.clicked.connect(lambda: self._switch_tab(1))
        self._tab_buttons.addWidget(self._btn_tab_combo)

        self._tab_buttons.addStretch()
        layout.addLayout(self._tab_buttons)

        # Stack de contenido de tabs
        self._tab_stack = QFrame()
        self._tab_stack_layout = QVBoxLayout(self._tab_stack)
        self._tab_stack_layout.setContentsMargins(0, 8, 0, 0)
        self._tab_stack_layout.setSpacing(0)

        # Tab 1: Pago Simple
        self._tab_simple = QFrame()
        self._tab_simple.setProperty("class", "tab-content")
        ts_layout = QVBoxLayout(self._tab_simple)
        ts_layout.setContentsMargins(0, 0, 0, 0)
        ts_layout.setSpacing(10)

        # Método selector
        self._simple_method_buttons = {}
        ms_layout = QHBoxLayout()
        ms_layout.setSpacing(8)
        for key, icon, label in PAYMENT_METHODS:
            btn = QPushButton(f"{icon} {label}")
            btn.setCheckable(True)
            btn.setProperty("class", "payment-method-btn")
            btn.setFixedHeight(42)
            btn.clicked.connect(lambda checked, k=key: self._select_simple_method(k))
            self._simple_method_buttons[key] = btn
            ms_layout.addWidget(btn)
        ms_layout.addStretch()
        ts_layout.addLayout(ms_layout)

        self._selected_simple_method = "efectivo"
        self._simple_method_buttons["efectivo"].setChecked(True)

        self._simple_monto = QDoubleSpinBox()
        self._simple_monto.setPrefix(f"{CURRENCY_SYMBOL} ")
        self._simple_monto.setRange(0.0, 999999.0)
        self._simple_monto.setDecimals(2)
        self._simple_monto.setValue(self.total)
        self._simple_monto.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self._simple_monto.setFixedHeight(44)
        self._simple_monto.selectAll()
        # Import local para evitar circular import
        from views.layouts import create_form_row
        ts_layout.addLayout(create_form_row("Monto Recibido", self._simple_monto))

        # Vuelto simple
        vuelto_simple = QHBoxLayout()
        lbl_vs = QLabel("Vuelto:")
        lbl_vs.setProperty("class", "subtitle")
        vuelto_simple.addWidget(lbl_vs)
        self._val_vuelto_simple = QLabel(f"{CURRENCY_SYMBOL}0.00")
        self._val_vuelto_simple.setProperty("class", "title")
        self._val_vuelto_simple.setObjectName("payment-vuelto-success")
        vuelto_simple.addWidget(self._val_vuelto_simple, alignment=Qt.AlignmentFlag.AlignRight)
        ts_layout.addLayout(vuelto_simple)

        self._desglose_simple = QLabel("")
        self._desglose_simple.setProperty("class", "caption")
        self._desglose_simple.setWordWrap(True)
        ts_layout.addWidget(self._desglose_simple)

        self._simple_monto.valueChanged.connect(self._recalcular_simple)
        self._tab_stack_layout.addWidget(self._tab_simple)

        # Tab 2: Pago Combinado
        self._tab_combo = QFrame()
        self._tab_combo.setProperty("class", "tab-content")
        self._tab_combo.hide()
        tc_layout = QVBoxLayout(self._tab_combo)
        tc_layout.setContentsMargins(0, 0, 0, 0)
        tc_layout.setSpacing(8)

        # Indicador de progreso
        progress_container = QFrame()
        progress_container.setFixedHeight(12)
        progress_container.setObjectName("progress-bar-bg")
        pc_layout = QHBoxLayout(progress_container)
        pc_layout.setContentsMargins(0, 0, 0, 0)
        self._progress_fill = QFrame()
        self._progress_fill.setObjectName("progress-fill")
        self._progress_fill.setFixedHeight(12)
        pc_layout.addWidget(self._progress_fill)
        tc_layout.addWidget(progress_container)

        self._remaining_lbl = QLabel(f"Faltan {CURRENCY_SYMBOL}{self.total:.2f}")
        self._remaining_lbl.setProperty("class", "caption")
        self._remaining_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tc_layout.addWidget(self._remaining_lbl)

        # Métodos de pago
        self._method_rows = {}
        for key, icon, label in PAYMENT_METHODS:
            row = PaymentMethodRow(key, icon, label)
            row.valueChanged.connect(self._recalcular_combinado)
            self._method_rows[key] = row
            tc_layout.addWidget(row)

        # Total cubierto
        total_cubierto = QHBoxLayout()
        lbl_tc = QLabel("Total Cubierto:")
        lbl_tc.setProperty("class", "bold")
        total_cubierto.addWidget(lbl_tc)
        self._val_cubierto = QLabel(f"{CURRENCY_SYMBOL}0.00")
        self._val_cubierto.setProperty("class", "subtitle")
        total_cubierto.addWidget(self._val_cubierto, alignment=Qt.AlignmentFlag.AlignRight)
        tc_layout.addLayout(total_cubierto)

        btn_split = QPushButton("↔  Dividir en partes iguales")
        btn_split.setProperty("class", "ghost")
        btn_split.setFixedHeight(32)
        btn_split.clicked.connect(self._dividir_igualmente)
        tc_layout.addWidget(btn_split)

        self._tab_stack_layout.addWidget(self._tab_combo)
        layout.addWidget(self._tab_stack, 1)

        # ─── Opciones ───
        opts_frame = QHBoxLayout()
        opts_frame.setSpacing(12)

        self.check_imprimir = QCheckBox("🖨️  Imprimir recibo")
        self.check_imprimir.setChecked(True)
        opts_frame.addWidget(self.check_imprimir)

        # Selector rápido de impresora
        printer_lbl = QLabel("📠")
        printer_lbl.setProperty("class", "caption")
        opts_frame.addWidget(printer_lbl)

        self._printer_combo = QComboBox()
        self._printer_combo.setFixedHeight(32)
        self._printer_combo.setMinimumWidth(220)
        self._printer_combo.setToolTip("Escribe o escanea código de barras para buscar impresora")
        self._printer_combo.setEditable(True)
        self._printer_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        opts_frame.addWidget(self._printer_combo)

        self._btn_search_printer = QPushButton("🔍")
        self._btn_search_printer.setFixedSize(32, 32)
        self._btn_search_printer.setToolTip("Buscar impresora (escanea código de barras o escribe el nombre)")
        self._btn_search_printer.clicked.connect(self._focus_printer_search)
        opts_frame.addWidget(self._btn_search_printer)

        self._btn_refresh_printers = QPushButton("🔄")
        self._btn_refresh_printers.setFixedSize(32, 32)
        self._btn_refresh_printers.setToolTip("Refrescar estado de impresoras")
        self._btn_refresh_printers.clicked.connect(self._load_printers)
        opts_frame.addWidget(self._btn_refresh_printers)

        self.btn_preview = QPushButton("👁️  Vista Previa")
        self.btn_preview.setProperty("class", "ghost")
        self.btn_preview.setFixedHeight(36)
        self.btn_preview.clicked.connect(self._mostrar_vista_previa)
        opts_frame.addWidget(self.btn_preview)
        opts_frame.addStretch()
        layout.addLayout(opts_frame)

        # Separador
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setProperty("class", "divider")
        layout.addWidget(sep)

        # ─── Botones de acción ───
        btns = QHBoxLayout()

        self._vuelto_desglose = QLabel("")
        self._vuelto_desglose.setProperty("class", "caption")
        btns.addWidget(self._vuelto_desglose, 1)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "secondary")
        btn_cancel.setFixedHeight(44)
        btn_cancel.setMinimumWidth(120)
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)

        self.btn_confirm = QPushButton("✅  Confirmar Pago")
        self.btn_confirm.setProperty("class", "success")
        self.btn_confirm.setFixedHeight(44)
        self.btn_confirm.setMinimumWidth(180)
        self.btn_confirm.setEnabled(False)
        self.btn_confirm.clicked.connect(self._confirmar)
        btns.addWidget(self.btn_confirm)

        layout.addLayout(btns)

        self._recalcular_simple()
        self._recalcular_combinado()

        # Datos para preview
        self._orden_preview = None
        self._items_preview = None

        # Cargar impresoras disponibles
        self._load_printers()

    def _switch_tab(self, index):
        self._btn_tab_simple.setChecked(index == 0)
        self._btn_tab_combo.setChecked(index == 1)
        self._tab_simple.setVisible(index == 0)
        self._tab_combo.setVisible(index == 1)

    def set_orden_data(self, orden, items):
        """Guarda referencia a la orden para la vista previa del recibo."""
        self._orden_preview = orden
        self._items_preview = items

    # ─── Pago Simple ───
    def _select_simple_method(self, key):
        self._selected_simple_method = key
        for k, btn in self._simple_method_buttons.items():
            btn.setChecked(k == key)

    def _recalcular_simple(self):
        recibido = self._simple_monto.value()
        vuelto = max(0, recibido - self.total)
        self._val_vuelto_simple.setText(f"{CURRENCY_SYMBOL}{vuelto:.2f}")
        self._val_vuelto_simple.setStyleSheet(
            "color: #34d399;" if recibido >= self.total else "color: #f87171;"
        )
        self.btn_confirm.setEnabled(recibido >= self.total)

        if vuelto > 0:
            self._desglose_simple.setText(
                f"🪙 Desglose: {self._calcular_desglose(vuelto)}"
            )
        else:
            self._desglose_simple.setText("")

    # ─── Pago Combinado ───
    def _recalcular_combinado(self):
        total_asignado = sum(row.value for row in self._method_rows.values())
        restante = self.total - total_asignado

        # Actualizar labels de balance por método
        for key, row in self._method_rows.items():
            if row.value > 0:
                pct = (row.value / max(total_asignado, 0.01)) * 100
                row.set_balance_text(f"{pct:.0f}%")
            else:
                row.set_balance_text("")

        # Actualizar barra de progreso
        pct_cubierto = min(100, (total_asignado / max(self.total, 0.01)) * 100)
        w = self._progress_fill.parent()
        parent_w = w.width() if w else 400
        fill_w = max(0, int(pct_cubierto / 100 * parent_w))
        self._progress_fill.setFixedWidth(fill_w)
        if total_asignado >= self.total:
            color = "#34d399"
        elif pct_cubierto > 50:
            color = "#f59e0b"
        else:
            color = "#f87171"
        self._progress_fill.setStyleSheet(
            f"background-color: {color}; border-radius: 6px;"
        )

        self._val_cubierto.setText(f"{CURRENCY_SYMBOL}{total_asignado:.2f}")

        if restante > 0.005:
            self._remaining_lbl.setText(f"❌  Faltan {CURRENCY_SYMBOL}{restante:.2f}")
            self._remaining_lbl.setStyleSheet("color: #f87171;")
            self.btn_confirm.setEnabled(False)
        else:
            excedente = abs(restante)
            cambio_text = f"  (vuelto: {CURRENCY_SYMBOL}{excedente:.2f})" if excedente > 0.005 else ""
            self._remaining_lbl.setText(f"✅  Cubierto{cambio_text}")
            self._remaining_lbl.setStyleSheet("color: #34d399;")
            self.btn_confirm.setEnabled(True)

    def _dividir_igualmente(self):
        """Distribuye el total entre todos los métodos con valor > 0."""
        activos_con_valor = [row for row in self._method_rows.values() if row.value > 0]
        if not activos_con_valor:
            # Si ninguno tiene valor, usar efectivo solamente
            self._method_rows["efectivo"].value = self.total
            for k, row in self._method_rows.items():
                if k != "efectivo":
                    row.value = 0
            return

        parte = round(self.total / len(activos_con_valor), 2)
        resto = round(self.total - parte * len(activos_con_valor), 2)
        for i, row in enumerate(activos_con_valor):
            row.value = round(parte + (resto if i == 0 else 0), 2)

    # ─── Confirmar ───
    def _load_printers(self):
        """Carga la lista de impresoras disponibles en el combo
        con soporte para búsqueda por texto y escaneo de código de barras.

        Usa la preferencia del usuario en sesión para pre-seleccionar
        la impresora. Si el usuario no tiene preferencia, cae en la
        configuración global de la DB.
        """
        try:
            from utils.printer import get_available_printers
            from database.db_manager import DatabaseManager
            from utils.session import Session

            from utils.printer import check_printer_status

            current_text = self._printer_combo.currentText()
            self._printer_combo.clear()

            # Items del combo con indicador de estado
            # ✅ = conectada, ❌ = desconectada, 🔌 = predeterminada
            items = [("🔌 (Predeterminada)", "")]
            printers = get_available_printers()
            for p in printers:
                online = check_printer_status(p)
                icon = "✅" if online else "❌"
                items.append((f"{icon}  {p}", p))

            for idx, (display_text, data) in enumerate(items):
                self._printer_combo.addItem(display_text, data)
                # Tooltip con información detallada del estado
                if idx == 0:
                    self._printer_combo.setItemData(
                        idx, "🔌 Usar la impresora predeterminada de Windows",
                        Qt.ToolTipRole
                    )
                else:
                    online = "✅" in display_text
                    status_text = "Conectada" if online else "Desconectada"
                    self._printer_combo.setItemData(
                        idx,
                        f"{data}\n"
                        f"Estado: {status_text}\n"
                        f"Haga clic en 🔄 para re-verificar conectividad",
                        Qt.ToolTipRole
                    )

            # ─── QCompleter para búsqueda en tiempo real ───
            display_names = [t for t, d in items[1:]]
            completer = QCompleter(display_names, self)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setMaxVisibleItems(10)
            self._printer_combo.setCompleter(completer)

            # Enter / scanner trigger → buscar coincidencia exacta por nombre
            if self._printer_combo.lineEdit():
                self._printer_combo.lineEdit().returnPressed.connect(self._on_printer_search)

            # Restaurar selección previa o leer de preferencia del usuario
            restored = False
            if current_text:
                for i in range(self._printer_combo.count()):
                    if self._printer_combo.itemText(i) == current_text:
                        self._printer_combo.setCurrentIndex(i)
                        restored = True
                        break

            if not restored:
                try:
                    # 1. Preferencia del usuario en sesión
                    session = Session.get()
                    user_printer = session.get_preference("printer_name")
                    if user_printer:
                        for i in range(self._printer_combo.count()):
                            if self._printer_combo.itemData(i) == user_printer:
                                self._printer_combo.setCurrentIndex(i)
                                restored = True
                                break

                    # 2. Fallback: configuración global de la DB
                    if not restored:
                        db = DatabaseManager()
                        cfg_printer = db.get_config("printer_name")
                        if cfg_printer:
                            for i in range(self._printer_combo.count()):
                                if self._printer_combo.itemData(i) == cfg_printer:
                                    self._printer_combo.setCurrentIndex(i)
                                    break
                except Exception:
                    pass
        except Exception:
            self._printer_combo.clear()
            self._printer_combo.addItem("📠 (No disponible)", "")

    def _focus_printer_search(self):
        """Enfoca el campo de búsqueda de impresora para escritura o escaneo.

        Útil para escáneres de código de barras: al hacer clic en el botón 🔍,
        se limpia el campo y se da foco para recibir el código escaneado.
        """
        if self._printer_combo.lineEdit():
            self._printer_combo.lineEdit().clear()
            self._printer_combo.lineEdit().setFocus()
            self._printer_combo.showPopup()

    def _on_printer_search(self):
        """Busca la impresora escrita o escaneada en el combo.

        Soporta:
        - Escaneo de código de barras (el scanner escribe el código + Enter)
        - Escritura manual del nombre de la impresora + Enter
        - Búsqueda parcial insensible a mayúsculas
        """
        text = self._printer_combo.currentText().strip()
        if not text:
            return

        # Buscar por data (nombre limpio de impresora)
        for i in range(self._printer_combo.count()):
            data = self._printer_combo.itemData(i)
            if data and (data.lower() == text.lower() or data.lower() in text.lower()):
                self._printer_combo.setCurrentIndex(i)
                return

        # Buscar por texto visible (con icono)
        for i in range(self._printer_combo.count()):
            display = self._printer_combo.itemText(i)
            if text.lower() in display.lower():
                self._printer_combo.setCurrentIndex(i)
                return

        # Sin coincidencia: restaurar el texto original del ítem seleccionado
        idx = self._printer_combo.currentIndex()
        if idx >= 0 and self._printer_combo.itemText(idx):
            if self._printer_combo.lineEdit():
                self._printer_combo.lineEdit().setText(self._printer_combo.itemText(idx))

    def _confirmar(self):
        self.imprimir_recibo = self.check_imprimir.isChecked()
        self.printer_name = self._printer_combo.currentData() or None

        # Guardar preferencia del usuario en sesión
        try:
            from utils.session import Session
            session = Session.get()
            session.set_preference("printer_name", self.printer_name or "")
        except Exception:
            pass

        if self._tab_simple.isVisible():
            # Pago simple
            metodo = self._selected_simple_method
            monto = self._simple_monto.value()
            self.metodos_pago = [(metodo, monto)]
        else:
            # Pago combinado
            self.metodos_pago = [
                (key, row.value)
                for key, row in self._method_rows.items()
                if row.value > 0
            ]
        self.accept()

    def _mostrar_vista_previa(self):
        if self._orden_preview and self._items_preview:
            dlg = ReceiptPreviewDialog(self._orden_preview, self._items_preview, self)
            dlg.exec()

    @staticmethod
    def _calcular_desglose(monto):
        """Calcula cómo dar el vuelto en billetes y monedas."""
        partes = []
        restante = round(monto, 2)
        for valor, tipo in DENOMINATIONS:
            if restante >= valor - 0.001:
                cantidad = int(restante / valor)
                restante = round(restante - cantidad * valor, 2)
                if cantidad > 0:
                    icono = "💵" if tipo == "billete" else "🪙"
                    label = "billete" if cantidad == 1 else "billetes" if tipo == "billete" else "moneda" if cantidad == 1 else "monedas"
                    partes.append(f"{icono} {cantidad} {label} de {CURRENCY_SYMBOL}{valor:.2f}")
                if restante <= 0:
                    break
        return " ".join(partes) if partes else "Vuelto exacto"

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._tab_combo and self._tab_combo.isVisible():
            self._recalcular_combinado()

    def showEvent(self, event):
        super().showEvent(event)
        self._simple_monto.selectAll()
        self._simple_monto.setFocus()
        QTimer.singleShot(50, self._recalcular_combinado)

    # ─── Propiedades de resultado (compatibilidad) ───
    @property
    def metodo_pago(self):
        if self.metodos_pago:
            return self.metodos_pago[0][0]
        return "efectivo"

    @property
    def monto_recibido(self):
        return sum(m for _, m in self.metodos_pago)

    @property
    def val_vuelto(self):
        return self._val_vuelto_simple
