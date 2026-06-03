"""Sidebar de navegación principal con soporte de roles."""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget,
)
from PySide6.QtCore import Qt, Signal

import config as app_config


class SidebarButton(QPushButton):
    """Botón de navegación del sidebar."""

    def __init__(self, icon, text, name, parent=None):
        super().__init__(f"  {icon}   {text}", parent)
        self.name = name
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setCheckable(True)
        self.setProperty("class", "sidebar-nav-button")


class Sidebar(QFrame):
    """Sidebar de navegación lateral con filtrado por rol."""

    navigation_changed = Signal(str)
    logout_requested = Signal()

    ALL_MENU_ITEMS = [
        ("📊", "Dashboard", "dashboard"),
        ("🛒", "Punto de Venta", "pos"),
        ("📋", "Menú", "menu"),
        ("📦", "Órdenes", "ordenes"),
        ("🛵", "Domicilios", "domicilios"),
        ("👨‍🍳", "Cocina", "cocina"),
        ("📈", "Reportes", "reportes"),
        ("💰", "Contabilidad", "contabilidad"),
        ("⚙️", "Ajustes", "ajustes"),
        ("👥", "Usuarios", "usuarios"),
    ]

    def __init__(self, allowed_modules=None, user_display_name="", user_role="",
                 parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self._allowed = allowed_modules or [item[2] for item in self.ALL_MENU_ITEMS]
        self._user_name = user_display_name
        self._user_role = user_role
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(4)

        # Logo / Brand
        brand = QFrame()
        brand.setObjectName("sidebar-brand-frame")
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(8, 8, 8, 16)
        brand_layout.setSpacing(12)

        logo_lbl = QLabel("🍕")
        logo_lbl.setObjectName("sidebar-logo-label")
        brand_layout.addWidget(logo_lbl)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(2)
        name_lbl = QLabel(app_config.APP_NAME)
        name_lbl.setProperty("class", "title")
        name_lbl.setObjectName("sidebar-brand-title")
        brand_text.addWidget(name_lbl)
        slogan_lbl = QLabel(app_config.BUSINESS_SLOGAN)
        slogan_lbl.setProperty("class", "caption")
        slogan_lbl.setObjectName("sidebar-brand-caption")
        brand_text.addWidget(slogan_lbl)
        brand_layout.addLayout(brand_text)
        brand_layout.addStretch()

        layout.addWidget(brand)

        # Separador
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setObjectName("sidebar-separator")
        layout.addWidget(sep)
        layout.addSpacing(8)

        # Sección label
        nav_label = QLabel("NAVEGACIÓN")
        nav_label.setProperty("class", "section")
        nav_label.setObjectName("sidebar-nav-label")
        layout.addWidget(nav_label)
        layout.addSpacing(4)

        # Botones de navegación (filtrados por rol)
        self._buttons = {}
        for icon, text, name in self.ALL_MENU_ITEMS:
            if name not in self._allowed:
                continue
            btn = SidebarButton(icon, text, name)
            btn.clicked.connect(lambda checked, n=name: self._on_nav_click(n))
            self._buttons[name] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Separador footer
        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setObjectName("sidebar-separator")
        layout.addWidget(sep2)

        # Info del usuario logueado
        if self._user_name:
            user_frame = QHBoxLayout()
            user_frame.setContentsMargins(8, 10, 8, 4)
            user_frame.setSpacing(10)

            user_avatar = QLabel("👤")
            user_avatar.setStyleSheet(
                "font-size: 20px; background: transparent; border: none;"
            )
            user_frame.addWidget(user_avatar)

            user_info = QVBoxLayout()
            user_info.setSpacing(0)
            user_name_lbl = QLabel(self._user_name)
            user_name_lbl.setProperty("class", "caption")
            user_name_lbl.setStyleSheet("font-weight: 600; border: none;")
            user_info.addWidget(user_name_lbl)

            role_text = "🔑 Administrador" if self._user_role == "admin" else "🧑‍💼 Cajero"
            role_lbl = QLabel(role_text)
            role_lbl.setProperty("class", "caption")
            role_lbl.setStyleSheet("font-size: 10px; border: none;")
            user_info.addWidget(role_lbl)
            user_frame.addLayout(user_info)
            user_frame.addStretch()
            layout.addLayout(user_frame)

        # Botón cerrar sesión
        btn_logout = QPushButton("🚪  Cerrar Sesión")
        btn_logout.setFixedHeight(38)
        btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_logout.setProperty("class", "secondary")
        btn_logout.clicked.connect(self.logout_requested.emit)
        layout.addWidget(btn_logout)

        # Versión
        version_lbl = QLabel(f"v{app_config.APP_VERSION}  •  {app_config.APP_NAME}")
        version_lbl.setProperty("class", "caption")
        version_lbl.setObjectName("sidebar-version-label")
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_lbl)

    def _on_nav_click(self, name):
        for key, btn in self._buttons.items():
            btn.setChecked(key == name)
        self.navigation_changed.emit(name)

    def set_active(self, name):
        """Establece el botón activo programáticamente."""
        for key, btn in self._buttons.items():
            btn.setChecked(key == name)
