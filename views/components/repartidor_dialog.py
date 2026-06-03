"""Diálogo para crear/editar repartidores."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QFrame,
)
from PySide6.QtCore import Qt

from database.models import Repartidor
from views.components import ModernMessageBox
from views.layouts import create_form_row


VEHICULOS = [
    ("moto", "🏍️  Moto"),
    ("carro", "🚗  Carro"),
    ("bicicleta", "🚲  Bicicleta"),
    ("pie", "🚶  A Pie"),
]


class RepartidorDialog(QDialog):
    """Diálogo para crear o editar un repartidor."""

    def __init__(self, parent=None, repartidor=None):
        super().__init__(parent)
        self.repartidor = repartidor
        self.setWindowTitle("Editar Repartidor" if repartidor else "Nuevo Repartidor")
        self.setMinimumWidth(420)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_ui()
        if repartidor:
            self._fill_data()

    def _build_ui(self):
        outer = QFrame(self)
        outer.setObjectName("dlgOuter")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(outer)

        layout = QVBoxLayout(outer)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        is_edit = self.repartidor is not None
        title_text = "✏️  Editar Repartidor" if is_edit else "🛵  Nuevo Repartidor"
        title = QLabel(title_text)
        title.setProperty("class", "title")
        layout.addWidget(title)

        self._nombre = QLineEdit()
        self._nombre.setPlaceholderText("Nombre del repartidor")
        layout.addLayout(create_form_row("Nombre Completo", self._nombre, required=True))

        self._telefono = QLineEdit()
        self._telefono.setPlaceholderText("Ej: +58 412-000-0000")
        layout.addLayout(create_form_row("Teléfono", self._telefono))

        self._vehiculo = QComboBox()
        for key, label in VEHICULOS:
            self._vehiculo.addItem(label, key)
        layout.addLayout(create_form_row("Vehículo", self._vehiculo))

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setProperty("class", "divider")
        layout.addWidget(sep)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "secondary")
        btn_cancel.setFixedHeight(38)
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)

        btn_save = QPushButton("💾  Guardar")
        btn_save.setFixedHeight(38)
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _fill_data(self):
        r = self.repartidor
        self._nombre.setText(r.nombre)
        self._telefono.setText(r.telefono)
        idx = self._vehiculo.findData(r.vehiculo)
        if idx >= 0:
            self._vehiculo.setCurrentIndex(idx)

    def _save(self):
        nombre = self._nombre.text().strip()
        if not nombre:
            ModernMessageBox.warning(self, "Campo Requerido", "El nombre es obligatorio.")
            return

        if self.repartidor is None:
            self.repartidor = Repartidor(
                nombre=nombre,
                telefono=self._telefono.text().strip(),
                vehiculo=self._vehiculo.currentData(),
            )
        else:
            self.repartidor.nombre = nombre
            self.repartidor.telefono = self._telefono.text().strip()
            self.repartidor.vehiculo = self._vehiculo.currentData()

        self.accept()
