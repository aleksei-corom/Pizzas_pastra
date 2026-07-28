"""Tarjeta visual de combo/promoción para el POS — theme-aware."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal

import config as app_config
from database.models import Combo


class ComboCard(QFrame):
    """Tarjeta de combo clicable para el punto de venta."""

    clicked = Signal(object)

    def __init__(self, combo: Combo, parent=None):
        super().__init__(parent)
        self.combo = combo
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(160, 150)
        self.setProperty("class", "combo-card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 8)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Icono del combo
        icon_lbl = QLabel(combo.icono or "\U0001f389")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setObjectName("combo-card-icon")
        layout.addWidget(icon_lbl)

        # Nombre
        name_lbl = QLabel(combo.nombre)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setWordWrap(True)
        name_lbl.setProperty("class", "caption")
        name_lbl.setObjectName("combo-card-name")
        name_lbl.setMaximumHeight(34)
        layout.addWidget(name_lbl)

        # Items count — usa clase CSS en vez de inline style
        n_items = len(combo.items)
        items_lbl = QLabel(f"{n_items} producto{'s' if n_items != 1 else ''}")
        items_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        items_lbl.setProperty("class", "small-muted")
        layout.addWidget(items_lbl)

        # Precio + badge de ahorro — badge usa clase CSS
        price_row = QHBoxLayout()
        price_row.setSpacing(4)
        price_row.setAlignment(Qt.AlignmentFlag.AlignCenter)

        price_lbl = QLabel(f"{app_config.CURRENCY_SYMBOL}{combo.precio_total:.2f}")
        price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_lbl.setProperty("class", "badge-info")
        price_lbl.setObjectName("combo-card-price")
        price_row.addWidget(price_lbl)

        if combo.ahorro > 0:
            ahorro_lbl = QLabel(f"-{app_config.CURRENCY_SYMBOL}{combo.ahorro:.2f}")
            ahorro_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ahorro_lbl.setProperty("class", "badge-success")
            ahorro_lbl.setObjectName("combo-savings-badge")
            price_row.addWidget(ahorro_lbl)

        layout.addLayout(price_row)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.combo)
        super().mousePressEvent(event)
