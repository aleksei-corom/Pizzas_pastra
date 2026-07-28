"""Vista Domicilios — Gestión de repartidores y seguimiento de entregas.

Diseño adaptativo para pantallas pequeñas:
- Tabla izquierda simplificada a 4 columnas (sin "Estado" redundante)
- Panel derecho con QSplitter vertical arrastrable (Entregas Activas / Repartidores)
- QTableWidget reemplazado por filas-tarjeta (DeliveryRowWidget/RepRow) de 48px
  cada una, mostrando toda la info inline con separadores verticales y badges de estado
- QScrollArea independiente para cada sección garantiza scroll accesible
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFrame, QComboBox, QDialog, QScrollArea, QSplitter,
)
from PySide6.QtCore import Qt, Signal

from database.orden_service import OrdenService
from database.repartidor_service import RepartidorService
import config as app_config
from views.components import ModernMessageBox, CardWidget
from views.components.repartidor_dialog import RepartidorDialog
from views.layouts import create_page_header


# ─── Datos de vehículos ───────────────────────────────────────────────────────

VEHICULO_ICONO = {
    "moto": "🏍️",
    "carro": "🚗",
    "bicicleta": "🚲",
    "pie": "🚶",
}

VEHICULO_NOMBRE = {
    "moto": "Moto",
    "carro": "Carro",
    "bicicleta": "Bicicleta",
    "pie": "A Pie",
}

# ─── Estilo compartido para las filas tarjeta ─────────────────────────────────

_ROW_STYLE = """
QFrame#deliveryRow {
    background-color: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 8px;
}
QFrame#deliveryRow:hover {
    background-color: rgba(255, 255, 255, 0.09);
    border-color: rgba(255, 255, 255, 0.15);
}
"""

_SPLITTER_STYLE = """
QSplitter::handle:vertical {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 transparent,
        stop:0.25 rgba(255,255,255,0.10),
        stop:0.50 rgba(255,255,255,0.22),
        stop:0.75 rgba(255,255,255,0.10),
        stop:1 transparent);
    height: 6px;
    border-radius: 3px;
    margin: 2px 24px;
}
QSplitter::handle:vertical:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 transparent,
        stop:0.25 rgba(99,102,241,0.35),
        stop:0.50 rgba(99,102,241,0.60),
        stop:0.75 rgba(99,102,241,0.35),
        stop:1 transparent);
}
QSplitter::handle:vertical:pressed {
    background: rgba(99,102,241,0.70);
}
"""


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _vsep(parent_layout: QHBoxLayout):
    """Inserta un separador vertical decorativo de 1px dentro de un QHBoxLayout."""
    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.VLine)
    sep.setFixedWidth(1)
    sep.setFixedHeight(22)
    sep.setStyleSheet("background: rgba(255,255,255,0.11); border: none;")
    parent_layout.addWidget(sep)


def _clear_layout(layout: QVBoxLayout):
    """Elimina recursivamente todos los widgets de un QVBoxLayout."""
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()


class _EmptyState(QLabel):
    """Etiqueta de estado vacío centrada con padding."""

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "caption")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setContentsMargins(0, 24, 0, 24)
        self.setWordWrap(True)


# ─── Fila de entrega activa ───────────────────────────────────────────────────

class ActiveDeliveryRow(QFrame):
    """Tarjeta compacta de 48px para una entrega actualmente en camino.

    Layout:  [#Orden] │ [🛵 Repartidor] │ [📍 Dirección] [📞 Tel] [Total] [✅]
    """

    completed = Signal(int)  # emite orden_id

    def __init__(self, orden, rep_nombre: str, parent=None):
        super().__init__(parent)
        self.orden = orden
        self.setObjectName("deliveryRow")
        self.setStyleSheet(_ROW_STYLE)
        self.setFixedHeight(48)
        self._build(rep_nombre)

    def _build(self, rep_nombre: str):
        lo = QHBoxLayout(self)
        lo.setContentsMargins(14, 0, 10, 0)
        lo.setSpacing(10)

        # Número de orden (corto: últimos 4 dígitos)
        seq = self.orden.numero.split("-")[-1] if "-" in self.orden.numero else self.orden.numero
        num_lbl = QLabel(f"#{seq}")
        num_lbl.setProperty("class", "bold")
        num_lbl.setFixedWidth(54)
        num_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lo.addWidget(num_lbl)

        _vsep(lo)

        # Repartidor
        rep_lbl = QLabel(f"🛵  {rep_nombre}")
        rep_lbl.setProperty("class", "bold")
        rep_lbl.setFixedWidth(150)
        rep_lbl.setToolTip(rep_nombre)
        lo.addWidget(rep_lbl)

        _vsep(lo)

        # Dirección — toma el espacio disponible
        dir_text = self.orden.direccion or "Sin dirección"
        dir_lbl = QLabel(f"📍 {dir_text}")
        dir_lbl.setProperty("class", "caption")
        dir_lbl.setToolTip(dir_text)
        lo.addWidget(dir_lbl, 1)

        # Teléfono
        tel_lbl = QLabel(f"📞 {self.orden.telefono_contacto or '—'}")
        tel_lbl.setProperty("class", "caption")
        tel_lbl.setFixedWidth(120)
        lo.addWidget(tel_lbl)

        # Total
        total_lbl = QLabel(f"{app_config.CURRENCY_SYMBOL}{self.orden.total:.2f}")
        total_lbl.setProperty("class", "bold")
        total_lbl.setFixedWidth(64)
        total_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lo.addWidget(total_lbl)

        # Botón "Entregado"
        btn = QPushButton("✅ Entregado")
        btn.setFixedHeight(32)
        btn.setFixedWidth(104)
        btn.setProperty("class", "icon-success")
        btn.setToolTip("Marcar esta orden como entregada")
        btn.clicked.connect(lambda: self.completed.emit(self.orden.id))
        lo.addWidget(btn)


# ─── Fila de repartidor ───────────────────────────────────────────────────────

class RepRow(QFrame):
    """Tarjeta compacta de 48px para un repartidor.

    Layout:  [🏍️ Nombre] │ [Vehículo] │ [📞 Tel] [● badge] [✏️] [⛔/✅]
    """

    edit_requested   = Signal(int)   # emite rep_id
    toggle_requested = Signal(int)   # emite rep_id

    def __init__(self, rep, parent=None):
        super().__init__(parent)
        self.rep = rep
        self.setObjectName("deliveryRow")
        self.setStyleSheet(_ROW_STYLE)
        self.setFixedHeight(48)
        self._build()

    def _build(self):
        lo = QHBoxLayout(self)
        lo.setContentsMargins(14, 0, 10, 0)
        lo.setSpacing(10)

        # Nombre con icono de vehículo
        veh_icon = VEHICULO_ICONO.get(self.rep.vehiculo, "❓")
        name_lbl = QLabel(f"{veh_icon}  {self.rep.nombre}")
        name_lbl.setProperty("class", "bold")
        name_lbl.setMinimumWidth(136)
        name_lbl.setToolTip(self.rep.nombre)
        lo.addWidget(name_lbl)

        _vsep(lo)

        # Tipo de vehículo
        veh_lbl = QLabel(VEHICULO_NOMBRE.get(self.rep.vehiculo, self.rep.vehiculo or "—"))
        veh_lbl.setProperty("class", "caption")
        veh_lbl.setFixedWidth(70)
        lo.addWidget(veh_lbl)

        _vsep(lo)

        # Teléfono — expandible
        tel_lbl = QLabel(f"📞 {self.rep.telefono or '—'}")
        tel_lbl.setProperty("class", "caption")
        lo.addWidget(tel_lbl, 1)

        # Badge de estado coloreado
        is_active = bool(self.rep.activo)
        badge = QLabel("● Activo" if is_active else "● Inactivo")
        badge.setFixedWidth(76)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if is_active:
            badge.setStyleSheet(
                "color: #34d399; font-weight: 700; font-size: 11px;"
                "background: rgba(52,211,153,0.12); border-radius: 4px; padding: 3px 6px;"
            )
        else:
            badge.setStyleSheet(
                "color: #f87171; font-weight: 700; font-size: 11px;"
                "background: rgba(248,113,113,0.12); border-radius: 4px; padding: 3px 6px;"
            )
        lo.addWidget(badge)

        # Botón editar
        btn_edit = QPushButton("✏️")
        btn_edit.setFixedSize(30, 30)
        btn_edit.setProperty("class", "icon-warning")
        btn_edit.setToolTip("Editar repartidor")
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(self.rep.id))
        lo.addWidget(btn_edit)

        # Botón activar/desactivar
        btn_toggle = QPushButton("⛔" if is_active else "✅")
        btn_toggle.setFixedSize(30, 30)
        btn_toggle.setProperty("class", "icon-danger" if is_active else "icon-success")
        btn_toggle.setToolTip("Desactivar" if is_active else "Activar")
        btn_toggle.clicked.connect(lambda: self.toggle_requested.emit(self.rep.id))
        lo.addWidget(btn_toggle)


# ─── Vista principal ──────────────────────────────────────────────────────────

class DeliveryView(QWidget):
    """Vista principal del módulo de domicilios."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.orden_svc = OrdenService()
        self.rep_svc   = RepartidorService()
        self._build_ui()
        self.cargar_datos()

    # ── Construcción de UI ────────────────────────────────────────────────────

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Header
        layout.addLayout(create_page_header(
            "🛵  Gestión de Domicilios",
            "Administra repartidores y seguimiento de entregas en tiempo real"
        ))

        # ── Fila de estadísticas ──
        row1 = QHBoxLayout()
        row1.setSpacing(16)
        self._card_pendientes   = self._stat_card("📋", "Pendientes",    "0")
        self._card_activos      = self._stat_card("🛵", "En Delivery",   "0")
        self._card_repartidores = self._stat_card("👤", "Repartidores",  "0")
        self._card_hoy          = self._stat_card("📦", "Entregas Hoy",  "0")
        for card in (self._card_pendientes, self._card_activos,
                     self._card_repartidores, self._card_hoy):
            row1.addWidget(card)
        layout.addLayout(row1)

        # ── Contenido principal: tabla izquierda + panel derecho adaptativo ──
        content = QHBoxLayout()
        content.setSpacing(20)

        content.addWidget(self._build_left_panel(), 2)
        content.addWidget(self._build_right_splitter(), 3)

        layout.addLayout(content, 1)

    def _build_left_panel(self) -> QWidget:
        """Tabla de pedidos listos para asignar (4 cols)."""
        card = CardWidget(title="📋  Pedidos Listos para Asignar")
        card.setMinimumWidth(290)

        self._pendientes_table = QTableWidget(0, 4)
        self._pendientes_table.setHorizontalHeaderLabels(["#Orden", "Cliente", "Total", ""])
        hh = self._pendientes_table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._pendientes_table.setColumnWidth(3, 94)
        self._pendientes_table.verticalHeader().setVisible(False)
        self._pendientes_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._pendientes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._pendientes_table.setAlternatingRowColors(True)
        card.add_widget(self._pendientes_table)
        return card

    def _build_right_splitter(self) -> QSplitter:
        """Panel derecho con QSplitter vertical: Entregas Activas / Repartidores."""
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(8)
        splitter.setStyleSheet(_SPLITTER_STYLE)

        # ── Sección superior: Entregas Activas ──
        active_card = CardWidget(title="🛵  Entregas Activas")
        active_card.setMinimumHeight(130)

        self._activas_scroll = QScrollArea()
        self._activas_scroll.setWidgetResizable(True)
        self._activas_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._activas_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._activas_container = QWidget()
        self._activas_layout = QVBoxLayout(self._activas_container)
        self._activas_layout.setContentsMargins(10, 8, 10, 8)
        self._activas_layout.setSpacing(5)

        self._activas_scroll.setWidget(self._activas_container)
        active_card.add_widget(self._activas_scroll)
        splitter.addWidget(active_card)

        # ── Sección inferior: Repartidores ──
        reps_card = CardWidget(title="👤  Repartidores")
        reps_card.setMinimumHeight(130)

        # Toolbar
        tb = QWidget()
        tb_lo = QHBoxLayout(tb)
        tb_lo.setContentsMargins(0, 0, 0, 0)
        tb_lo.setSpacing(8)
        tb_lo.addStretch()

        self._rep_filtro = QComboBox()
        self._rep_filtro.addItem("Todos",    None)
        self._rep_filtro.addItem("Activos",  True)
        self._rep_filtro.addItem("Inactivos", False)
        self._rep_filtro.currentIndexChanged.connect(self.cargar_datos)
        tb_lo.addWidget(self._rep_filtro)

        btn_nuevo = QPushButton("➕  Nuevo")
        btn_nuevo.setFixedHeight(34)
        btn_nuevo.setProperty("class", "secondary")
        btn_nuevo.clicked.connect(self._nuevo_repartidor)
        tb_lo.addWidget(btn_nuevo)

        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedSize(34, 34)
        btn_refresh.setProperty("class", "ghost")
        btn_refresh.clicked.connect(self.cargar_datos)
        tb_lo.addWidget(btn_refresh)

        reps_card.add_widget_header(tb)

        # Scroll de filas
        self._reps_scroll = QScrollArea()
        self._reps_scroll.setWidgetResizable(True)
        self._reps_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._reps_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._reps_container = QWidget()
        self._reps_layout = QVBoxLayout(self._reps_container)
        self._reps_layout.setContentsMargins(10, 8, 10, 8)
        self._reps_layout.setSpacing(5)

        self._reps_scroll.setWidget(self._reps_container)
        reps_card.add_widget(self._reps_scroll)
        splitter.addWidget(reps_card)

        # Distribución inicial: 40 % para activas, 60 % para repartidores
        splitter.setSizes([240, 340])
        return splitter

    # ── Stat cards ────────────────────────────────────────────────────────────

    def _stat_card(self, icon: str, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")
        lo = QVBoxLayout(card)
        lo.setContentsMargins(16, 12, 16, 12)
        lo.setSpacing(4)

        icon_lbl = QLabel(icon)
        icon_lbl.setProperty("class", "metric-icon")
        lo.addWidget(icon_lbl)

        val_lbl = QLabel(value)
        val_lbl.setObjectName("statValue")
        val_lbl.setProperty("class", "title")
        lo.addWidget(val_lbl)

        title_lbl = QLabel(title)
        title_lbl.setProperty("class", "caption")
        lo.addWidget(title_lbl)

        return card

    def _update_stat(self, card: QFrame, value) -> None:
        lbl = card.findChild(QLabel, "statValue")
        if lbl:
            lbl.setText(str(value))

    # ── Carga de datos ────────────────────────────────────────────────────────

    def cargar_datos(self):
        """Recarga todos los datos y refresca los widgets."""
        filtro_activos = self._rep_filtro.currentData() if hasattr(self, "_rep_filtro") else None

        pendientes    = self.orden_svc.get_ordenes_delivery_pendientes()
        activas       = self.orden_svc.get_ordenes_en_delivery()
        entregas_hoy  = self.orden_svc.get_entregas_hoy()
        repartidores  = (
            self.rep_svc.get_repartidores()
            if filtro_activos is None
            else self.rep_svc.get_repartidores(solo_activos=filtro_activos)
        )

        # Stats
        self._update_stat(self._card_pendientes,   len(pendientes))
        self._update_stat(self._card_activos,       len(activas))
        self._update_stat(self._card_repartidores,  len(repartidores))
        self._update_stat(self._card_hoy,           len(entregas_hoy))

        # ─── Tabla de pedidos pendientes (4 cols) ───
        self._pendientes_table.setRowCount(len(pendientes))
        for i, orden in enumerate(pendientes):
            self._pendientes_table.setItem(i, 0, QTableWidgetItem(orden.numero))
            self._pendientes_table.setItem(i, 1, QTableWidgetItem(orden.cliente_nombre or "—"))
            self._pendientes_table.setItem(i, 2,
                QTableWidgetItem(f"{app_config.CURRENCY_SYMBOL}{orden.total:.2f}"))

            btn = QPushButton("🛵 Asignar")
            btn.setFixedHeight(30)
            btn.setProperty("class", "icon-success")
            btn.clicked.connect(
                lambda _, oid=orden.id, num=orden.numero: self._asignar_repartidor(oid, num)
            )
            self._pendientes_table.setCellWidget(i, 3, btn)
            self._pendientes_table.setRowHeight(i, 42)

        # ─── Filas de entregas activas ───
        _clear_layout(self._activas_layout)
        if not activas:
            self._activas_layout.addWidget(
                _EmptyState("📭  No hay entregas activas en este momento")
            )
        else:
            for orden in activas:
                rep = (self.rep_svc.get_repartidor(orden.repartidor_id)
                       if orden.repartidor_id else None)
                row = ActiveDeliveryRow(orden, rep.nombre if rep else "—")
                row.completed.connect(self._completar_entrega)
                self._activas_layout.addWidget(row)
        self._activas_layout.addStretch()

        # ─── Filas de repartidores ───
        _clear_layout(self._reps_layout)
        if not repartidores:
            self._reps_layout.addWidget(
                _EmptyState("👤  Sin repartidores. Usa ➕ Nuevo para agregar uno.")
            )
        else:
            for rep in repartidores:
                row = RepRow(rep)
                row.edit_requested.connect(self._editar_repartidor)
                row.toggle_requested.connect(self._toggle_repartidor)
                self._reps_layout.addWidget(row)
        self._reps_layout.addStretch()

    # ── Acciones ─────────────────────────────────────────────────────────────

    def _asignar_repartidor(self, orden_id: int, orden_num: str):
        """Muestra diálogo para asignar un repartidor a una orden."""
        disponibles = self.rep_svc.get_repartidores_disponibles()
        if not disponibles:
            ModernMessageBox.warning(
                self, "Sin Repartidores Disponibles",
                "No hay repartidores disponibles para asignar.\n\n"
                "Agrega un repartidor nuevo o espera a que alguno termine su entrega."
            )
            return

        # Diálogo de selección
        dlg = QDialog(self)
        dlg.setWindowTitle("Asignar Repartidor")
        dlg.setMinimumWidth(390)
        dlg.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        dlg.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        outer = QFrame(dlg)
        outer.setObjectName("dlgOuter")
        main = QVBoxLayout(dlg)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(outer)

        lo = QVBoxLayout(outer)
        lo.setContentsMargins(24, 20, 24, 20)
        lo.setSpacing(16)

        title = QLabel(f"🛵  Asignar Repartidor — #{orden_num}")
        title.setProperty("class", "title")
        lo.addWidget(title)

        combo = QComboBox()
        combo.setFixedHeight(38)
        for rep in disponibles:
            veh = VEHICULO_ICONO.get(rep.vehiculo, "❓")
            combo.addItem(
                f"{veh}  {rep.nombre}  —  {rep.telefono or 'sin teléfono'}",
                rep.id
            )
        lo.addWidget(combo)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setProperty("class", "divider")
        lo.addWidget(sep)

        btns = QHBoxLayout()
        btns.setSpacing(10)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "secondary")
        btn_cancel.setFixedHeight(38)
        btn_cancel.clicked.connect(dlg.reject)
        btn_ok = QPushButton("✅  Asignar")
        btn_ok.setProperty("class", "success")
        btn_ok.setFixedHeight(38)
        btn_ok.clicked.connect(dlg.accept)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        lo.addLayout(btns)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        rep_id = combo.currentData()
        if self.rep_svc.asignar_repartidor(orden_id, rep_id):
            rep_nombre = combo.currentText().split("—")[0].strip()
            ModernMessageBox.success(
                self, "Repartidor Asignado",
                f"Orden #{orden_num} asignada a {rep_nombre}.\n"
                f"Estado actualizado a: 🛵 En Camino"
            )
            self.cargar_datos()
        else:
            ModernMessageBox.error(
                self, "Error al Asignar",
                "No se pudo asignar el repartidor. Intenta de nuevo."
            )

    def _completar_entrega(self, orden_id: int):
        """Marca una orden como entregada tras confirmación."""
        result = ModernMessageBox.question(
            self, "Confirmar Entrega",
            "¿Marcar esta orden como entregada y completar el ciclo?"
        )
        if result == QDialog.DialogCode.Accepted:
            self.orden_svc.actualizar_estado_orden(orden_id, "delivered")
            ModernMessageBox.success(
                self, "✅ Entrega Completada",
                "La orden ha sido marcada como entregada."
            )
            self.cargar_datos()

    def _nuevo_repartidor(self):
        dlg = RepartidorDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.rep_svc.crear_repartidor(dlg.repartidor)
            ModernMessageBox.success(
                self, "Repartidor Registrado",
                f"{dlg.repartidor.nombre} registrado exitosamente."
            )
            self.cargar_datos()

    def _editar_repartidor(self, rep_id: int):
        rep = self.rep_svc.get_repartidor(rep_id)
        if not rep:
            return
        dlg = RepartidorDialog(self, repartidor=rep)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.rep_svc.actualizar_repartidor(dlg.repartidor)
            self.cargar_datos()

    def _toggle_repartidor(self, rep_id: int):
        self.rep_svc.toggle_repartidor(rep_id)
        self.cargar_datos()
