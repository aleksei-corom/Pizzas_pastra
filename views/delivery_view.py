"""Vista Domicilios — Gestión de repartidores y seguimiento de entregas."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFrame, QComboBox, QDialog,
)
from PySide6.QtCore import Qt, QTimer

from database.db_manager import DatabaseManager
from database.models import Repartidor
from config import CURRENCY_SYMBOL, ORDER_TYPES, ORDER_STATUS
from views.components import ModernMessageBox, CardWidget
from views.components.repartidor_dialog import RepartidorDialog
from views.layouts import create_page_header


# Iconos por vehículo
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


class DeliveryView(QWidget):
    """Vista principal del módulo de domicilios."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Header
        layout.addLayout(create_page_header(
            "🛵  Gestión de Domicilios",
            "Administra repartidores y seguimiento de entregas"
        ))

        # ─── Fila 1: Stats ───
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        self._card_pendientes = self._stat_card("📋", "Pendientes", "0")
        self._card_activos = self._stat_card("🛵", "En Delivery", "0")
        self._card_repartidores = self._stat_card("👤", "Repartidores", "0")
        self._card_hoy = self._stat_card("📦", "Entregas Hoy", "0")

        row1.addWidget(self._card_pendientes)
        row1.addWidget(self._card_activos)
        row1.addWidget(self._card_repartidores)
        row1.addWidget(self._card_hoy)
        layout.addLayout(row1)

        # ─── Fila 2: Dos paneles lado a lado ───
        row2 = QHBoxLayout()
        row2.setSpacing(20)

        # Panel Izquierdo: Órdenes pendientes de asignar
        left_card = CardWidget(title="📋  Pedidos Listos para Asignar")
        left_card.setMinimumWidth(350)

        self._pendientes_table = QTableWidget(0, 5)
        self._pendientes_table.setHorizontalHeaderLabels(["#Orden", "Cliente", "Total", "Estado", "Asignar"])
        self._pendientes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._pendientes_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._pendientes_table.setColumnWidth(4, 100)
        self._pendientes_table.verticalHeader().setVisible(False)
        self._pendientes_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._pendientes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        left_card.add_widget(self._pendientes_table)
        row2.addWidget(left_card, 1)

        # Panel Derecho: Entregas activas + Repartidores
        right_panel = QVBoxLayout()
        right_panel.setSpacing(16)

        # Sección entregas activas
        active_card = CardWidget(title="🛵  Entregas Activas")

        self._activas_table = QTableWidget(0, 5)
        self._activas_table.setHorizontalHeaderLabels(["#Orden", "Repartidor", "Dirección", "Teléfono", "Completar"])
        self._activas_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._activas_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._activas_table.setColumnWidth(4, 100)
        self._activas_table.verticalHeader().setVisible(False)
        self._activas_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._activas_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        active_card.add_widget(self._activas_table)
        right_panel.addWidget(active_card, 1)

        # Sección repartidores
        reps_card = CardWidget(title="👤  Repartidores")

        reps_header_w = QWidget()
        reps_header = QHBoxLayout(reps_header_w)
        reps_header.setContentsMargins(0, 0, 0, 0)
        reps_header.setSpacing(8)
        reps_header.addStretch()

        self._rep_filtro = QComboBox()
        self._rep_filtro.addItem("Todos", None)
        self._rep_filtro.addItem("Activos", True)
        self._rep_filtro.addItem("Inactivos", False)
        self._rep_filtro.currentIndexChanged.connect(self.cargar_datos)
        reps_header.addWidget(self._rep_filtro)

        btn_nuevo_rep = QPushButton("➕  Nuevo")
        btn_nuevo_rep.setFixedHeight(34)
        btn_nuevo_rep.setProperty("class", "secondary")
        btn_nuevo_rep.clicked.connect(self._nuevo_repartidor)

        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedSize(34, 34)
        btn_refresh.setProperty("class", "ghost")
        btn_refresh.clicked.connect(self.cargar_datos)

        reps_header.addWidget(btn_nuevo_rep)
        reps_header.addWidget(btn_refresh)
        reps_card.add_widget_header(reps_header_w)

        self._reps_table = QTableWidget(0, 5)
        self._reps_table.setHorizontalHeaderLabels(["Nombre", "Teléfono", "Vehículo", "Estado", "Acciones"])
        self._reps_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._reps_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._reps_table.setColumnWidth(4, 140)
        self._reps_table.verticalHeader().setVisible(False)
        self._reps_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._reps_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        reps_card.add_widget(self._reps_table)
        right_panel.addWidget(reps_card, 1)

        row2.addLayout(right_panel, 2)
        layout.addLayout(row2, 1)

    def _stat_card(self, icon, title, value):
        """Crea una tarjeta de estadística."""
        card = QFrame()
        card.setProperty("class", "card")
        lo = QVBoxLayout(card)
        lo.setContentsMargins(16, 12, 16, 12)
        lo.setSpacing(4)
        i = QLabel(icon)
        i.setProperty("class", "metric-icon")
        lo.addWidget(i)
        v = QLabel(value)
        v.setObjectName("statValue")
        v.setProperty("class", "title")
        lo.addWidget(v)
        l = QLabel(title)
        l.setProperty("class", "caption")
        lo.addWidget(l)
        return card

    def _update_stat(self, card, value):
        lbl = card.findChild(QLabel, "statValue")
        if lbl:
            lbl.setText(str(value))

    def cargar_datos(self):
        """Recarga todos los datos de la vista."""
        filtro_activos = self._rep_filtro.currentData() if hasattr(self, '_rep_filtro') else None

        # Stats
        pendientes = self.db.get_ordenes_delivery_pendientes()
        activas = self.db.get_ordenes_en_delivery()
        entregas_hoy = self.db.get_entregas_hoy()

        if filtro_activos is None:
            repartidores = self.db.get_repartidores()
        else:
            repartidores = self.db.get_repartidores(solo_activos=filtro_activos)

        self._update_stat(self._card_pendientes, str(len(pendientes)))
        self._update_stat(self._card_activos, str(len(activas)))
        self._update_stat(self._card_repartidores, str(len(repartidores)))
        self._update_stat(self._card_hoy, str(len(entregas_hoy)))

        # ─── Tabla de pendientes ───
        self._pendientes_table.setRowCount(len(pendientes))
        for i, orden in enumerate(pendientes):
            self._pendientes_table.setItem(i, 0, QTableWidgetItem(orden.numero))
            self._pendientes_table.setItem(i, 1, QTableWidgetItem(orden.cliente_nombre or "-"))
            self._pendientes_table.setItem(i, 2,
                QTableWidgetItem(f"{CURRENCY_SYMBOL}{orden.total:.2f}"))
            self._pendientes_table.setItem(i, 3,
                QTableWidgetItem(ORDER_STATUS.get(orden.estado, orden.estado)))

            btn_asignar = QPushButton("🛵 Asignar")
            btn_asignar.setFixedHeight(30)
            btn_asignar.setProperty("class", "icon-success")
            btn_asignar.clicked.connect(lambda _, oid=orden.id, num=orden.numero: self._asignar_repartidor(oid, num))
            self._pendientes_table.setCellWidget(i, 4, btn_asignar)
            self._pendientes_table.setRowHeight(i, 42)

        # ─── Tabla de entregas activas ───
        self._activas_table.setRowCount(len(activas))
        for i, orden in enumerate(activas):
            rep = self.db.get_repartidor(orden.repartidor_id) if orden.repartidor_id else None
            rep_nombre = rep.nombre if rep else "—"

            self._activas_table.setItem(i, 0, QTableWidgetItem(orden.numero))
            self._activas_table.setItem(i, 1, QTableWidgetItem(rep_nombre))
            self._activas_table.setItem(i, 2, QTableWidgetItem(orden.direccion or "-"))
            self._activas_table.setItem(i, 3, QTableWidgetItem(orden.telefono_contacto or "-"))

            btn_completar = QPushButton("✅")
            btn_completar.setFixedSize(32, 32)
            btn_completar.setToolTip("Marcar como entregado")
            btn_completar.setProperty("class", "icon-success")
            btn_completar.clicked.connect(lambda _, oid=orden.id: self._completar_entrega(oid))
            self._activas_table.setCellWidget(i, 4, btn_completar)
            self._activas_table.setRowHeight(i, 42)

        # ─── Tabla de repartidores ───
        self._reps_table.setRowCount(len(repartidores))
        for i, rep in enumerate(repartidores):
            self._reps_table.setItem(i, 0, QTableWidgetItem(rep.nombre))
            self._reps_table.setItem(i, 1, QTableWidgetItem(rep.telefono or "-"))
            veh_icono = VEHICULO_ICONO.get(rep.vehiculo, "❓")
            veh_nombre = VEHICULO_NOMBRE.get(rep.vehiculo, rep.vehiculo)
            self._reps_table.setItem(i, 2, QTableWidgetItem(f"{veh_icono} {veh_nombre}"))
            estado_text = "✅ Activo" if rep.activo else "⛔ Inactivo"
            self._reps_table.setItem(i, 3, QTableWidgetItem(estado_text))

            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(6)

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(30, 30)
            btn_edit.setProperty("class", "icon-warning")
            btn_edit.clicked.connect(lambda _, rid=rep.id: self._editar_repartidor(rid))
            actions_layout.addWidget(btn_edit)

            btn_toggle = QPushButton("⛔" if rep.activo else "✅")
            btn_toggle.setFixedSize(30, 30)
            btn_toggle.setToolTip("Desactivar" if rep.activo else "Activar")
            btn_toggle.setProperty("class", "icon-danger" if rep.activo else "icon-success")
            btn_toggle.clicked.connect(lambda _, rid=rep.id: self._toggle_repartidor(rid))
            actions_layout.addWidget(btn_toggle)

            self._reps_table.setCellWidget(i, 4, actions)
            self._reps_table.setRowHeight(i, 42)

    # ─── Acciones ───

    def _asignar_repartidor(self, orden_id, orden_num):
        """Muestra diálogo para asignar un repartidor a una orden."""
        disponibles = self.db.get_repartidores_disponibles()
        if not disponibles:
            ModernMessageBox.warning(
                self, "Sin Repartidores",
                "No hay repartidores disponibles para asignar.\n\n"
                "Registra un repartidor o espera a que alguno termine su entrega."
            )
            return

        # Crear selector simple
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QPushButton, QLabel, QFrame
        dlg = QDialog(self)
        dlg.setWindowTitle("Asignar Repartidor")
        dlg.setMinimumWidth(380)
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
        for rep in disponibles:
            veh = VEHICULO_ICONO.get(rep.vehiculo, "❓")
            combo.addItem(f"{rep.nombre} ({veh} - {rep.telefono or 'sin tel.'})", rep.id)
        lo.addWidget(combo)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "secondary")
        btn_cancel.clicked.connect(dlg.reject)
        btn_ok = QPushButton("✅ Asignar")
        btn_ok.setProperty("class", "success")
        btn_ok.clicked.connect(dlg.accept)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        lo.addLayout(btns)

        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        rep_id = combo.currentData()
        success = self.db.asignar_repartidor(orden_id, rep_id)
        if success:
            rep_nombre = combo.currentText().split(" (")[0]
            ModernMessageBox.success(
                self, "Repartidor Asignado",
                f"Orden #{orden_num} asignada a {rep_nombre}.\n"
                f"Estado actualizado a: En Delivery 🛵"
            )
            self.cargar_datos()
        else:
            ModernMessageBox.error(
                self, "Error",
                "No se pudo asignar el repartidor. Intenta de nuevo."
            )

    def _completar_entrega(self, orden_id):
        """Marca una orden como entregada."""
        result = ModernMessageBox.question(
            self, "Confirmar Entrega",
            "¿Marcar esta orden como entregada?"
        )
        if result == QDialog.DialogCode.Accepted:
            self.db.actualizar_estado_orden(orden_id, "delivered")
            ModernMessageBox.success(self, "Entrega Completada", "La orden ha sido marcada como entregada.")
            self.cargar_datos()

    def _nuevo_repartidor(self):
        dlg = RepartidorDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.db.crear_repartidor(dlg.repartidor)
            ModernMessageBox.success(
                self, "Repartidor Creado",
                f"{dlg.repartidor.nombre} registrado exitosamente."
            )
            self.cargar_datos()

    def _editar_repartidor(self, rep_id):
        rep = self.db.get_repartidor(rep_id)
        if not rep:
            return
        dlg = RepartidorDialog(self, repartidor=rep)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.db.actualizar_repartidor(dlg.repartidor)
            self.cargar_datos()

    def _toggle_repartidor(self, rep_id):
        self.db.toggle_repartidor(rep_id)
        self.cargar_datos()
