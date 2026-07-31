"""Diálogo de creación de premios canjeables por puntos."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QDoubleSpinBox, QSpinBox, QFormLayout,
    QComboBox,
)
from PySide6.QtCore import Qt

from database.models import Premio


class PremioDialog(QDialog):
    """Diálogo para crear un nuevo premio."""

    def __init__(self, productos: list = None, parent=None):
        super().__init__(parent)
        self._productos = productos or []
        self.setWindowTitle("Nuevo Premio")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        titulo = QLabel("⭐  Nuevo Premio")
        titulo.setProperty("class", "title")
        layout.addWidget(titulo)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._nombre = QLineEdit()
        self._nombre.setPlaceholderText("Ej: Pizza Gratis")
        self._nombre.setMinimumHeight(36)
        form.addRow("Nombre *", self._nombre)

        self._desc = QLineEdit()
        self._desc.setPlaceholderText("Descripción del premio")
        self._desc.setMinimumHeight(36)
        form.addRow("Descripción", self._desc)

        self._puntos = QSpinBox()
        self._puntos.setMinimum(100)
        self._puntos.setMaximum(99999)
        self._puntos.setValue(1000)
        self._puntos.setSuffix(" pts")
        self._puntos.setMinimumHeight(36)
        form.addRow("Puntos requeridos *", self._puntos)

        self._descuento = QDoubleSpinBox()
        self._descuento.setMinimum(0)
        self._descuento.setMaximum(100)
        self._descuento.setValue(0)
        self._descuento.setSuffix(" %")
        self._descuento.setMinimumHeight(36)
        self._descuento.valueChanged.connect(self._on_descuento_changed)
        form.addRow("Descuento (%)", self._descuento)

        self._prod_combo = QComboBox()
        self._prod_combo.setMinimumHeight(36)
        self._prod_combo.addItem("-- Ninguno --", None)
        for p in self._productos:
            self._prod_combo.addItem(f"{p.nombre} (${p.precio:.2f})", p.id)
        self._prod_combo.currentIndexChanged.connect(self._on_producto_changed)
        form.addRow("Producto gratis", self._prod_combo)

        layout.addLayout(form)

        # Botones
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "secondary")
        btn_cancel.setFixedHeight(38)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("Crear Premio")
        btn_save.setFixedHeight(38)
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._accept)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def _on_descuento_changed(self, val):
        if val > 0:
            self._prod_combo.setCurrentIndex(0)

    def _on_producto_changed(self, idx):
        if idx > 0:
            self._descuento.setValue(0)

    def _accept(self):
        if not self._nombre.text().strip():
            self._nombre.setFocus()
            return
        if self._descuento.value() == 0 and self._prod_combo.currentData() is None:
            return
        self.accept()

    def get_premio(self) -> Premio:
        return Premio(
            nombre=self._nombre.text().strip(),
            descripcion=self._desc.text().strip(),
            puntos_requeridos=self._puntos.value(),
            descuento_porcentaje=self._descuento.value(),
            producto_gratis_id=self._prod_combo.currentData(),
        )
