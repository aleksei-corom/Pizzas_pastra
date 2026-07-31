"""Widget reutilizable para mostrar un Insight del Asistente Inteligente.

Muestra un insight con icono según tipo, título, descripción,
métricas y un botón de acción opcional.
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)
from PySide6.QtCore import Qt, Signal


class InsightCard(QFrame):
    """Tarjeta visual para un insight del asistente inteligente."""

    action_clicked = Signal(str)  # Emite la acción del insight

    ICONOS = {
        "alerta": "\u26a0\ufe0f",
        "oportunidad": "\U0001f4a0",
        "positivo": "\u2705",
        "sugerencia": "\U0001f4a1",
        "info": "\u2139\ufe0f",
    }

    COLORES_BORDE = {
        "alerta": "danger",
        "oportunidad": "accent",
        "positivo": "success",
        "sugerencia": "primary",
        "info": "primary",
    }

    def __init__(self, insight, parent=None):
        super().__init__(parent)
        self.insight = insight
        self.setProperty("class", "card")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Fila superior: icono + título + métrica
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        icono = QLabel(self.ICONOS.get(self.insight.tipo, "\u2139\ufe0f"))
        icono.setStyleSheet("font-size: 20px; border: none;")
        top_row.addWidget(icono)

        titulo = QLabel(self.insight.titulo)
        titulo.setProperty("class", "section")
        titulo.setWordWrap(True)
        top_row.addWidget(titulo, 1)

        # Métrica si existe
        if self.insight.metrica_valor:
            metrica_col = QVBoxLayout()
            metrica_col.setSpacing(0)
            metrica_val = QLabel(self.insight.metrica_valor)
            metrica_val.setProperty("class", "title")
            metrica_val.setAlignment(Qt.AlignmentFlag.AlignRight)
            metrica_col.addWidget(metrica_val)

            if self.insight.metrica_label:
                metrica_lbl = QLabel(self.insight.metrica_label)
                metrica_lbl.setProperty("class", "caption")
                metrica_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
                metrica_col.addWidget(metrica_lbl)

            top_row.addLayout(metrica_col)

        layout.addLayout(top_row)

        # Descripción
        if self.insight.descripcion:
            desc = QLabel(self.insight.descripcion)
            desc.setProperty("class", "caption")
            desc.setWordWrap(True)
            desc.setTextFormat(Qt.TextFormat.PlainText)
            layout.addWidget(desc)

        # Botón de acción
        if self.insight.accion:
            btn = QPushButton(f"\u2192  {self.insight.accion}")
            btn.setProperty("class", "ghost")
            btn.setFixedHeight(32)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda: self.action_clicked.emit(self.insight.accion))
            layout.addWidget(btn)

        # Color de borde según tipo
        try:
            from views.themes.theme_helper import th
            color_key = self.COLORES_BORDE.get(self.insight.tipo, "primary")
            border_color = th(color_key, "#6366f1")
            self.setStyleSheet(
                f"InsightCard {{ border-left: 3px solid {border_color}; }}"
            )
        except Exception:
            pass
