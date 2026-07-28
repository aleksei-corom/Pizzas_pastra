"""Widgets de gráficos reutilizables para el Dashboard usando QtCharts."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt, QMargins
from PySide6.QtGui import QPainter, QFont, QColor, QPen

from PySide6.QtCharts import (
    QChart, QChartView,
    QBarSeries, QBarSet, QBarCategoryAxis,
    QPieSeries,
    QLineSeries, QValueAxis,
)

import config as app_config


# ─── Paleta de colores para gráficos ───
CHART_COLORS = [
    "#e63946",  # Rojo pizzeria
    "#f77f00",  # Naranja acento
    "#06d6a0",  # Verde éxito
    "#118ab2",  # Azul
    "#ffd166",  # Amarillo
    "#ef476f",  # Rosa
    "#8338ec",  # Púrpura
    "#ff6b6b",  # Rojo claro
    "#4ecdc4",  # Turquesa
    "#45b7d1",  # Azul claro
]


def _create_base_chart(title_text=""):
    """Crea un QChart con tema oscuro y configuración base."""
    chart = QChart()
    if title_text:
        chart.setTitle(title_text)
        chart.setTitleFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
    chart.setTheme(QChart.ChartTheme.ChartThemeDark)
    chart.setBackgroundBrush(QColor("#1e293b"))
    chart.setBackgroundRoundness(12)
    chart.setMargins(QMargins(0, 0, 0, 0))
    chart.layout().setContentsMargins(0, 0, 0, 0)
    chart.legend().setVisible(True)
    chart.legend().setFont(QFont("Segoe UI", 10))
    chart.legend().setLabelColor(QColor("#94a3b8"))
    chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
    return chart


def _create_chart_view(chart):
    """Crea un QChartView con anti-aliasing y fondo oscuro."""
    view = QChartView(chart)
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    view.setBackgroundBrush(QColor("#1e293b"))
    view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    return view


class SalesBarChart(QFrame):
    """Gráfico de barras para ventas por período."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        header = QVBoxLayout()
        header.setSpacing(4)

        title_lbl = QLabel("📊  Ventas por Día")
        title_lbl.setProperty("class", "card-title")
        header.addWidget(title_lbl)

        subtitle = QLabel("Últimos 7 días")
        subtitle.setProperty("class", "caption")
        header.addWidget(subtitle)
        layout.addLayout(header)

        self._chart = _create_base_chart()
        self._chart.legend().setVisible(False)
        self._chart.setMargins(QMargins(5, 5, 5, 5))

        self._view = _create_chart_view(self._chart)
        self._view.setMinimumHeight(200)
        layout.addWidget(self._view, 1)

    def set_data(self, labels, values):
        """Actualiza los datos del gráfico de barras."""
        self._chart.removeAllSeries()

        for axis in self._chart.axes():
            self._chart.removeAxis(axis)

        if not labels or not values:
            return

        bar_set = QBarSet("Ventas")
        for v in values:
            bar_set.append(v)

        bar_set.setColor(QColor("#e63946"))
        bar_set.setBorderColor(QColor("#c1121f"))

        series = QBarSeries()
        series.append(bar_set)
        series.setBarWidth(0.7)
        self._chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        axis_x.setLabelsColor(QColor("#94a3b8"))
        axis_x.setLabelsFont(QFont("Segoe UI", 9))
        axis_x.setGridLineColor(QColor("#334155"))
        axis_x.setLineVisible(False)
        self._chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        max_val = max(values) if values else 1
        axis_y = QValueAxis()
        axis_y.setRange(0, max_val * 1.2)
        axis_y.setLabelsColor(QColor("#94a3b8"))
        axis_y.setLabelsFont(QFont("Segoe UI", 9))
        axis_y.setGridLineColor(QColor("#334155"))
        axis_y.setLineVisible(False)
        axis_y.setLabelFormat(f"{app_config.CURRENCY_SYMBOL}%.0f")
        self._chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)


class OrderDonutChart(QFrame):
    """Gráfico de dona para distribución de órdenes / métricas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        title_lbl = QLabel("🍽️  Distribución de Órdenes")
        title_lbl.setProperty("class", "card-title")
        layout.addWidget(title_lbl)

        self._chart = _create_base_chart()
        self._chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        self._chart.legend().setFont(QFont("Segoe UI", 10))
        self._chart.setMargins(QMargins(5, 5, 5, 5))

        self._series = QPieSeries()
        self._series.setHoleSize(0.55)  # Donut
        self._chart.addSeries(self._series)

        self._view = _create_chart_view(self._chart)
        self._view.setMinimumHeight(200)
        layout.addWidget(self._view, 1)

        self._total_lbl = QLabel("")
        self._total_lbl.setProperty("class", "caption")
        self._total_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._total_lbl)

    def set_data(self, labels, values):
        """Actualiza los datos del gráfico donut."""
        self._series.clear()

        if not labels or not values:
            return

        total = sum(values)
        self._total_lbl.setText(f"Total: {total} órdenes")

        for i, (label, value) in enumerate(zip(labels, values)):
            if value <= 0:
                continue
            pct = (value / total * 100) if total > 0 else 0
            slice_ = self._series.append(f"{label}  ({pct:.0f}%)", value)
            slice_.setColor(QColor(CHART_COLORS[i % len(CHART_COLORS)]))
            slice_.setLabelVisible(True)
            slice_.setLabelColor(QColor("#f1f5f9"))
            slice_.setLabelFont(QFont("Segoe UI", 9))
            slice_.setExplodeDistanceFactor(0.05)


class MiniTrendChart(QFrame):
    """Mini gráfico de línea para tendencia de ventas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card-light")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        self._value_lbl = QLabel("$0")
        self._value_lbl.setProperty("class", "title")
        layout.addWidget(self._value_lbl)

        header = QVBoxLayout()
        header.setSpacing(0)
        self._label_lbl = QLabel("Tendencia")
        self._label_lbl.setProperty("class", "caption")
        header.addWidget(self._label_lbl)
        self._change_lbl = QLabel("")
        self._change_lbl.setProperty("class", "caption")
        header.addWidget(self._change_lbl)
        layout.addLayout(header)

        self._chart = QChart()
        self._chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self._chart.setBackgroundBrush(QColor("transparent"))
        self._chart.setMargins(QMargins(0, 0, 0, 0))
        self._chart.layout().setContentsMargins(0, 0, 0, 0)
        self._chart.legend().setVisible(False)

        self._series = QLineSeries()
        self._series.setPen(QPen(QColor("#06d6a0"), 2))
        self._chart.addSeries(self._series)

        self._view = _create_chart_view(self._chart)
        self._view.setFixedHeight(60)
        layout.addWidget(self._view)

    def set_data(self, values, label="", value_text="", change_text=""):
        """Actualiza los datos del minigráfico de tendencia."""
        if label:
            self._label_lbl.setText(label)
        if value_text:
            self._value_lbl.setText(value_text)
        if change_text:
            self._change_lbl.setText(change_text)
            is_positive = "+" in change_text
            self._change_lbl.setStyleSheet(
                f"color: #34d399;" if is_positive else "color: #f87171;"
            )

        self._series.clear()
        if not values:
            return

        for i, v in enumerate(values):
            self._series.append(i, v)

        max_v = max(values) if values else 1
        min_v = min(values) if values else 0
        padding = (max_v - min_v) * 0.2 or max_v * 0.2

        for axis in self._chart.axes():
            self._chart.removeAxis(axis)

        axis_x = QValueAxis()
        axis_x.setRange(0, len(values) - 1)
        axis_x.setVisible(False)
        axis_x.setLabelsVisible(False)
        axis_x.setGridLineVisible(False)
        self._chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        self._series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(max(0, min_v - padding), max_v + padding)
        axis_y.setVisible(False)
        axis_y.setLabelsVisible(False)
        axis_y.setGridLineVisible(False)
        self._chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        self._series.attachAxis(axis_y)
