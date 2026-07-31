"""Vista CRM & Fidelización — Gestión de clientes, puntos y premios.

Módulo diferenciador que permite:
- Búsqueda rápida de clientes por teléfono (útil en POS)
- Registro de clientes con programa de puntos
- Historial de puntos y movimientos
- Gestión de premios canjeables
- Top clientes por gasto
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStackedWidget, QFrame, QTabWidget, QDialog, QLineEdit,
)
from PySide6.QtCore import Qt

from database.cliente_service import ClienteService
from database.producto_service import ProductoService
from views.layouts import create_page_header, create_stats_grid
from views.components import CardWidget, StatusBadge, ModernMessageBox
from views.components.search_bar import SearchBar
from views.components.cliente_dialog import ClienteDialog
from views.components.premio_dialog import PremioDialog
import config as app_config


class ClientesView(QWidget):
    """Vista de gestión de clientes con tabs: Directorio / Puntos / Premios."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._svc = ClienteService()
        self._prod_svc = ProductoService()
        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        btn_nuevo = QPushButton("+ Nuevo Cliente")
        btn_nuevo.clicked.connect(self._nuevo_cliente)
        header = create_page_header(
            "💎  Clientes & Fidelización",
            "Programa de lealtad y gestión de clientes",
            actions=[btn_nuevo]
        )
        layout.addLayout(header)

        self._stats_layout = QHBoxLayout()
        layout.addLayout(self._stats_layout)

        self._tabs = QTabWidget()
        self._tabs.setObjectName("main-tabs")

        self._tab_directorio = QWidget()
        self._build_tab_directorio()
        self._tabs.addTab(self._tab_directorio, "📋  Directorio")

        self._tab_puntos = QWidget()
        self._build_tab_puntos()
        self._tabs.addTab(self._tab_puntos, "⭐  Puntos")

        self._tab_premios = QWidget()
        self._build_tab_premios()
        self._tabs.addTab(self._tab_premios, "⭐  Premios")

        layout.addWidget(self._tabs, 1)

    def _build_tab_directorio(self):
        layout = QVBoxLayout(self._tab_directorio)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        search_row = QHBoxLayout()
        self._search = SearchBar("Buscar por nombre, teléfono o email...")
        self._search.textChanged.connect(self._on_search)
        search_row.addWidget(self._search, 1)

        btn_buscar_tel = QPushButton("📞  Búsqueda rápida")
        btn_buscar_tel.setProperty("class", "secondary")
        btn_buscar_tel.setToolTip("Busca un cliente por teléfono para asociar a una orden")
        btn_buscar_tel.clicked.connect(self._busqueda_rapida)
        search_row.addWidget(btn_buscar_tel)

        layout.addLayout(search_row)

        self._tabla = QTableWidget(0, 7)
        self._tabla.setHorizontalHeaderLabels([
            "Nombre", "Teléfono", "Puntos", "Visitas",
            "Total Gastado", "Última Visita", ""
        ])
        self._tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._tabla.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._tabla.setColumnWidth(6, 80)
        self._tabla.verticalHeader().setVisible(False)
        self._tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabla.setAlternatingRowColors(True)
        self._tabla.cellClicked.connect(self._on_row_clicked)
        layout.addWidget(self._tabla, 1)

    def _build_tab_puntos(self):
        layout = QVBoxLayout(self._tab_puntos)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        self._cliente_info = QFrame()
        self._cliente_info.setProperty("class", "card")
        self._cliente_info_layout = QVBoxLayout(self._cliente_info)
        self._cliente_info_layout.setContentsMargins(20, 16, 20, 16)

        self._lbl_cliente_nombre = QLabel("Selecciona un cliente del directorio")
        self._lbl_cliente_nombre.setProperty("class", "title")
        self._cliente_info_layout.addWidget(self._lbl_cliente_nombre)

        self._cliente_stats_row = QHBoxLayout()
        self._cliente_info_layout.addLayout(self._cliente_stats_row)
        layout.addWidget(self._cliente_info)

        lbl_hist = QLabel("📋  Historial de Movimientos")
        lbl_hist.setProperty("class", "section")
        layout.addWidget(lbl_hist)

        self._tabla_puntos = QTableWidget(0, 5)
        self._tabla_puntos.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "Puntos", "Saldo", "Concepto"
        ])
        self._tabla_puntos.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._tabla_puntos.verticalHeader().setVisible(False)
        self._tabla_puntos.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla_puntos.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabla_puntos.setAlternatingRowColors(True)
        self._tabla_puntos.setMaximumHeight(300)
        layout.addWidget(self._tabla_puntos, 1)

    def _build_tab_premios(self):
        layout = QVBoxLayout(self._tab_premios)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        premios_row = QHBoxLayout()
        lbl_premios = QLabel("⭐  Catálogo de Premios")
        lbl_premios.setProperty("class", "section")
        premios_row.addWidget(lbl_premios)
        premios_row.addStretch()

        btn_nuevo_premio = QPushButton("+ Nuevo Premio")
        btn_nuevo_premio.clicked.connect(self._nuevo_premio)
        premios_row.addWidget(btn_nuevo_premio)
        layout.addLayout(premios_row)

        self._tabla_premios = QTableWidget(0, 4)
        self._tabla_premios.setHorizontalHeaderLabels([
            "Premio", "Descripción", "Puntos Req.", ""
        ])
        self._tabla_premios.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._tabla_premios.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._tabla_premios.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._tabla_premios.setColumnWidth(3, 80)
        self._tabla_premios.verticalHeader().setVisible(False)
        self._tabla_premios.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla_premios.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabla_premios.setAlternatingRowColors(True)
        layout.addWidget(self._tabla_premios, 1)

    def cargar_datos(self):
        self._load_stats()
        self._load_clientes()
        self._load_premios()

    def _load_stats(self):
        stats = self._svc.get_stats_fidelizacion()
        stats_data = [
            {'label': 'Total Clientes', 'value': str(stats['total_clientes']),
             'badge': f"+{stats['nuevos_hoy']} hoy" if stats['nuevos_hoy'] > 0 else None,
             'status': 'success'},
            {'label': 'Puntos Activos', 'value': f"{stats['puntos_activos']:,}",
             'status': 'info'},
            {'label': 'Puntos Canjeados', 'value': f"{stats['total_canjeados']:,}",
             'status': 'warning'},
            {'label': 'Ratio Canje', 'value': self._calc_ratio(stats),
             'status': 'info'},
        ]
        while self._stats_layout.count():
            child = self._stats_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        from views.layouts import create_stats_grid
        stats_grid = create_stats_grid(stats_data)
        while stats_grid.count():
            item = stats_grid.takeAt(0)
            if item.widget():
                self._stats_layout.addWidget(item.widget())

    def _calc_ratio(self, stats):
        total = stats['puntos_activos'] + stats['total_canjeados']
        if total == 0:
            return "0%"
        return f"{stats['total_canjeados'] / total * 100:.0f}%"

    def _load_clientes(self, busqueda=""):
        clientes = self._svc.get_clientes(busqueda=busqueda)
        self._tabla.setRowCount(len(clientes))
        for i, c in enumerate(clientes):
            self._tabla.setItem(i, 0, QTableWidgetItem(c.nombre))
            self._tabla.setItem(i, 1, QTableWidgetItem(c.telefono))
            self._tabla.setItem(i, 2, QTableWidgetItem(f"{c.puntos:,} pts"))
            self._tabla.setItem(i, 3, QTableWidgetItem(str(c.visitas)))
            self._tabla.setItem(i, 4, QTableWidgetItem(
                f"{app_config.CURRENCY_SYMBOL}{c.total_gastado:.2f}"
            ))
            ultima = c.ultima_visita[5:16] if c.ultima_visita else "Nunca"
            self._tabla.setItem(i, 5, QTableWidgetItem(ultima))

            btn_edit = QPushButton("✉")
            btn_edit.setProperty("class", "ghost")
            btn_edit.setFixedWidth(50)
            btn_edit.clicked.connect(lambda checked, cid=c.id: self._editar_cliente(cid))
            self._tabla.setCellWidget(i, 6, btn_edit)

    def _load_premios(self):
        premios = self._svc.get_premios()
        self._tabla_premios.setRowCount(len(premios))
        for i, p in enumerate(premios):
            self._tabla_premios.setItem(i, 0, QTableWidgetItem(p.nombre))
            desc = p.descripcion
            if p.descuento_porcentaje > 0:
                desc += f" ({p.descuento_porcentaje:.0f}% desc.)"
            if p.producto_gratis_id:
                desc += " (Producto gratis)"
            self._tabla_premios.setItem(i, 1, QTableWidgetItem(desc))
            self._tabla_premios.setItem(i, 2, QTableWidgetItem(f"{p.puntos_requeridos:,} pts"))

            btn_del = QPushButton("✖")
            btn_del.setProperty("class", "danger-ghost")
            btn_del.setFixedWidth(50)
            btn_del.clicked.connect(lambda checked, pid=p.id: self._eliminar_premio(pid))
            self._tabla_premios.setCellWidget(i, 3, btn_del)

    def _load_puntos_cliente(self, cliente_id):
        cliente = self._svc.get_cliente(cliente_id)
        if not cliente:
            return

        self._lbl_cliente_nombre.setText(
            f"👤  {cliente.nombre}  —  {cliente.puntos:,} puntos"
        )

        while self._cliente_stats_row.count():
            child = self._cliente_stats_row.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        stat_labels = [
            (f"{app_config.CURRENCY_SYMBOL}{cliente.total_gastado:.2f}", "Total Gastado"),
            (str(cliente.visitas), "Visitas"),
            (f"{cliente.puntos:,}", "Puntos"),
        ]
        for val, label in stat_labels:
            stat_card = CardWidget(title=val, subtitle=label, padding=12)
            self._cliente_stats_row.addWidget(stat_card)
        self._cliente_stats_row.addStretch()

        movs = self._svc.get_historial_puntos(cliente_id)
        self._tabla_puntos.setRowCount(len(movs))
        for i, m in enumerate(movs):
            fecha = m.fecha[5:16] if m.fecha else ""
            self._tabla_puntos.setItem(i, 0, QTableWidgetItem(fecha))

            tipo_map = {
                "acumulado": ("✅ Acumulado", "success"),
                "canjeado": ("📦 Canjeado", "danger"),
                "bono_cumpleanos": ("🎉 Bono", "warning"),
                "ajuste": ("⚙️ Ajuste", "info"),
            }
            tipo_text, tipo_status = tipo_map.get(m.tipo, (m.tipo, "info"))
            self._tabla_puntos.setItem(i, 1, QTableWidgetItem(tipo_text))

            pts_text = f"+{m.puntos}" if m.tipo != "canjeado" else f"-{m.puntos}"
            self._tabla_puntos.setItem(i, 2, QTableWidgetItem(pts_text))
            self._tabla_puntos.setItem(i, 3, QTableWidgetItem(f"{m.saldo_nuevo:,}"))
            self._tabla_puntos.setItem(i, 4, QTableWidgetItem(m.concepto))

    def _on_search(self, text):
        self._load_clientes(busqueda=text)

    def _on_row_clicked(self, row, col):
        item = self._tabla.item(row, 0)
        if item:
            nombre = item.text()
            clientes = self._svc.get_clientes(busqueda=nombre)
            if clientes:
                self._load_puntos_cliente(clientes[0].id)
                self._tabs.setCurrentIndex(1)

    def _nuevo_cliente(self):
        dlg = ClienteDialog(parent=self)
        if dlg.exec():
            cliente = dlg.get_cliente()
            try:
                self._svc.crear_cliente(cliente)
                self.cargar_datos()
            except Exception as e:
                ModernMessageBox.error(self, "Error", f"No se pudo guardar: {e}")

    def _editar_cliente(self, cliente_id):
        cliente = self._svc.get_cliente(cliente_id)
        if not cliente:
            return
        dlg = ClienteDialog(cliente=cliente, parent=self)
        if dlg.exec():
            cliente = dlg.get_cliente()
            try:
                self._svc.actualizar_cliente(cliente)
                self.cargar_datos()
            except Exception as e:
                ModernMessageBox.error(self, "Error", f"No se pudo actualizar: {e}")

    def _busqueda_rapida(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("📞  Búsqueda Rápida por Teléfono")
        dlg.setMinimumWidth(350)
        lay = QVBoxLayout(dlg)
        lay.setSpacing(12)
        lay.setContentsMargins(20, 16, 20, 16)

        lbl = QLabel("Ingresa el número de teléfono del cliente:")
        lay.addWidget(lbl)

        tel_input = QLineEdit()
        tel_input.setPlaceholderText("Ej: 4120000000")
        tel_input.setMinimumHeight(40)
        lay.addWidget(tel_input)

        resultado = QLabel("")
        resultado.setProperty("class", "caption")
        resultado.setWordWrap(True)
        lay.addWidget(resultado)

        def buscar():
            tel = tel_input.text().strip()
            if not tel:
                return
            c = self._svc.buscar_por_telefono(tel)
            if c:
                resultado.setText(
                    f"✅ Encontrado: {c.nombre}\n"
                    f"Puntos: {c.puntos:,} | Visitas: {c.visitas} | "
                    f"Total: {app_config.CURRENCY_SYMBOL}{c.total_gastado:.2f}"
                )
                resultado.setStyleSheet("color: #34d399;")
            else:
                resultado.setText(
                    "❌ Cliente no encontrado. Regístralo desde 'Nuevo Cliente'."
                )
                resultado.setStyleSheet("color: #f87171;")

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_buscar = QPushButton("Buscar")
        btn_buscar.clicked.connect(buscar)
        btn_row.addWidget(btn_buscar)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setProperty("class", "secondary")
        btn_cerrar.clicked.connect(dlg.reject)
        btn_row.addWidget(btn_cerrar)
        lay.addLayout(btn_row)

        tel_input.returnPressed.connect(buscar)
        tel_input.setFocus()
        dlg.exec()

    def _nuevo_premio(self):
        productos = self._prod_svc.get_productos()
        dlg = PremioDialog(productos=productos, parent=self)
        if dlg.exec():
            premio = dlg.get_premio()
            try:
                self._svc.crear_premio(premio)
                self._load_premios()
            except Exception as e:
                ModernMessageBox.error(self, "Error", f"No se pudo crear: {e}")

    def _eliminar_premio(self, premio_id):
        from PySide6.QtWidgets import QDialog
        result = ModernMessageBox.question(
            self, "Eliminar Premio",
            "¿Estás seguro de eliminar este premio?"
        )
        if result == QDialog.DialogCode.Accepted:
            self._svc.eliminar_premio(premio_id)
            self._load_premios()
