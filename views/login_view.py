"""Pantalla de Login — Autenticación de usuarios."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QGraphicsOpacityEffect,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont

from database.db_manager import DatabaseManager
import config as app_config


class LoginView(QDialog):
    """Pantalla de login a pantalla completa."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self._logged_user = None
        self.setWindowTitle(f"🍕 {app_config.APP_NAME} — Iniciar Sesión")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMinimumSize(500, 600)
        self._build_ui()

    def _build_ui(self):
        # Fondo oscuro a pantalla completa
        self.setStyleSheet("""
            LoginView {
                background-color: #0f172a;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Card central
        card = QFrame()
        card.setFixedWidth(420)
        card.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 20px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 48, 40, 40)
        card_layout.setSpacing(24)

        # Logo
        logo = QLabel("🍕")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size: 64px; background: transparent; border: none;")
        card_layout.addWidget(logo)

        # Título
        title = QLabel(app_config.APP_NAME)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 28px; font-weight: 800; color: #f1f5f9; "
            "background: transparent; border: none;"
        )
        card_layout.addWidget(title)

        subtitle = QLabel("Ingresa tus credenciales para continuar")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            "font-size: 13px; color: #94a3b8; background: transparent; border: none;"
        )
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(8)

        # Campo usuario
        user_label = QLabel("USUARIO")
        user_label.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #94a3b8; "
            "letter-spacing: 1px; background: transparent; border: none;"
        )
        card_layout.addWidget(user_label)

        self._username = QLineEdit()
        self._username.setPlaceholderText("Tu nombre de usuario")
        self._username.setFixedHeight(44)
        self._username.setStyleSheet("""
            QLineEdit {
                background-color: #334155;
                color: #f1f5f9;
                border: 1.5px solid #475569;
                border-radius: 10px;
                padding: 10px 16px;
                font-size: 14px;
            }
            QLineEdit:focus { border-color: #e63946; }
            QLineEdit::placeholder { color: #64748b; }
        """)
        card_layout.addWidget(self._username)

        # Campo contraseña
        pw_label = QLabel("CONTRASEÑA")
        pw_label.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #94a3b8; "
            "letter-spacing: 1px; background: transparent; border: none;"
        )
        card_layout.addWidget(pw_label)

        self._password = QLineEdit()
        self._password.setPlaceholderText("Tu contraseña")
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._password.setFixedHeight(44)
        self._password.setStyleSheet(self._username.styleSheet())
        self._password.returnPressed.connect(self._do_login)
        card_layout.addWidget(self._password)

        # Mensaje de error
        self._error_lbl = QLabel("")
        self._error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_lbl.setStyleSheet(
            "color: #ef4444; font-size: 12px; font-weight: 600; "
            "background: transparent; border: none; min-height: 20px;"
        )
        self._error_lbl.setVisible(False)
        card_layout.addWidget(self._error_lbl)

        card_layout.addSpacing(4)

        # Botón login
        self._btn_login = QPushButton("🔐  Iniciar Sesión")
        self._btn_login.setFixedHeight(48)
        self._btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_login.setStyleSheet("""
            QPushButton {
                background-color: #e63946;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 700;
            }
            QPushButton:hover { background-color: #c1121f; }
            QPushButton:pressed { padding-top: 2px; }
        """)
        self._btn_login.clicked.connect(self._do_login)
        card_layout.addWidget(self._btn_login)

        # Footer
        footer = QLabel(f"v{app_config.APP_VERSION} • {app_config.BUSINESS_SLOGAN}")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(
            "font-size: 11px; color: #475569; background: transparent; border: none;"
        )
        card_layout.addWidget(footer)

        main_layout.addWidget(card)

        # Focus en username
        QTimer.singleShot(100, self._username.setFocus)

    def _do_login(self):
        """Intenta autenticar al usuario."""
        username = self._username.text().strip()
        password = self._password.text()

        if not username or not password:
            self._show_error("Ingresa usuario y contraseña")
            return

        user = self.db.verificar_password(username, password)
        if user is None:
            self._show_error("Usuario o contraseña incorrectos")
            self._password.selectAll()
            self._password.setFocus()
            return

        self._logged_user = user
        self.accept()

    def _show_error(self, text: str):
        """Muestra mensaje de error con animación."""
        self._error_lbl.setText(f"⚠️ {text}")
        self._error_lbl.setVisible(True)

        # Shake animation en el card
        effect = QGraphicsOpacityEffect(self._error_lbl)
        self._error_lbl.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(300)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.start()
        self._error_anim = anim  # Evitar garbage collection

    @property
    def logged_user(self):
        return self._logged_user

    def showEvent(self, event):
        """Maximizar al mostrar."""
        super().showEvent(event)
        self.showMaximized()
