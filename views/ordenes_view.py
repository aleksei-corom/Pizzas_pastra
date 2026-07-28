"""Vista Órdenes — Historial y gestión de órdenes."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QDateEdit, QDialog, QFrame,
)
from PySide6.QtCore import Qt, QDate, QTimer

from database.orden_service import OrdenService
import config as app_config
from views.components import ModernMessageBox, SearchBar
from views.layouts import create_page_header


class OrderDetailDialog(QDialog):
    """Diálogo de detalle de una orden."""

    def __init__(self, orden, items, parent=None):
        super().__init__(parent)
        self.orden = orden
        self.items = items
        self.setMinimumWidth(500)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QFrame(self)
        outer.setObjectName("dlgOuter")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(outer)

        layout = QVBoxLayout(outer)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel(f"📦  Orden #{orden.numero}")
        title.setProperty("class", "title")
        layout.addWidget(title)

        # Info
        info_grid = QHBoxLayout()
        tipo_text = app_config.ORDER_TYPES.get(orden.tipo, orden.tipo)
        estado_text = app_config.ORDER_STATUS.get(orden.estado, orden.estado)
        for lbl, val in [("Tipo", tipo_text), ("Estado", estado_text), ("Fecha", orden.fecha_creacion[:16])]:
            col = QVBoxLayout()
            col.setSpacing(4)
            l = QLabel(lbl)
            l.setProperty("class", "section")
            col.addWidget(l)
            v = QLabel(str(val))
            v.setProperty("class", "bold")
            col.addWidget(v)
            info_grid.addLayout(col)
        info_grid.addStretch()
        layout.addLayout(info_grid)

        # Items
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setProperty("class", "divider")
        layout.addWidget(sep)

        for item in items:
            row = QHBoxLayout()
            name = QLabel(f"{item.producto_nombre}  x{item.cantidad}")
            row.addWidget(name, 1)
            price = QLabel(f"{app_config.CURRENCY_SYMBOL}{item.subtotal:.2f}")
            price.setProperty("class", "badge-info")
            row.addWidget(price)
            layout.addLayout(row)

        # Totales
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setProperty("class", "divider")
        layout.addWidget(sep2)

        for lbl, val in [("Subtotal", orden.subtotal), ("Impuesto", orden.impuesto)]:
            row = QHBoxLayout()
            l = QLabel(lbl)
            l.setProperty("class", "caption")
            row.addWidget(l, 1)
            v = QLabel(f"{app_config.CURRENCY_SYMBOL}{val:.2f}")
            row.addWidget(v)
            layout.addLayout(row)

        total_row = QHBoxLayout()
        t_lbl = QLabel("TOTAL")
        t_lbl.setProperty("class", "section")
        total_row.addWidget(t_lbl, 1)
        t_val = QLabel(f"{app_config.CURRENCY_SYMBOL}{orden.total:.2f}")
        t_val.setProperty("class", "badge-info")
        total_row.addWidget(t_val)
        layout.addLayout(total_row)

        # Botones inferiores
        btns_layout = QHBoxLayout()
        
        btn_print = QPushButton("🖨️ Imprimir")
        btn_print.setProperty("class", "secondary")
        btn_print.setFixedHeight(38)
        btn_print.clicked.connect(self._imprimir)
        btns_layout.addWidget(btn_print)

        btns_layout.addStretch()

        btn_close = QPushButton("Cerrar")
        btn_close.setProperty("class", "primary")
        btn_close.setFixedHeight(38)
        btn_close.clicked.connect(self.accept)
        btns_layout.addWidget(btn_close)
        
        layout.addLayout(btns_layout)

    def _imprimir(self):
        from utils.printer import print_receipt
        from views.components.modern_messagebox import ModernMessageBox
        success, msg = print_receipt(self.orden, self.items)
        if success:
            ModernMessageBox.success(self, "Impresión", msg)
        else:
            ModernMessageBox.error(self, "Error de Impresión", msg)


class OrdenesView(QWidget):
    """Vista de historial de órdenes con filtros y gestión de estado."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.orden_svc = OrdenService()
        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Header
        btn_refresh = QPushButton("🔄  Actualizar")
        btn_refresh.setFixedHeight(40)
        btn_refresh.setProperty("class", "secondary")
        btn_refresh.clicked.connect(self.cargar_datos)
        layout.addLayout(create_page_header(
            "📦  Historial de Órdenes",
            "Visualiza y gestiona todas las órdenes",
            actions=[btn_refresh]
        ))

        # Filtros
        filters = QHBoxLayout()
        filters.setSpacing(12)

        self._date_filter = QDateEdit()
        self._date_filter.setDate(QDate.currentDate())
        self._date_filter.setCalendarPopup(True)
        self._date_filter.setFixedWidth(160)
        filters.addWidget(QLabel("Fecha:"))
        filters.addWidget(self._date_filter)

        self._filter_timer = QTimer()
        self._filter_timer.setSingleShot(True)
        self._filter_timer.setInterval(300)
        self._filter_timer.timeout.connect(self.cargar_datos)
        self._date_filter.dateChanged.connect(self._filter_timer.start)

        self._status_filter = QComboBox()
        self._status_filter.addItem("Todos los estados", None)
        for key, val in app_config.ORDER_STATUS.items():
            self._status_filter.addItem(val, key)
        self._status_filter.setFixedWidth(200)
        self._status_filter.currentIndexChanged.connect(self.cargar_datos)
        filters.addWidget(self._status_filter)
        filters.addStretch()
        layout.addLayout(filters)

        # Tabla
        self._table = QTableWidget(0, 7)
        self._table.setHorizontalHeaderLabels([
            "#Orden", "Tipo", "Estado", "Items", "Total", "Hora", "Acciones"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(6, 120)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, 1)

    def cargar_datos(self):
        fecha = self._date_filter.date().toString("yyyy-MM-dd")
        estado = self._status_filter.currentData()
        rows = self.orden_svc.get_ordenes_con_items_count(
            fecha=fecha, estado=estado, limit=100
        )

        self._table.setRowCount(len(rows))
        for i, row_data in enumerate(rows):
            orden = row_data["orden"]
            items_count = row_data["items_count"]

            self._table.setItem(i, 0, QTableWidgetItem(orden.numero))

            tipo_text = app_config.ORDER_TYPES.get(orden.tipo, orden.tipo)
            self._table.setItem(i, 1, QTableWidgetItem(tipo_text))

            estado_text = app_config.ORDER_STATUS.get(orden.estado, orden.estado)
            self._table.setItem(i, 2, QTableWidgetItem(estado_text))

            self._table.setItem(i, 3, QTableWidgetItem(f"{items_count} items"))

            self._table.setItem(i, 4, QTableWidgetItem(f"{app_config.CURRENCY_SYMBOL}{orden.total:.2f}"))

            hora = orden.fecha_creacion[11:16] if len(orden.fecha_creacion) > 16 else ""
            self._table.setItem(i, 5, QTableWidgetItem(hora))

            # Botones de acción
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(4)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            btn_view = QPushButton("👁️")
            btn_view.setFixedSize(32, 32)
            btn_view.setToolTip("Ver detalle")
            btn_view.setProperty("class", "icon-warning")
            btn_view.clicked.connect(lambda _, o=orden: self._ver_detalle(o))
            actions_layout.addWidget(btn_view)

            # Botón avanzar estado
            next_states = {"pending": "preparing", "preparing": "ready", "ready": "delivered"}
            if orden.estado in next_states:
                next_st = next_states[orden.estado]
                next_icon = {"preparing": "👨‍🍳", "ready": "✅", "delivered": "📦"}.get(next_st, "➡️")
                btn_next = QPushButton(next_icon)
                btn_next.setFixedSize(32, 32)
                btn_next.setToolTip(f"Cambiar a: {app_config.ORDER_STATUS.get(next_st, '')}")
                btn_next.setProperty("class", "icon-success")
                btn_next.clicked.connect(lambda _, oid=orden.id, ns=next_st: self._cambiar_estado(oid, ns))
                actions_layout.addWidget(btn_next)

            self._table.setCellWidget(i, 6, actions)
            self._table.setRowHeight(i, 46)

    def _ver_detalle(self, orden):
        items = self.orden_svc.get_orden_items(orden.id)
        dlg = OrderDetailDialog(orden, items, self)
        dlg.exec()

    def _cambiar_estado(self, orden_id, nuevo_estado):
        self.orden_svc.actualizar_estado_orden(orden_id, nuevo_estado)
        self.cargar_datos()
