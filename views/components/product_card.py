"""Tarjeta visual de producto para la vista POS."""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal

import config as app_config


class ProductCard(QFrame):
    """Tarjeta de producto clicable para el punto de venta."""

    clicked = Signal(object)

    def __init__(self, producto, parent=None):
        super().__init__(parent)
        self.producto = producto
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(160, 140)
        self.setProperty("class", "product-card") # Nueva propiedad de clase

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_lbl = QLabel(producto.icono or "🍽️")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setObjectName("product-card-icon")
        layout.addWidget(icon_lbl)

        name_lbl = QLabel(producto.nombre)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setWordWrap(True)
        name_lbl.setProperty("class", "caption")
        name_lbl.setObjectName("product-card-name")
        name_lbl.setMaximumHeight(36)
        layout.addWidget(name_lbl)

        price_lbl = QLabel(f"{app_config.CURRENCY_SYMBOL}{producto.precio:.2f}")
        price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_lbl.setProperty("class", "badge-info")
        price_lbl.setObjectName("product-card-price")
        layout.addWidget(price_lbl)

        # Badge de variantes si aplica
        if producto.tiene_variantes:
            badge = QLabel("📏 +ingredientes")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setProperty("class", "caption")
            badge.setStyleSheet("font-size: 9px; color: #f77f00; padding: 0;")
            layout.addWidget(badge)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.producto)
        super().mousePressEvent(event)
