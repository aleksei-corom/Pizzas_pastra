"""Ventana principal con sidebar + stacked content (session-aware)."""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QStackedWidget,
    QLabel, QStatusBar, QDialog
)
from PySide6.QtCore import Qt, QTimer, Signal
from datetime import datetime

from config import APP_NAME, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
from views.themes.theme_helper import get_stylesheet
from utils.printer import check_printer_status, get_default_printer
from views.components import Sidebar, ModernMessageBox
from views.dashboard_view import DashboardView
from views.pos_view import POSView
from views.menu_view import MenuView
from views.ordenes_view import OrdenesView
from views.reportes_view import ReportesView
from views.contabilidad_view import ContabilidadView
from views.delivery_view import DeliveryView
from views.kds_view import KitchenDisplayView
from views.ajustes_view import AjustesView
from views.usuarios_view import UsuariosView
from utils.session import Session


class MainWindow(QMainWindow):
    """Ventana principal de Pizzas Pastra POS."""

    logout_signal = Signal()

    def __init__(self):
        super().__init__()
        self.session = Session.get()
        self.setWindowTitle(f"🍕 {APP_NAME} — Punto de Venta")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(1400, 850)

        self.setStyleSheet(get_stylesheet())

        self._build_ui()
        self._setup_clock()

        # Navegar a la primera vista permitida
        allowed = self.session.get_allowed_modules()
        default = allowed[0] if allowed else "pos"
        self._navigate(default)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar (filtrado por rol)
        user = self.session.user
        self._sidebar = Sidebar(
            allowed_modules=self.session.get_allowed_modules(),
            user_display_name=user.nombre_completo if user else "",
            user_role=user.rol if user else "",
        )
        self._sidebar.navigation_changed.connect(self._navigate)
        self._sidebar.logout_requested.connect(self._on_logout)
        main_layout.addWidget(self._sidebar)

        # Stacked views (solo las permitidas)
        self._stack = QStackedWidget()
        all_views = {
            "dashboard": DashboardView,
            "pos": POSView,
            "menu": MenuView,
            "ordenes": OrdenesView,
            "domicilios": DeliveryView,
            "cocina": KitchenDisplayView,
            "reportes": ReportesView,
            "contabilidad": ContabilidadView,
            "ajustes": AjustesView,
            "usuarios": UsuariosView,
        }

        self._views = {}
        for name, ViewClass in all_views.items():
            if self.session.has_access(name):
                view = ViewClass()
                self._views[name] = view
                self._stack.addWidget(view)

        main_layout.addWidget(self._stack, 1)

        # Status bar
        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)

        user_text = f"👤 {user.nombre_completo}" if user else ""
        self._status_left = QLabel(f"🍕 {APP_NAME}  •  {user_text}")
        self._clock_label = QLabel()

        self._printer_status = QLabel()
        self._status_bar.addPermanentWidget(self._printer_status)

        self._status_bar.addPermanentWidget(self._status_left)
        self._status_bar.addPermanentWidget(self._clock_label)

        # Inicializar estado de impresora (diferido para no bloquear constructor)
        self._printer_timer = QTimer(self)
        self._printer_timer.timeout.connect(self._update_printer_status)
        self._printer_timer.start(30000)  # Re-verificar cada 30 segundos
        QTimer.singleShot(100, self._update_printer_status)  # Primer check async

    def _navigate(self, name: str):
        """Navega a una vista por nombre."""
        if name in self._views:
            self._stack.setCurrentWidget(self._views[name])
            self._sidebar.set_active(name)

            # Refrescar datos al navegar
            view = self._views[name]
            if hasattr(view, 'cargar_datos'):
                view.cargar_datos()

    def _setup_clock(self):
        """Configura reloj en la barra de estado."""
        self._update_clock()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_clock)
        self._timer.start(1000)

    def _update_clock(self):
        now = datetime.now()
        self._clock_label.setText(now.strftime("🕐 %H:%M:%S  •  %d/%m/%Y"))

    def _update_printer_status(self):
        """Actualiza el indicador de estado de la impresora en la barra de estado."""
        try:
            from database.config_service import ConfigService
            from utils.session import Session

            printer_name = None
            try:
                session = Session.get()
                printer_name = session.get_preference("printer_name")
            except Exception:
                pass

            if not printer_name:
                try:
                    cfg_svc = ConfigService()
                    printer_name = cfg_svc.get_config("printer_name")
                except Exception:
                    pass

            if not printer_name:
                printer_name = get_default_printer() or ""

            if printer_name:
                online = check_printer_status(printer_name)
                if online:
                    self._printer_status.setText(f"🖨️  🟢 {printer_name}")
                    self._printer_status.setStyleSheet("color: #34d399;")
                else:
                    self._printer_status.setText(f"🖨️  🔴 {printer_name}")
                    self._printer_status.setStyleSheet("color: #f87171;")
            else:
                self._printer_status.setText("🖨️  ⚫ Sin impresora")
                self._printer_status.setStyleSheet("color: #6b7280;")
        except Exception:
            self._printer_status.setText("🖨️  ⚫ Error")
            self._printer_status.setStyleSheet("color: #f87171;")


    def _on_logout(self):
        """Maneja solicitud de cierre de sesión."""
        result = ModernMessageBox.question(
            self,
            "Cerrar Sesión",
            "¿Estás seguro de que deseas cerrar sesión?\n\n"
            "Volverás a la pantalla de inicio de sesión."
        )
        if result == QDialog.DialogCode.Accepted:
            self.session.logout()
            self.logout_signal.emit()
            self.close()

    def closeEvent(self, event):
        """Pide confirmación antes de cerrar la aplicación."""
        if not self.session.is_logged_in:
            # Ya se cerró sesión, dejar cerrar sin preguntar
            event.accept()
            return

        result = ModernMessageBox.question(
            self,
            "Cerrar Aplicación",
            f"¿Estás seguro de que deseas cerrar {APP_NAME}?\n\n"
            "Asegúrate de que no haya órdenes pendientes."
        )
        if result == QDialog.DialogCode.Accepted:
            event.accept()
        else:
            event.ignore()
