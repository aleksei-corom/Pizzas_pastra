"""Vista Reportes — Estadísticas de ventas."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QPushButton,
)
from PySide6.QtCore import Qt
from datetime import datetime, timedelta

from database.orden_service import OrdenService
import logging
from database.producto_service import ProductoService
import config as app_config
from views.layouts import create_page_header


class ReportesView(QWidget):
    """Vista de reportes con métricas de ventas y análisis."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.orden_svc = OrdenService()
        self.prod_svc = ProductoService()
        self._periodo = 7
        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        # Header
        layout.addLayout(create_page_header(
            "📈  Reportes de Ventas",
            "Análisis y estadísticas de tu negocio"
        ))

        # Selector de período
        period_row = QHBoxLayout()
        period_row.setSpacing(8)
        self._period_buttons = []
        for label, days in [("Hoy", 1), ("7 Días", 7), ("30 Días", 30)]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(days == self._periodo)
            btn.setFixedHeight(36)
            btn.setProperty("class", "period-button")
            btn.clicked.connect(lambda checked, d=days: self._set_periodo(d))
            self._period_buttons.append((btn, days))
            period_row.addWidget(btn)
        period_row.addStretch()
        layout.addLayout(period_row)

        # Tarjetas de resumen
        self._stats_row = QHBoxLayout()
        self._stats_row.setSpacing(16)

        self._card_total_ventas = self._create_metric_card("💰", "Total Ventas", "$0.00")
        self._card_total_ordenes = self._create_metric_card("📦", "Total Órdenes", "0")
        self._card_ticket_prom = self._create_metric_card("🎫", "Ticket Promedio", "$0.00")
        self._card_producto_top = self._create_metric_card("🏆", "Más Vendido", "-")

        self._stats_row.addWidget(self._card_total_ventas)
        self._stats_row.addWidget(self._card_total_ordenes)
        self._stats_row.addWidget(self._card_ticket_prom)
        self._stats_row.addWidget(self._card_producto_top)
        layout.addLayout(self._stats_row)

        # Tablas: Ventas por día + Top productos
        tables_row = QHBoxLayout()
        tables_row.setSpacing(20)

        # Ventas por día
        daily_card = QFrame()
        daily_card.setProperty("class", "card")
        daily_layout = QVBoxLayout(daily_card)
        daily_layout.setContentsMargins(20, 16, 20, 16)
        daily_layout.setSpacing(12)

        daily_title = QLabel("📅  Ventas por Día")
        daily_title.setProperty("class", "card-title")
        daily_layout.addWidget(daily_title)

        self._daily_table = QTableWidget(0, 3)
        self._daily_table.setHorizontalHeaderLabels(["Fecha", "Órdenes", "Ventas"])
        self._daily_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._daily_table.verticalHeader().setVisible(False)
        self._daily_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._daily_table.setAlternatingRowColors(True)
        daily_layout.addWidget(self._daily_table)

        tables_row.addWidget(daily_card, 1)

        # Top productos
        top_card = QFrame()
        top_card.setProperty("class", "card")
        top_layout = QVBoxLayout(top_card)
        top_layout.setContentsMargins(20, 16, 20, 16)
        top_layout.setSpacing(12)

        top_title = QLabel("🏆  Productos Más Vendidos")
        top_title.setProperty("class", "card-title")
        top_layout.addWidget(top_title)

        self._top_table = QTableWidget(0, 3)
        self._top_table.setHorizontalHeaderLabels(["Producto", "Cantidad", "Ingresos"])
        self._top_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._top_table.verticalHeader().setVisible(False)
        self._top_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._top_table.setAlternatingRowColors(True)
        top_layout.addWidget(self._top_table)

        tables_row.addWidget(top_card, 1)
        layout.addLayout(tables_row)
        layout.addStretch()

    def _create_metric_card(self, icon, label, value):
        card = QFrame()
        card.setProperty("class", "card")
        lo = QVBoxLayout(card)
        lo.setContentsMargins(20, 16, 20, 16)
        lo.setSpacing(8)

        i = QLabel(icon)
        i.setProperty("class", "metric-icon")
        lo.addWidget(i)

        v = QLabel(value)
        v.setObjectName("metricValue")
        v.setProperty("class", "title")
        lo.addWidget(v)

        l = QLabel(label)
        l.setProperty("class", "caption")
        lo.addWidget(l)

        return card

    def _update_metric(self, card, value):
        lbl = card.findChild(QLabel, "metricValue")
        if lbl:
            lbl.setText(str(value))

    def _set_periodo(self, dias):
        self._periodo = dias
        # Actualizar estado de todos los botones
        for btn, d in self._period_buttons:
            btn.setChecked(d == dias)
        self.cargar_datos()

    def cargar_datos(self):
        try:
            # Ventas por día
            ventas = self.orden_svc.get_ventas_por_periodo(self._periodo)
            total_ventas = sum(d.get("ventas", 0) for d in ventas)
            total_ordenes = sum(d.get("ordenes", 0) for d in ventas)
            ticket_prom = total_ventas / total_ordenes if total_ordenes else 0

            self._update_metric(self._card_total_ventas, f"{app_config.CURRENCY_SYMBOL}{total_ventas:.2f}")
            self._update_metric(self._card_total_ordenes, str(total_ordenes))
            self._update_metric(self._card_ticket_prom, f"{app_config.CURRENCY_SYMBOL}{ticket_prom:.2f}")

            # Tabla ventas por día
            self._daily_table.setRowCount(len(ventas))
            for i, d in enumerate(ventas):
                self._daily_table.setItem(i, 0, QTableWidgetItem(d.get("fecha", "")))
                self._daily_table.setItem(i, 1, QTableWidgetItem(str(d.get("ordenes", 0))))
                self._daily_table.setItem(i, 2, QTableWidgetItem(f"{app_config.CURRENCY_SYMBOL}{d.get('ventas', 0):.2f}"))

            # Top productos
            top = self.prod_svc.get_productos_populares(limit=10)
            self._top_table.setRowCount(len(top))
            for i, p in enumerate(top):
                self._top_table.setItem(i, 0, QTableWidgetItem(p.get("producto_nombre", "")))
                self._top_table.setItem(i, 1, QTableWidgetItem(str(int(p.get("total_cantidad", 0)))))
                self._top_table.setItem(i, 2, QTableWidgetItem(f"{app_config.CURRENCY_SYMBOL}{p.get('total_ventas', 0):.2f}"))

            if top:
                self._update_metric(self._card_producto_top, top[0].get("producto_nombre", "-"))
            else:
                self._update_metric(self._card_producto_top, "Sin datos")

        except Exception as e:
            logging.getLogger(__name__).error("Error cargando reportes: %s", e, exc_info=True)
