"""Vista Ajustes — Configuración del negocio."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QDoubleSpinBox, QFrame, QScrollArea, QComboBox, QCheckBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor

from database.db_manager import DatabaseManager
import config as app_config
from views.components import ModernMessageBox
from views.layouts import create_page_header, create_form_row
from utils.printer import get_available_printers, ESCPOSPrinter, get_default_printer, check_printer_status


class AjustesView(QWidget):
    """Vista de configuración del negocio."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Envolver todo en QScrollArea para evitar solapamientos
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        scroll_content = QWidget()
        scroll_content.setObjectName("scrollAreaWidgetContents")
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        layout.addLayout(create_page_header(
            "⚙️  Ajustes",
            "Configuración general del negocio"
        ))

        # Card: Información del Negocio
        info_card = self._make_card()
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(24, 16, 24, 16)
        info_layout.setSpacing(16)

        info_title = QLabel("🏪  Información del Negocio")
        info_title.setProperty("class", "title")
        info_layout.addWidget(info_title)

        row1 = QHBoxLayout()
        row1.setSpacing(16)
        self._nombre = self._make_input()
        row1.addLayout(create_form_row("Nombre del Negocio", self._nombre), 1)
        self._slogan = self._make_input()
        row1.addLayout(create_form_row("Slogan", self._slogan), 1)
        info_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(16)
        self._telefono = self._make_input()
        row2.addLayout(create_form_row("Teléfono", self._telefono), 1)
        self._direccion = self._make_input()
        row2.addLayout(create_form_row("Dirección", self._direccion), 1)
        info_layout.addLayout(row2)

        layout.addWidget(info_card)

        # Card: Facturación
        billing_card = self._make_card()
        billing_layout = QVBoxLayout(billing_card)
        billing_layout.setContentsMargins(24, 12, 24, 12)
        billing_layout.setSpacing(12)

        billing_title = QLabel("💰  Facturación")
        billing_title.setProperty("class", "title")
        billing_layout.addWidget(billing_title)

        row3 = QHBoxLayout()
        row3.setSpacing(16)
        self._moneda = self._make_input()
        self._moneda.setMaximumWidth(80)
        row3.addLayout(create_form_row("Símbolo Moneda", self._moneda))

        self._tax = QDoubleSpinBox()
        self._tax.setObjectName("formSpinBox")
        self._tax.setSuffix(" %")
        self._tax.setMaximum(100)
        self._tax.setDecimals(1)
        self._tax.setMaximumWidth(120)
        row3.addLayout(create_form_row("Impuesto (IVA)", self._tax))
        row3.addStretch()
        billing_layout.addLayout(row3)

        layout.addWidget(billing_card)

        # Card: Impresora Térmica
        printer_card = self._make_card()
        printer_layout = QVBoxLayout(printer_card)
        printer_layout.setContentsMargins(24, 12, 24, 12)
        printer_layout.setSpacing(12)

        printer_title = QLabel("🖨️  Impresora Térmica")
        printer_title.setProperty("class", "title")
        printer_layout.addWidget(printer_title)

        printer_desc = QLabel("Configura la impresora térmica de recibos (ESC/POS). Se usa al confirmar pagos en el POS.")
        printer_desc.setProperty("class", "caption")
        printer_desc.setWordWrap(True)
        printer_layout.addWidget(printer_desc)

        # Printer selection
        row_p1 = QHBoxLayout()
        row_p1.setSpacing(16)
        self._printer_combo = QComboBox()
        self._printer_combo.setMinimumWidth(300)
        self._printer_combo.setFixedHeight(36)
        row_p1.addLayout(create_form_row("Impresora", self._printer_combo), 2)

        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedSize(36, 36)
        btn_refresh.setToolTip("Actualizar lista de impresoras")
        btn_refresh.clicked.connect(self._refresh_printers)
        row_p1.addWidget(btn_refresh)

        btn_test = QPushButton("🧪  Imprimir Prueba")
        btn_test.setFixedHeight(36)
        btn_test.setProperty("class", "secondary")
        btn_test.clicked.connect(self._test_printer)
        row_p1.addWidget(btn_test)

        row_p1.addStretch()
        printer_layout.addLayout(row_p1)

        # Auto-cut toggle + paper width
        row_p2 = QHBoxLayout()
        row_p2.setSpacing(24)

        self._auto_cut = QCheckBox("✂️  Corte automático después de imprimir")
        self._auto_cut.setChecked(True)
        row_p2.addWidget(self._auto_cut)

        pw_label = QLabel("Papel:")
        pw_label.setProperty("class", "caption")
        row_p2.addWidget(pw_label)

        self._paper_width = QComboBox()
        self._paper_width.setFixedHeight(36)
        self._paper_width.addItem("80mm (48 columnas)", 48)
        self._paper_width.addItem("58mm (32 columnas)", 32)
        row_p2.addWidget(self._paper_width)

        cp_label = QLabel("Codificación:")
        cp_label.setProperty("class", "caption")
        row_p2.addWidget(cp_label)

        self._codepage = QComboBox()
        self._codepage.setFixedHeight(36)
        self._codepage.addItem("CP850 (Latin-1)", "cp850")
        self._codepage.addItem("CP437 (USA/Europe)", "cp437")
        row_p2.addWidget(self._codepage)

        row_p2.addStretch()
        printer_layout.addLayout(row_p2)

        # QR on receipts
        row_p3 = QHBoxLayout()
        self._printer_qr = QCheckBox("📱  Incluir código QR en los recibos")
        self._printer_qr.setChecked(True)
        row_p3.addWidget(self._printer_qr)
        qr_desc = QLabel("El QR contiene número de orden, total e información del negocio")
        qr_desc.setProperty("class", "caption")
        row_p3.addWidget(qr_desc)
        row_p3.addStretch()
        printer_layout.addLayout(row_p3)

        # PDF backup
        row_p4 = QHBoxLayout()
        self._printer_pdf = QCheckBox("📄  Guardar copia PDF del recibo en respaldos")
        self._printer_pdf.setChecked(True)
        row_p4.addWidget(self._printer_pdf)
        pdf_desc = QLabel("Se guarda en: %APPDATA%\\FastBitePOS\\receipts\\")
        pdf_desc.setProperty("class", "caption")
        row_p4.addWidget(pdf_desc)
        row_p4.addStretch()
        printer_layout.addLayout(row_p4)

        layout.addWidget(printer_card)

        # Card: Acerca de
        about_card = self._make_card()
        about_layout = QVBoxLayout(about_card)
        about_layout.setContentsMargins(24, 12, 24, 12)
        about_layout.setSpacing(4)

        about_title = QLabel("ℹ️  Acerca de")
        about_title.setProperty("class", "title")
        about_layout.addWidget(about_title)

        about_text = QLabel(
            f"{app_config.APP_NAME} POS v{app_config.APP_VERSION}\n"
            f"{app_config.BUSINESS_SLOGAN}\n\n"
            "Desarrollado con PySide6 + SQLite\n"
            f"© 2026 {app_config.APP_NAME} — Todos los derechos reservados"
        )
        about_text.setProperty("class", "subtitle")
        about_text.setWordWrap(True)
        about_layout.addWidget(about_text)

        layout.addWidget(about_card)

        # Botón guardar
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_reset = QPushButton("↺ Restaurar Valores por Defecto")
        btn_reset.setFixedHeight(44)
        btn_reset.setProperty("class", "secondary")
        btn_reset.clicked.connect(self._reset_defaults)
        btn_row.addWidget(btn_reset)

        btn_save = QPushButton("💾  Guardar Cambios")
        btn_save.setFixedHeight(44)
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        layout.addStretch()

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    @staticmethod
    def _make_card() -> QFrame:
        """Crea un QFrame card con estilo aplicado vía property (no cascada)."""
        card = QFrame()
        card.setProperty("class", "card")
        return card

    @staticmethod
    def _make_input(text: str = "") -> QLineEdit:
        """Crea un QLineEdit con estilo directo garantizando legibilidad.

        Usa objectName + selector ID para máxima especificidad en el
        stylesheet, y establece QPalette como respaldo infalible contra
        cascadas de estilos heredados del contenedor padre.
        """
        inp = QLineEdit(text)
        return inp

    def _refresh_printers(self):
        """Recarga la lista de impresoras disponibles con indicador de estado.

        ✅ = conectada, ❌ = desconectada, 🔌 = predeterminada del sistema.
        """
        current = self._printer_combo.currentText()
        self._printer_combo.clear()
        self._printer_combo.addItem("🔌 (Predeterminada de Windows)", "")
        self._printer_combo.setItemData(
            0, "🔌 Usar la impresora predeterminada de Windows",
            Qt.ToolTipRole
        )
        printers = get_available_printers()
        for i, p in enumerate(printers, start=1):
            online = check_printer_status(p)
            icon = "✅" if online else "❌"
            self._printer_combo.addItem(f"{icon}  {p}", p)
            status_text = "Conectada" if online else "Desconectada"
            self._printer_combo.setItemData(
                i,
                f"{p}\n"
                f"Estado: {status_text}\n"
                f"Haga clic en 🔄 para re-verificar conectividad",
                Qt.ToolTipRole
            )
        # Re-seleccionar preservando selección anterior
        idx = self._printer_combo.findText(current if current else "🔌 (Predeterminada de Windows)")
        if idx >= 0:
            self._printer_combo.setCurrentIndex(idx)

    def _test_printer(self):
        """Imprime una página de prueba para verificar la configuración."""
        printer_name = self._printer_combo.currentData() or None
        auto_cut = self._auto_cut.isChecked()
        pw = self._paper_width.currentData()
        cp = self._codepage.currentData()

        printer = ESCPOSPrinter(
            printer_name=printer_name,
            auto_cut=auto_cut,
            paper_width=pw,
            codepage=cp,
        )
        success, msg = printer.print_test()
        if success:
            ModernMessageBox.success(self, "✅ Prueba Exitosa",
                f"La página de prueba se imprimió correctamente.\n\n{msg}")
        else:
            ModernMessageBox.error(self, "❌ Error de Impresión",
                f"No se pudo imprimir la página de prueba.\n\n{msg}\n\n"
                "Verifica que la impresora esté encendida, conectada y configurada correctamente."
            )

    def _load_settings(self):
        """Lee la configuración desde la BD y la muestra en los campos."""
        settings = self.db.get_all_configs()
        self._nombre.setText(settings.get("business_name", app_config.BUSINESS_NAME))
        self._slogan.setText(settings.get("business_slogan", app_config.BUSINESS_SLOGAN))
        self._telefono.setText(settings.get("business_phone", app_config.BUSINESS_PHONE))
        self._direccion.setText(settings.get("business_address", app_config.BUSINESS_ADDRESS))
        self._moneda.setText(settings.get("currency_symbol", app_config.CURRENCY_SYMBOL))
        tax = float(settings.get("tax_rate", app_config.TAX_RATE))
        self._tax.setValue(tax * 100)

        # Printer settings
        self._refresh_printers()
        printer_name = settings.get("printer_name", app_config.PRINTER_NAME)
        if printer_name:
            for i in range(self._printer_combo.count()):
                if self._printer_combo.itemData(i) == printer_name:
                    self._printer_combo.setCurrentIndex(i)
                    break
        self._auto_cut.setChecked(
            settings.get("printer_auto_cut", "1") == "1"
        )
        pw = int(settings.get("printer_paper_width", app_config.PRINTER_PAPER_WIDTH))
        for i in range(self._paper_width.count()):
            if self._paper_width.itemData(i) == pw:
                self._paper_width.setCurrentIndex(i)
                break
        cp = settings.get("printer_codepage", app_config.PRINTER_CODEPAGE)
        for i in range(self._codepage.count()):
            if self._codepage.itemData(i) == cp:
                self._codepage.setCurrentIndex(i)
                break

        self._printer_qr.setChecked(
            settings.get("printer_print_qr", "1") == "1"
        )

        self._printer_pdf.setChecked(
            settings.get("printer_save_pdf", "1") == "1"
        )

    def _save(self):
        """Guarda la configuración en BD y actualiza las variables globales de config.py."""
        # Leer valores
        nombre = self._nombre.text().strip()
        slogan = self._slogan.text().strip()
        telefono = self._telefono.text().strip()
        direccion = self._direccion.text().strip()
        moneda = self._moneda.text().strip() or "$"
        tax = self._tax.value() / 100.0

        # Printer settings
        printer_name = self._printer_combo.currentData() or ""
        auto_cut = "1" if self._auto_cut.isChecked() else "0"
        pw = str(self._paper_width.currentData())
        cp = self._codepage.currentData()
        print_qr = "1" if self._printer_qr.isChecked() else "0"
        save_pdf = "1" if self._printer_pdf.isChecked() else "0"

        # Guardar en BD
        self.db.set_config("business_name", nombre)
        self.db.set_config("business_slogan", slogan)
        self.db.set_config("business_phone", telefono)
        self.db.set_config("business_address", direccion)
        self.db.set_config("currency_symbol", moneda)
        self.db.set_config("tax_rate", str(tax))
        self.db.set_config("printer_name", printer_name)
        self.db.set_config("printer_auto_cut", auto_cut)
        self.db.set_config("printer_paper_width", pw)
        self.db.set_config("printer_codepage", cp)
        self.db.set_config("printer_print_qr", print_qr)
        self.db.set_config("printer_save_pdf", save_pdf)

        # Actualizar variables globales (efecto inmediato)
        app_config.BUSINESS_NAME = nombre
        app_config.BUSINESS_SLOGAN = slogan
        app_config.BUSINESS_PHONE = telefono
        app_config.BUSINESS_ADDRESS = direccion
        app_config.CURRENCY_SYMBOL = moneda
        app_config.TAX_RATE = tax
        app_config.PRINTER_NAME = printer_name
        app_config.PRINTER_AUTO_CUT = auto_cut == "1"
        app_config.PRINTER_PAPER_WIDTH = int(pw)
        app_config.PRINTER_CODEPAGE = cp
        app_config.PRINTER_PRINT_QR = print_qr == "1"
        app_config.PRINTER_SAVE_PDF = save_pdf == "1"

        ModernMessageBox.success(
            self,
            "Configuración Guardada",
            "Los ajustes han sido guardados correctamente.\n"
            "Los cambios se aplican de inmediato."
        )

    def _reset_defaults(self):
        """Restaura los valores por defecto de config.py."""
        defaults = {
            "business_name": app_config.BUSINESS_NAME,
            "business_slogan": app_config.BUSINESS_SLOGAN,
            "business_phone": app_config.BUSINESS_PHONE,
            "business_address": app_config.BUSINESS_ADDRESS,
            "currency_symbol": app_config.CURRENCY_SYMBOL,
            "tax_rate": str(app_config.TAX_RATE),
            "printer_name": app_config.PRINTER_NAME,
            "printer_auto_cut": "1" if app_config.PRINTER_AUTO_CUT else "0",
            "printer_paper_width": str(app_config.PRINTER_PAPER_WIDTH),
            "printer_codepage": app_config.PRINTER_CODEPAGE,
            "printer_print_qr": "1" if app_config.PRINTER_PRINT_QR else "0",
            "printer_save_pdf": "1" if app_config.PRINTER_SAVE_PDF else "0",
        }
        for clave, valor in defaults.items():
            self.db.set_config(clave, valor)
        self._load_settings()
        
        # También actualizar variables globales
        app_config.BUSINESS_NAME = defaults["business_name"]
        app_config.BUSINESS_SLOGAN = defaults["business_slogan"]
        app_config.BUSINESS_PHONE = defaults["business_phone"]
        app_config.BUSINESS_ADDRESS = defaults["business_address"]
        app_config.CURRENCY_SYMBOL = defaults["currency_symbol"]
        app_config.TAX_RATE = float(defaults["tax_rate"])
        app_config.PRINTER_NAME = defaults["printer_name"]
        app_config.PRINTER_AUTO_CUT = defaults["printer_auto_cut"] == "1"
        app_config.PRINTER_PAPER_WIDTH = int(defaults["printer_paper_width"])
        app_config.PRINTER_CODEPAGE = defaults["printer_codepage"]
        app_config.PRINTER_PRINT_QR = defaults["printer_print_qr"] == "1"
        app_config.PRINTER_SAVE_PDF = defaults["printer_save_pdf"] == "1"
        
        ModernMessageBox.information(self, "Valores Restaurados", "Se han restaurado los valores por defecto.")
