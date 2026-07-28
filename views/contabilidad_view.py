"""Vista Contabilidad — Gestión de ingresos y egresos."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFrame, QDialog, QLineEdit, QComboBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt
from datetime import datetime

from database.contabilidad_service import ContabilidadService
from database.models import Transaccion
import config as app_config
from views.layouts import create_page_header
from views.components import ModernMessageBox


class RegistrarEgresoDialog(QDialog):
    """Diálogo para registrar un gasto (egreso)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Egreso")
        self.setMinimumWidth(400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.resultado_transaccion = None

        outer = QFrame(self)
        outer.setObjectName("dlgOuter")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(outer)

        layout = QVBoxLayout(outer)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title = QLabel("💸 Registrar Gasto / Egreso")
        title.setProperty("class", "title")
        layout.addWidget(title)

        # Formulario
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Ej. Compra de queso, Pago de luz...")
        layout.addWidget(QLabel("Descripción:"))
        layout.addWidget(self.desc_input)

        self.monto_input = QDoubleSpinBox()
        self.monto_input.setRange(0.01, 9999999.99)
        self.monto_input.setPrefix(f"{app_config.CURRENCY_SYMBOL} ")
        layout.addWidget(QLabel("Monto:"))
        layout.addWidget(self.monto_input)

        self.cat_input = QComboBox()
        self.cat_input.addItems(["Insumos", "Nómina", "Servicios", "Mantenimiento", "Otros"])
        layout.addWidget(QLabel("Categoría:"))
        layout.addWidget(self.cat_input)

        # Botones
        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "secondary")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("Guardar")
        btn_save.setProperty("class", "primary")
        btn_save.clicked.connect(self._guardar)
        
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _guardar(self):
        desc = self.desc_input.text().strip()
        monto = self.monto_input.value()
        cat = self.cat_input.currentText()

        if not desc:
            ModernMessageBox.error(self, "Error", "La descripción es requerida.")
            return

        self.resultado_transaccion = Transaccion(
            tipo="egreso",
            monto=monto,
            descripcion=desc,
            fecha=datetime.now().isoformat(),
            categoria=cat
        )
        self.accept()


class ResumenTarjeta(QFrame):
    """Tarjeta para mostrar un total (ej. Ingresos)."""
    def __init__(self, titulo, valor, color_clase=""):
        super().__init__()
        self.setProperty("class", "card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setProperty("class", "section")
        
        self.lbl_valor = QLabel(f"{app_config.CURRENCY_SYMBOL}{valor:.2f}")
        self.lbl_valor.setProperty("class", f"title {color_clase}")
        self.lbl_valor.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(lbl_titulo)
        layout.addWidget(self.lbl_valor)
        layout.setAlignment(lbl_titulo, Qt.AlignmentFlag.AlignHCenter)

    def set_valor(self, valor):
        self.lbl_valor.setText(f"{app_config.CURRENCY_SYMBOL}{valor:.2f}")


class ContabilidadView(QWidget):
    """Vista del módulo de contabilidad."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cont_svc = ContabilidadService()
        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Header
        btn_egreso = QPushButton("💸 Registrar Egreso")
        btn_egreso.setFixedHeight(40)
        btn_egreso.setProperty("class", "primary")
        btn_egreso.clicked.connect(self._registrar_egreso)
        
        layout.addLayout(create_page_header(
            "💰  Contabilidad",
            "Gestión de ingresos, gastos y balance de caja",
            actions=[btn_egreso]
        ))

        # Tarjetas de resumen
        resumen_layout = QHBoxLayout()
        resumen_layout.setSpacing(20)
        
        self.card_ingresos = ResumenTarjeta("Total Ingresos", 0.0, "success-text")
        self.card_egresos = ResumenTarjeta("Total Egresos", 0.0, "danger-text")
        self.card_balance = ResumenTarjeta("Balance Neto", 0.0, "info-text")
        
        resumen_layout.addWidget(self.card_ingresos)
        resumen_layout.addWidget(self.card_egresos)
        resumen_layout.addWidget(self.card_balance)
        layout.addLayout(resumen_layout)

        # Título Tabla
        lbl_tabla = QLabel("Últimos Movimientos")
        lbl_tabla.setProperty("class", "section")
        layout.addWidget(lbl_tabla)

        # Tabla
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "Descripción", "Categoría", "Monto"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, 1)

    def cargar_datos(self):
        balance = self.cont_svc.get_balance_contable()
        self.card_ingresos.set_valor(balance["total_ingresos"])
        self.card_egresos.set_valor(balance["total_egresos"])
        self.card_balance.set_valor(balance["balance_neto"])

        # Para darle color al balance
        color_class = "success-text" if balance["balance_neto"] >= 0 else "danger-text"
        self.card_balance.lbl_valor.setProperty("class", f"title {color_class}")
        # Reset style para forzar repintado
        self.card_balance.lbl_valor.style().unpolish(self.card_balance.lbl_valor)
        self.card_balance.lbl_valor.style().polish(self.card_balance.lbl_valor)

        transacciones = self.cont_svc.get_transacciones()
        self._table.setRowCount(len(transacciones))
        for i, t in enumerate(transacciones):
            fecha = t.fecha.replace("T", " ")[:16]
            self._table.setItem(i, 0, QTableWidgetItem(fecha))
            
            tipo_item = QTableWidgetItem("Ingreso" if t.tipo == "ingreso" else "Egreso")
            if t.tipo == "ingreso":
                tipo_item.setForeground(Qt.GlobalColor.darkGreen)
            else:
                tipo_item.setForeground(Qt.GlobalColor.darkRed)
            self._table.setItem(i, 1, tipo_item)
            
            self._table.setItem(i, 2, QTableWidgetItem(t.descripcion))
            self._table.setItem(i, 3, QTableWidgetItem(t.categoria or "-"))
            
            monto_str = f"{app_config.CURRENCY_SYMBOL}{t.monto:.2f}"
            self._table.setItem(i, 4, QTableWidgetItem(monto_str))
            
            self._table.setRowHeight(i, 40)

    def _registrar_egreso(self):
        dlg = RegistrarEgresoDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.resultado_transaccion:
            self.cont_svc.crear_transaccion(dlg.resultado_transaccion)
            self.cargar_datos()
