"""Diálogo de creación/edición de clientes del CRM."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QDateEdit,
)
from PySide6.QtCore import Qt, QDate

from database.models import Cliente


class ClienteDialog(QDialog):
    """Diálogo para crear o editar un cliente."""

    def __init__(self, cliente: Cliente = None, parent=None):
        super().__init__(parent)
        self._cliente = cliente or Cliente()
        self.setWindowTitle("Editar Cliente" if cliente else "Nuevo Cliente")
        self.setMinimumWidth(420)
        self.setModal(True)
        self._build_ui()

        if cliente:
            self._populate(cliente)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        # Título
        titulo = QLabel("✉️  Datos del Cliente")
        titulo.setProperty("class", "title")
        layout.addWidget(titulo)

        # Formulario
        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self._nombre = QLineEdit()
        self._nombre.setPlaceholderText("Nombre completo")
        self._nombre.setMinimumHeight(36)
        form.addRow("Nombre *", self._nombre)

        self._telefono = QLineEdit()
        self._telefono.setPlaceholderText("+58 412-000-0000")
        self._telefono.setMinimumHeight(36)
        form.addRow("Teléfono *", self._telefono)

        self._email = QLineEdit()
        self._email.setPlaceholderText("correo@ejemplo.com")
        self._email.setMinimumHeight(36)
        form.addRow("Email", self._email)

        self._cumpleanos = QDateEdit()
        self._cumpleanos.setCalendarPopup(True)
        self._cumpleanos.setDisplayFormat("dd/MM/yyyy")
        self._cumpleanos.setDate(QDate.currentDate())
        self._cumpleanos.setMinimumHeight(36)
        form.addRow("Cumpleaños", self._cumpleanos)

        self._notas = QLineEdit()
        self._notas.setPlaceholderText("Notas opcionales")
        self._notas.setMinimumHeight(36)
        form.addRow("Notas", self._notas)

        layout.addLayout(form)

        # Botones
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "secondary")
        btn_cancel.setFixedHeight(38)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("Guardar")
        btn_save.setFixedHeight(38)
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._accept)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def _populate(self, c: Cliente):
        self._nombre.setText(c.nombre)
        self._telefono.setText(c.telefono)
        self._email.setText(c.email)
        self._notas.setText(c.notas)
        if c.fecha_cumpleanos:
            try:
                parts = c.fecha_cumpleanos.split("-")
                self._cumpleanos.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
            except (ValueError, IndexError):
                pass

    def _accept(self):
        if not self._nombre.text().strip():
            self._nombre.setFocus()
            return
        if not self._telefono.text().strip():
            self._telefono.setFocus()
            return
        self.accept()

    def get_cliente(self) -> Cliente:
        fecha_cum = self._cumpleanos.date().toString("yyyy-MM-dd")
        c = self._cliente
        c.nombre = self._nombre.text().strip()
        c.telefono = self._telefono.text().strip()
        c.email = self._email.text().strip()
        c.fecha_cumpleanos = fecha_cum
        c.notas = self._notas.text().strip()
        return c
