"""Diálogo para crear/editar usuarios."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QFrame,
)
from PySide6.QtCore import Qt

from database.models import Usuario
from views.components import ModernMessageBox
from views.layouts import create_form_row


class UserDialog(QDialog):
    """Diálogo para crear o editar un usuario."""

    ROLES = [
        ("admin", "🔑 Administrador"),
        ("cajero", "🧑‍💼 Cajero"),
    ]

    def __init__(self, parent=None, usuario=None):
        super().__init__(parent)
        self.usuario = usuario
        self.new_password = None  # Se llenará solo si el usuario escribe algo
        self.setWindowTitle("Editar Usuario" if usuario else "Nuevo Usuario")
        self.setMinimumWidth(460)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_ui()
        if usuario:
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

        # Título
        is_edit = self.usuario is not None
        title_text = "✏️  Editar Usuario" if is_edit else "👤  Nuevo Usuario"
        title = QLabel(title_text)
        title.setProperty("class", "title")
        layout.addWidget(title)

        # Username
        self._username = QLineEdit()
        self._username.setPlaceholderText("Nombre de usuario (login)")
        if is_edit:
            self._username.setEnabled(False)  # No se puede cambiar el username
        layout.addLayout(create_form_row("Usuario", self._username, required=True))

        # Nombre completo
        self._nombre = QLineEdit()
        self._nombre.setPlaceholderText("Nombre y apellido")
        layout.addLayout(create_form_row("Nombre Completo", self._nombre, required=True))

        # Contraseña
        pw_hint = "Dejar vacío para no cambiar" if is_edit else ""
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setPlaceholderText(
            "Nueva contraseña" if is_edit else "Contraseña"
        )
        layout.addLayout(create_form_row(
            "Contraseña", self._password,
            required=not is_edit,
            hint=pw_hint
        ))

        # Confirmar contraseña
        self._password_confirm = QLineEdit()
        self._password_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_confirm.setPlaceholderText("Confirmar contraseña")
        layout.addLayout(create_form_row("Confirmar Contraseña", self._password_confirm,
                                          required=not is_edit))

        # Rol
        self._rol = QComboBox()
        for key, label in self.ROLES:
            self._rol.addItem(label, key)
        layout.addLayout(create_form_row("Rol", self._rol, required=True))

        # Activo (solo en edición)
        if is_edit:
            self._activo = QCheckBox("Usuario activo")
            self._activo.setChecked(True)
            layout.addWidget(self._activo)
        else:
            self._activo = None

        # Separador
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setProperty("class", "divider")
        layout.addWidget(sep)

        # Botones
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
        u = self.usuario
        self._username.setText(u.username)
        self._nombre.setText(u.nombre_completo)
        # Password no se muestra
        idx = self._rol.findData(u.rol)
        if idx >= 0:
            self._rol.setCurrentIndex(idx)
        if self._activo:
            self._activo.setChecked(u.activo)

    def _save(self):
        username = self._username.text().strip()
        nombre = self._nombre.text().strip()
        password = self._password.text()
        password_confirm = self._password_confirm.text()
        rol = self._rol.currentData()

        if not username:
            ModernMessageBox.warning(self, "Campo Requerido", "El usuario es obligatorio.")
            return

        if not nombre:
            ModernMessageBox.warning(self, "Campo Requerido", "El nombre completo es obligatorio.")
            return

        is_edit = self.usuario is not None

        # Validar contraseña
        if not is_edit and not password:
            ModernMessageBox.warning(self, "Campo Requerido", "La contraseña es obligatoria para nuevos usuarios.")
            return

        if password:
            if len(password) < 4:
                ModernMessageBox.warning(self, "Contraseña Débil", "La contraseña debe tener al menos 4 caracteres.")
                return
            if password != password_confirm:
                ModernMessageBox.warning(self, "Error de Contraseña", "Las contraseñas no coinciden.")
                return
            self.new_password = password

        # Actualizar o crear objeto
        if self.usuario is None:
            self.usuario = Usuario()

        self.usuario.username = username
        self.usuario.nombre_completo = nombre
        self.usuario.rol = rol
        if self._activo:
            self.usuario.activo = self._activo.isChecked()
        else:
            self.usuario.activo = True

        self.accept()
