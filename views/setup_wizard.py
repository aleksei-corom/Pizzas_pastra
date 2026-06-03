"""Asistente de configuración inicial — Primera ejecución."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QDoubleSpinBox, QFrame, QWidget, QStackedWidget,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from database.db_manager import DatabaseManager


class SetupWizard(QDialog):
    """Wizard de configuración inicial para primer uso."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.setWindowTitle("Configuración Inicial")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setMinimumSize(560, 680)
        self._result_data = {}
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            SetupWizard { background-color: #0f172a; }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setFixedWidth(500)
        card.setStyleSheet("""
            QFrame {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 20px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 36, 40, 36)
        card_layout.setSpacing(16)

        # Header
        logo = QLabel("🍕")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet("font-size: 48px; background: transparent; border: none;")
        card_layout.addWidget(logo)

        title = QLabel("¡Bienvenido!")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: 26px; font-weight: 800; color: #f1f5f9; "
            "background: transparent; border: none;"
        )
        card_layout.addWidget(title)

        subtitle = QLabel(
            "Configura los datos de tu negocio y crea tu\n"
            "usuario administrador para comenzar."
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(
            "font-size: 13px; color: #94a3b8; background: transparent; border: none;"
        )
        card_layout.addWidget(subtitle)

        card_layout.addSpacing(8)

        # Stacked pages
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background: transparent; border: none;")

        # Page 1: Datos del negocio
        page1 = QWidget()
        page1.setStyleSheet("background: transparent; border: none;")
        p1 = QVBoxLayout(page1)
        p1.setContentsMargins(0, 0, 0, 0)
        p1.setSpacing(12)

        p1.addWidget(self._section_label("📋  DATOS DEL NEGOCIO"))

        self._business_name = self._create_input("Nombre del negocio", "Ej: Pizzas Pastra")
        p1.addWidget(self._field("Nombre del Negocio *", self._business_name))

        self._business_slogan = self._create_input("Slogan o descripción", "Ej: Pizzería & Comidas Rápidas")
        p1.addWidget(self._field("Slogan", self._business_slogan))

        self._business_phone = self._create_input("Teléfono de contacto", "Ej: +58 412-000-0000")
        p1.addWidget(self._field("Teléfono", self._business_phone))

        self._business_address = self._create_input("Dirección del local", "Ej: Av. Principal, Local 1")
        p1.addWidget(self._field("Dirección", self._business_address))

        row_currency = QHBoxLayout()
        self._currency = self._create_input("$", "")
        self._currency.setFixedWidth(60)
        row_currency.addWidget(self._field("Moneda", self._currency))

        self._tax_rate = QDoubleSpinBox()
        self._tax_rate.setRange(0, 100)
        self._tax_rate.setValue(16.0)
        self._tax_rate.setSuffix(" %")
        self._tax_rate.setDecimals(1)
        self._tax_rate.setFixedHeight(42)
        self._tax_rate.setStyleSheet(self._input_style())
        row_currency.addWidget(self._field("Impuesto (IVA)", self._tax_rate))
        p1.addLayout(row_currency)

        self._stack.addWidget(page1)

        # Page 2: Datos del administrador
        page2 = QWidget()
        page2.setStyleSheet("background: transparent; border: none;")
        p2 = QVBoxLayout(page2)
        p2.setContentsMargins(0, 0, 0, 0)
        p2.setSpacing(12)

        p2.addWidget(self._section_label("🔑  CUENTA DE ADMINISTRADOR"))

        self._admin_name = self._create_input("Nombre completo", "Ej: Juan Pérez")
        p2.addWidget(self._field("Nombre del Administrador *", self._admin_name))

        self._admin_user = self._create_input("Nombre de usuario (login)", "Ej: admin")
        p2.addWidget(self._field("Usuario *", self._admin_user))

        self._admin_pw = self._create_input("Contraseña", "Mínimo 4 caracteres")
        self._admin_pw.setEchoMode(QLineEdit.EchoMode.Password)
        p2.addWidget(self._field("Contraseña *", self._admin_pw))

        self._admin_pw2 = self._create_input("Confirmar contraseña", "")
        self._admin_pw2.setEchoMode(QLineEdit.EchoMode.Password)
        p2.addWidget(self._field("Confirmar Contraseña *", self._admin_pw2))

        self._stack.addWidget(page2)

        card_layout.addWidget(self._stack)

        # Error label
        self._error_lbl = QLabel("")
        self._error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_lbl.setStyleSheet(
            "color: #ef4444; font-size: 12px; font-weight: 600; "
            "background: transparent; border: none; min-height: 20px;"
        )
        self._error_lbl.setVisible(False)
        card_layout.addWidget(self._error_lbl)

        # Botones de navegación
        btns = QHBoxLayout()

        self._btn_back = QPushButton("← Atrás")
        self._btn_back.setFixedHeight(44)
        self._btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_back.setStyleSheet("""
            QPushButton {
                background-color: #334155; color: #94a3b8; border: none;
                border-radius: 12px; font-size: 14px; font-weight: 600;
            }
            QPushButton:hover { background-color: #475569; color: #f1f5f9; }
        """)
        self._btn_back.clicked.connect(self._go_back)
        self._btn_back.setVisible(False)
        btns.addWidget(self._btn_back)

        self._btn_next = QPushButton("Siguiente →")
        self._btn_next.setFixedHeight(44)
        self._btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_next.setStyleSheet("""
            QPushButton {
                background-color: #e63946; color: #ffffff; border: none;
                border-radius: 12px; font-size: 14px; font-weight: 700;
            }
            QPushButton:hover { background-color: #c1121f; }
        """)
        self._btn_next.clicked.connect(self._go_next)
        btns.addWidget(self._btn_next)

        card_layout.addLayout(btns)

        # Step indicator
        self._step_lbl = QLabel("Paso 1 de 2")
        self._step_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._step_lbl.setStyleSheet(
            "font-size: 11px; color: #475569; background: transparent; border: none;"
        )
        card_layout.addWidget(self._step_lbl)

        main_layout.addWidget(card)
        QTimer.singleShot(100, self._business_name.setFocus)

    def _go_next(self):
        current = self._stack.currentIndex()
        if current == 0:
            # Validar página 1
            if not self._business_name.text().strip():
                self._show_error("El nombre del negocio es obligatorio.")
                return
            self._error_lbl.setVisible(False)
            self._stack.setCurrentIndex(1)
            self._btn_back.setVisible(True)
            self._btn_next.setText("🚀  Comenzar")
            self._step_lbl.setText("Paso 2 de 2")
            self._admin_name.setFocus()
        elif current == 1:
            # Validar página 2
            if not self._admin_name.text().strip():
                self._show_error("El nombre del administrador es obligatorio.")
                return
            if not self._admin_user.text().strip():
                self._show_error("El usuario es obligatorio.")
                return
            pw = self._admin_pw.text()
            if len(pw) < 4:
                self._show_error("La contraseña debe tener al menos 4 caracteres.")
                return
            if pw != self._admin_pw2.text():
                self._show_error("Las contraseñas no coinciden.")
                return
            self._finish()

    def _go_back(self):
        self._error_lbl.setVisible(False)
        self._stack.setCurrentIndex(0)
        self._btn_back.setVisible(False)
        self._btn_next.setText("Siguiente →")
        self._step_lbl.setText("Paso 1 de 2")

    def _finish(self):
        """Guarda toda la configuración y crea el admin."""
        import config as app_config

        biz_name = self._business_name.text().strip()
        biz_slogan = self._business_slogan.text().strip()
        biz_phone = self._business_phone.text().strip()
        biz_address = self._business_address.text().strip()
        currency = self._currency.text().strip() or "$"
        tax = self._tax_rate.value() / 100.0

        # Guardar en DB
        self.db.set_config("business_name", biz_name)
        self.db.set_config("business_slogan", biz_slogan)
        self.db.set_config("business_phone", biz_phone)
        self.db.set_config("business_address", biz_address)
        self.db.set_config("currency_symbol", currency)
        self.db.set_config("tax_rate", str(tax))

        # Actualizar config globals en memoria
        app_config.APP_NAME = biz_name
        app_config.BUSINESS_NAME = biz_name
        app_config.BUSINESS_SLOGAN = biz_slogan
        app_config.BUSINESS_PHONE = biz_phone
        app_config.BUSINESS_ADDRESS = biz_address
        app_config.CURRENCY_SYMBOL = currency
        app_config.TAX_RATE = tax

        # Crear usuario admin
        self.db.crear_usuario(
            username=self._admin_user.text().strip(),
            password=self._admin_pw.text(),
            nombre_completo=self._admin_name.text().strip(),
            rol="admin"
        )

        self._result_data = {
            "business_name": biz_name,
            "admin_username": self._admin_user.text().strip(),
        }
        self.accept()

    def _show_error(self, text):
        self._error_lbl.setText(f"⚠️ {text}")
        self._error_lbl.setVisible(True)

    # ─── UI Helpers ───

    def _create_input(self, placeholder, example):
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setFixedHeight(42)
        inp.setStyleSheet(self._input_style())
        return inp

    @staticmethod
    def _input_style():
        return """
            QLineEdit, QDoubleSpinBox {
                background-color: #334155; color: #f1f5f9;
                border: 1.5px solid #475569; border-radius: 10px;
                padding: 10px 14px; font-size: 13px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus { border-color: #e63946; }
            QLineEdit::placeholder { color: #64748b; }
        """

    @staticmethod
    def _section_label(text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size: 11px; font-weight: 700; color: #e63946; "
            "letter-spacing: 1px; background: transparent; border: none;"
        )
        return lbl

    @staticmethod
    def _field(label_text, widget):
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        lbl = QLabel(label_text)
        lbl.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #94a3b8; "
            "background: transparent; border: none;"
        )
        layout.addWidget(lbl)
        layout.addWidget(widget)
        return container

    @property
    def result_data(self):
        return self._result_data

    def showEvent(self, event):
        super().showEvent(event)
        self.showMaximized()
