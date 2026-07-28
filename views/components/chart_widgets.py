"""Widgets de gráficos reutilizables para el Dashboard usando QtCharts — theme-aware."""

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


def _get_theme_colors():
    """Retorna colores del tema activo para gráficos."""
    try:
        from views.themes.theme_helper import th, get_chart_colors, get_chart_bg
        return {
            'primary': th("primary"),
            'primary_hover': th("primary_hover"),
            'success': th("success"),
            'warning': th("warning"),
            'fg_muted': th("fg_muted"),
            'border': th("border"),
            'fg': th("fg"),
            'bg_card': th("bg_card"),
            'palette': get_chart_colors(),
        }
    except Exception:
        return {
            'primary': '#e63946', 'primary_hover': '#c1121f',
            'success': '#06d6a0', 'warning': '#ffd166',
            'fg_muted': '#94a3b8', 'border': '#334155',
            'fg': '#f1f5f9', 'bg_card': '#1e293b',
            'palette': ["#e63946", "#f77f00", "#06d6a0", "#118ab2", "#ffd166",
                        "#ef476f", "#8338ec", "#ff6b6b", "#4ecdc4", "#45b7d1"],
        }


_TC = _get_theme_colors()


def _get_font_family():
    """Retorna la familia de fuentes del tema o fallback."""
    try:
        from views.themes.theme_helper import th
        return "Segoe UI"
    except Exception:
        return "Segoe UI"


def _create_base_chart(title_text=""):
    """Crea un QChart con tema oscuro y configuración base."""
    chart = QChart()
    if title_text:
        chart.setTitle(title_text)
        chart.setTitleFont(QFont(_get_font_family(), 13, QFont.Weight.Bold))
    chart.setTheme(QChart.ChartTheme.ChartThemeDark)
    chart.setBackgroundBrush(QColor(_TC['bg_card']))
    chart.setBackgroundRoundness(12)
    chart.setMargins(QMargins(0, 0, 0, 0))
    chart.layout().setContentsMargins(0, 0, 0, 0)
    chart.legend().setVisible(True)
    chart.legend().setFont(QFont(_get_font_family(), 10))
    chart.legend().setLabelColor(QColor(_TC['fg_muted']))
    chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
    return chart


def _create_chart_view(chart):
    """Crea un QChartView con anti-aliasing y fondo del tema."""
    view = QChartView(chart)
    view.setRenderHint(QPainter.RenderHint.Antialiasing)
    view.setBackgroundBrush(QColor(_TC['bg_card']))
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

        title_lbl = QLabel("\U0001f4ca  Ventas por Día")
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

        # Colores del tema activo
        tc = _get_theme_colors()
        bar_set.setColor(QColor(tc['primary']))
        bar_set.setBorderColor(QColor(tc['primary_hover']))

        series = QBarSeries()
        series.append(bar_set)
        series.setBarWidth(0.7)
        self._chart.addSeries(series)

        axis_x = QBarCategoryAxis()
        axis_x.append(labels)
        axis_x.setLabelsColor(QColor(tc['fg_muted']))
        axis_x.setLabelsFont(QFont(_get_font_family(), 9))
        axis_x.setGridLineColor(QColor(tc['border']))
        axis_x.setLineVisible(False)
        self._chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        max_val = max(values) if values else 1
        axis_y = QValueAxis()
        axis_y.setRange(0, max_val * 1.2)
        axis_y.setLabelsColor(QColor(tc['fg_muted']))
        axis_y.setLabelsFont(QFont(_get_font_family(), 9))
        axis_y.setGridLineColor(QColor(tc['border']))
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

        title_lbl = QLabel("\U0001f37d\ufe0f  Distribución de Órdenes")
        title_lbl.setProperty("class", "card-title")
        layout.addWidget(title_lbl)

        self._chart = _create_base_chart()
        self._chart.legend().setAlignment(Qt.AlignmentFlag.AlignRight)
        self._chart.legend().setFont(QFont(_get_font_family(), 10))
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

        tc = _get_theme_colors()
        palette = tc['palette']

        for i, (label, value) in enumerate(zip(labels, values)):
            if value <= 0:
                continue
            pct = (value / total * 100) if total > 0 else 0
            slice_ = self._series.append(f"{label}  ({pct:.0f}%)", value)
            slice_.setColor(QColor(palette[i % len(palette)]))
            slice_.setLabelVisible(True)
            slice_.setLabelColor(QColor(tc['fg']))
            slice_.setLabelFont(QFont(_get_font_family(), 9))
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

        tc = _get_theme_colors()

        self._chart = QChart()
        self._chart.setTheme(QChart.ChartTheme.ChartThemeDark)
        self._chart.setBackgroundBrush(QColor("transparent"))
        self._chart.setMargins(QMargins(0, 0, 0, 0))
        self._chart.layout().setContentsMargins(0, 0, 0, 0)
        self._chart.legend().setVisible(False)

        self._series = QLineSeries()
        self._series.setPen(QPen(QColor(tc['success']), 2))
        self._chart.addSeries(self._series)

        self._view = _create_chart_view(self._chart)
        self._view.setFixedHeight(60)
        layout.addWidget(self._view)

    def set_data(self, values, label="", value_text="", change_text=""):
        """Actualiza los datos del minigráfico de tendencia."""
        tc = _get_theme_colors()
        if label:
            self._label_lbl.setText(label)
        if value_text:
            self._value_lbl.setText(value_text)
        if change_text:
            self._change_lbl.setText(change_text)
            is_positive = "+" in change_text
            self._change_lbl.setStyleSheet(
                f"color: {tc['success']};" if is_positive else f"color: {tc['danger'] if 'danger' in tc else '#f87171'};"
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
