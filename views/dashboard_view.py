"""Vista Dashboard — Resumen del día con gráficos visuales y métricas."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Qt
from datetime import datetime, timedelta

from database.orden_service import OrdenService
from database.producto_service import ProductoService
import config as app_config
from views.layouts import create_page_header, create_stats_grid
from views.components import CardWidget, StatusBadge
from views.components.chart_widgets import (
    SalesBarChart, OrderDonutChart, MiniTrendChart,
)


class DashboardView(QWidget):
    """Vista principal del dashboard con métricas, gráficos y tabla de órdenes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.orden_svc = OrdenService()
        self.prod_svc = ProductoService()
        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Header
        now = datetime.now()
        greeting = "Buenos días" if now.hour < 12 else "Buenas tardes" if now.hour < 18 else "Buenas noches"
        header_layout = create_page_header(
            f"{greeting} 👋",
            f"Resumen del {now.strftime('%d/%m/%Y')} — {app_config.APP_NAME}"
        )
        layout.addLayout(header_layout)

        # ─── Fila 1: Stats Cards + Mini Trends ───
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        self._stats_layout = QHBoxLayout()
        row1.addLayout(self._stats_layout, 3)

        # Mini trend charts (ventas últimas horas)
        self._mini_trend = MiniTrendChart()
        self._mini_trend.setMinimumWidth(180)
        row1.addWidget(self._mini_trend, 1)

        layout.addLayout(row1)

        # ─── Fila 2: Gráficos ───
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        # Bar chart de ventas semanales
        self._bar_chart = SalesBarChart()
        row2.addWidget(self._bar_chart, 3)

        # Donut chart de distribución
        self._donut_chart = OrderDonutChart()
        row2.addWidget(self._donut_chart, 2)

        layout.addLayout(row2)

        # ─── Fila 3: Últimas órdenes + Top productos ───
        row3 = QHBoxLayout()
        row3.setSpacing(20)

        # Últimas órdenes
        orders_card = CardWidget(title="📋  Últimas Órdenes")
        self._orders_table = QTableWidget(0, 5)
        self._orders_table.setHorizontalHeaderLabels(["#", "Tipo", "Estado", "Total", "Hora"])
        self._orders_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._orders_table.verticalHeader().setVisible(False)
        self._orders_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._orders_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._orders_table.setAlternatingRowColors(True)
        self._orders_table.setMaximumHeight(300)
        orders_card.add_widget(self._orders_table)
        row3.addWidget(orders_card, 2)

        # Top productos
        top_card = CardWidget(title="🏆  Más Vendidos")
        self._top_container = QVBoxLayout()
        self._top_container.setSpacing(8)
        top_card.add_layout(self._top_container)
        row3.addWidget(top_card, 1)

        layout.addLayout(row3)
        layout.addStretch()

    def cargar_datos(self):
        """Recarga todas las métricas y gráficos del dashboard."""
        try:
            hoy = datetime.now().strftime("%Y-%m-%d")
            ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

            ventas_hoy = self.orden_svc.get_ventas_dia(hoy)
            ventas_ayer = self.orden_svc.get_ventas_dia(ayer)

            total_ordenes = ventas_hoy.get("total_ordenes", 0)
            total_ventas = ventas_hoy.get("total_ventas", 0)
            ordenes_ayer = ventas_ayer.get("total_ordenes", 0)
            ventas_ayer_val = ventas_ayer.get("total_ventas", 0)

            # ─── Calcular tendencias ───
            trend_ventas = ""
            if ventas_ayer_val > 0:
                cambio = ((total_ventas - ventas_ayer_val) / ventas_ayer_val) * 100
                trend_ventas = f"{'+' if cambio >= 0 else ''}{cambio:.0f}%"

            trend_ordenes = ""
            if ordenes_ayer > 0:
                cambio_o = ((total_ordenes - ordenes_ayer) / ordenes_ayer) * 100
                trend_ordenes = f"{'+' if cambio_o >= 0 else ''}{cambio_o:.0f}%"

            ticket_promedio = total_ventas / total_ordenes if total_ordenes > 0 else 0

            productos = self.prod_svc.get_productos()
            disponibles = len([p for p in productos if p.disponible])

            # ─── Actualizar stats cards ───
            stats_data = [
                {'label': 'Ventas del Día', 'value': f"{app_config.CURRENCY_SYMBOL}{total_ventas:.2f}", 'badge': trend_ventas, 'status': 'success' if trend_ventas.startswith('+') else 'danger'},
                {'label': 'Órdenes Hoy', 'value': str(total_ordenes), 'badge': trend_ordenes, 'status': 'success' if trend_ordenes.startswith('+') else 'danger'},
                {'label': 'Ticket Promedio', 'value': f"{app_config.CURRENCY_SYMBOL}{ticket_promedio:.2f}"},
                {'label': 'Productos Activos', 'value': str(disponibles)},
            ]
            while self._stats_layout.count():
                child = self._stats_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            stats_grid = create_stats_grid(stats_data)
            while stats_grid.count():
                item = stats_grid.takeAt(0)
                if item.widget():
                    self._stats_layout.addWidget(item.widget())

            # ─── Mini Trend Chart ───
            # Datos de ventas de los últimos 7 días para tendencia
            ventas_periodo = self.orden_svc.get_ventas_por_periodo(7)
            trend_values = [d.get("ventas", 0) for d in ventas_periodo]
            # Determinar cambio vs día anterior
            cambio_trend = ""
            if len(trend_values) >= 2:
                diff = trend_values[-1] - trend_values[-2]
                if diff > 0:
                    cambio_trend = f"+{app_config.CURRENCY_SYMBOL}{diff:.0f} vs ayer"
                elif diff < 0:
                    cambio_trend = f"-{app_config.CURRENCY_SYMBOL}{abs(diff):.0f} vs ayer"
                else:
                    cambio_trend = "Sin cambio vs ayer"
            self._mini_trend.set_data(
                trend_values,
                label="Tendencia últimos 7 días",
                value_text=f"{app_config.CURRENCY_SYMBOL}{total_ventas:.0f}",
                change_text=cambio_trend,
            )

            # ─── Bar Chart de Ventas Semanales ───
            if ventas_periodo:
                labels = []
                values = []
                for d in ventas_periodo:
                    fecha = d.get("fecha", "")
                    if len(fecha) >= 10:
                        # Mostrar día/mes abreviado
                        fecha_dt = datetime.strptime(fecha[:10], "%Y-%m-%d")
                        labels.append(fecha_dt.strftime("%d/%m"))
                    else:
                        labels.append(fecha)
                    values.append(d.get("ventas", 0))
                self._bar_chart.set_data(labels, values)

            # ─── Donut Chart de Distribución ───
            conteo_estados = self.orden_svc.get_conteo_por_estado()
            if conteo_estados:
                labels_estados = []
                values_estados = []
                for estado_key, count in conteo_estados.items():
                    labels_estados.append(app_config.ORDER_STATUS.get(estado_key, estado_key))
                    values_estados.append(count)
                self._donut_chart.set_data(labels_estados, values_estados)

            # ─── Últimas órdenes ───
            ordenes = self.orden_svc.get_ordenes(limit=10)
            self._orders_table.setRowCount(len(ordenes))
            for i, orden in enumerate(ordenes):
                self._orders_table.setItem(i, 0, QTableWidgetItem(orden.numero))
                tipo_text = {"local": "🍽️ Local", "takeout": "🛍️ Llevar", "delivery": "🛵 Delivery"}.get(orden.tipo, orden.tipo)
                self._orders_table.setItem(i, 1, QTableWidgetItem(tipo_text))
                estado_text = app_config.ORDER_STATUS.get(orden.estado, orden.estado)
                self._orders_table.setItem(i, 2, QTableWidgetItem(estado_text))
                self._orders_table.setItem(i, 3, QTableWidgetItem(f"{app_config.CURRENCY_SYMBOL}{orden.total:.2f}"))
                hora = orden.fecha_creacion[11:16] if len(orden.fecha_creacion) > 16 else ""
                self._orders_table.setItem(i, 4, QTableWidgetItem(hora))

            # ─── Top productos ───
            while self._top_container.count():
                child = self._top_container.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            top_prods = self.prod_svc.get_productos_populares(limit=5)
            for i, prod in enumerate(top_prods):
                row = QFrame()
                row.setProperty("class", "card-light")
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(12, 8, 12, 8)

                rank = QLabel(f"#{i+1}")
                rank.setProperty("class", "badge-info")
                rank.setFixedWidth(32)
                row_layout.addWidget(rank)

                name = QLabel(prod["producto_nombre"])
                row_layout.addWidget(name, 1)

                qty = QLabel(f"{int(prod['total_cantidad'])} uds")
                qty.setProperty("class", "caption")
                row_layout.addWidget(qty)

                self._top_container.addWidget(row)

            if not top_prods:
                empty = QLabel("Sin datos aún")
                empty.setProperty("class", "caption")
                empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._top_container.addWidget(empty)

        except Exception as e:
            print(f"Error cargando dashboard: {e}")
