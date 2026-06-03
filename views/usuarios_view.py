"""Vista de gestión de usuarios — Solo para administradores."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
)
from PySide6.QtCore import Qt

from database.db_manager import DatabaseManager
from views.components import ModernMessageBox
from views.components.user_dialog import UserDialog
from views.layouts import create_page_header


ROLE_LABELS = {
    "admin": "🔑 Administrador",
    "cajero": "🧑‍💼 Cajero",
}


class UsuariosView(QWidget):
    """Vista de administración de usuarios."""

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Header
        btn_nuevo = QPushButton("➕  Nuevo Usuario")
        btn_nuevo.setFixedHeight(38)
        btn_nuevo.clicked.connect(self._nuevo_usuario)
        layout.addLayout(create_page_header(
            "👥  Gestión de Usuarios",
            "Administra los usuarios y permisos del sistema",
            actions=[btn_nuevo]
        ))

        # Tabla
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "Usuario", "Nombre Completo", "Rol", "Estado", "Creado", "Acciones"
        ])
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.Fixed
        )
        self._table.setColumnWidth(5, 180)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, 1)

    def cargar_datos(self):
        """Carga la lista de usuarios en la tabla."""
        usuarios = self.db.get_usuarios()
        self._table.setRowCount(len(usuarios))

        for i, u in enumerate(usuarios):
            self._table.setItem(i, 0, QTableWidgetItem(u.username))
            self._table.setItem(i, 1, QTableWidgetItem(u.nombre_completo))

            rol_text = ROLE_LABELS.get(u.rol, u.rol)
            self._table.setItem(i, 2, QTableWidgetItem(rol_text))

            estado = "✅ Activo" if u.activo else "⛔ Inactivo"
            self._table.setItem(i, 3, QTableWidgetItem(estado))

            fecha = u.fecha_creacion[:10] if u.fecha_creacion else ""
            self._table.setItem(i, 4, QTableWidgetItem(fecha))

            # Acciones
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(6)

            btn_edit = QPushButton("✏️ Editar")
            btn_edit.setFixedHeight(30)
            btn_edit.setProperty("class", "icon-warning")
            btn_edit.clicked.connect(lambda _, uid=u.id: self._editar_usuario(uid))
            actions_layout.addWidget(btn_edit)

            btn_toggle = QPushButton("⛔" if u.activo else "✅")
            btn_toggle.setFixedSize(30, 30)
            btn_toggle.setToolTip("Desactivar" if u.activo else "Activar")
            btn_toggle.setProperty("class", "icon-danger" if u.activo else "icon-success")
            btn_toggle.clicked.connect(lambda _, uid=u.id, act=u.activo: self._toggle_usuario(uid, act))
            actions_layout.addWidget(btn_toggle)

            self._table.setCellWidget(i, 5, actions)
            self._table.setRowHeight(i, 44)

    def _nuevo_usuario(self):
        dlg = UserDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            try:
                self.db.crear_usuario(
                    username=dlg.usuario.username,
                    password=dlg.new_password,
                    nombre_completo=dlg.usuario.nombre_completo,
                    rol=dlg.usuario.rol
                )
                ModernMessageBox.success(
                    self, "Usuario Creado",
                    f"El usuario '{dlg.usuario.username}' ha sido creado exitosamente."
                )
                self.cargar_datos()
            except Exception as e:
                if "UNIQUE" in str(e):
                    ModernMessageBox.error(
                        self, "Error", "Ya existe un usuario con ese nombre."
                    )
                else:
                    ModernMessageBox.error(self, "Error", str(e))

    def _editar_usuario(self, user_id):
        usuarios = self.db.get_usuarios()
        usuario = next((u for u in usuarios if u.id == user_id), None)
        if not usuario:
            return

        dlg = UserDialog(self, usuario=usuario)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            u = dlg.usuario
            self.db.actualizar_usuario(u.id, u.nombre_completo, u.rol, u.activo)
            if dlg.new_password:
                self.db.cambiar_password(u.id, dlg.new_password)
            ModernMessageBox.success(
                self, "Usuario Actualizado",
                f"'{u.username}' actualizado correctamente."
            )
            self.cargar_datos()

    def _toggle_usuario(self, user_id, activo_actual):
        if activo_actual:
            # Verificar que no sea el último admin
            usuario = next((u for u in self.db.get_usuarios() if u.id == user_id), None)
            if usuario and usuario.rol == "admin":
                if self.db.contar_admins_activos() <= 1:
                    ModernMessageBox.error(
                        self, "Operación No Permitida",
                        "No puedes desactivar al último administrador activo."
                    )
                    return

            result = ModernMessageBox.question(
                self, "Desactivar Usuario",
                "¿Estás seguro de que deseas desactivar este usuario?\n"
                "No podrá iniciar sesión hasta que sea reactivado."
            )
            if result != QDialog.DialogCode.Accepted:
                return

        usuario = next((u for u in self.db.get_usuarios() if u.id == user_id), None)
        if usuario:
            self.db.actualizar_usuario(
                user_id, usuario.nombre_completo, usuario.rol, not activo_actual
            )
            self.cargar_datos()
