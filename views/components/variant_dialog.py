"""Diálogo para seleccionar variantes (tamaño) e ingredientes adicionales."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QCheckBox, QScrollArea, QWidget, QButtonGroup,
)
from PySide6.QtCore import Qt

from database.producto_service import ProductoService
import config as app_config
from views.components import ModernMessageBox
from views.layouts import create_page_header


class VariantDialog(QDialog):
    """Diálogo que permite seleccionar tamaño e ingredientes antes de agregar al carrito."""

    def __init__(self, producto, parent=None):
        super().__init__(parent)
        self.producto = producto
        self.prod_svc = ProductoService()
        self.setMinimumWidth(440)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._selected_variant = None       # ProductoVariante | None
        self._selected_ingredients = []     # list of ProductoIngrediente
        self._build_ui()

    def _build_ui(self):
        outer = QFrame(self)
        outer.setObjectName("dlgOuter")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(outer)

        layout = QVBoxLayout(outer)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        # Header
        icono = self.producto.icono or "🍽️"
        title = QLabel(f"{icono}  {self.producto.nombre}")
        title.setProperty("class", "title")
        layout.addWidget(title)

        if self.producto.descripcion:
            desc = QLabel(self.producto.descripcion)
            desc.setProperty("class", "subtitle")
            desc.setWordWrap(True)
            layout.addWidget(desc)

        # Precio base
        base_layout = QHBoxLayout()
        base_layout.addWidget(QLabel("Precio base:"))
        self._base_price_lbl = QLabel(f"{app_config.CURRENCY_SYMBOL}{self.producto.precio:.2f}")
        self._base_price_lbl.setProperty("class", "badge-info")
        base_layout.addWidget(self._base_price_lbl)
        base_layout.addStretch()
        layout.addLayout(base_layout)

        # ─── Variantes (tamaños) ───
        variantes = self.prod_svc.get_variantes(self.producto.id)
        if variantes:
            sep1 = QFrame()
            sep1.setFixedHeight(1)
            sep1.setProperty("class", "divider")
            layout.addWidget(sep1)

            var_title = QLabel("📏  Seleccionar Tamaño")
            var_title.setProperty("class", "section")
            layout.addWidget(var_title)

            self._variant_group = QButtonGroup(self)
            var_layout = QHBoxLayout()
            var_layout.setSpacing(8)

            # Opción: tamaño base (sin variante)
            btn_base = QPushButton(f"Base  ({app_config.CURRENCY_SYMBOL}{self.producto.precio:.2f})")
            btn_base.setCheckable(True)
            btn_base.setChecked(True)
            btn_base.setProperty("class", "variant-btn")
            btn_base.clicked.connect(lambda: self._select_variant(None))
            self._variant_group.addButton(btn_base)
            var_layout.addWidget(btn_base)
            self._variant_buttons = {None: btn_base}

            for v in variantes:
                precio_total = self.producto.precio + v.precio_adicional
                btn = QPushButton(f"{v.nombre}  (+{app_config.CURRENCY_SYMBOL}{v.precio_adicional:.2f})")
                btn.setCheckable(True)
                btn.setProperty("class", "variant-btn")
                btn.clicked.connect(lambda checked, var=v: self._select_variant(var))
                self._variant_group.addButton(btn)
                var_layout.addWidget(btn)
                self._variant_buttons[v.id] = btn

            var_layout.addStretch()
            layout.addLayout(var_layout)

        # ─── Ingredientes adicionales ───
        ingredientes = self.prod_svc.get_ingredientes(self.producto.id, solo_activos=True)
        if ingredientes:
            sep2 = QFrame()
            sep2.setFixedHeight(1)
            sep2.setProperty("class", "divider")
            layout.addWidget(sep2)

            ing_title = QLabel("🧀  Ingredientes Adicionales")
            ing_title.setProperty("class", "section")
            layout.addWidget(ing_title)

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFixedHeight(160)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

            ing_container = QWidget()
            ing_layout = QVBoxLayout(ing_container)
            ing_layout.setContentsMargins(0, 0, 0, 0)
            ing_layout.setSpacing(4)

            self._ingredient_checks = {}
            for ing in ingredientes:
                cb = QCheckBox(
                    f"{ing.nombre}  (+{app_config.CURRENCY_SYMBOL}{ing.precio_adicional:.2f})"
                )
                cb.setProperty("class", "caption")
                cb.toggled.connect(self._update_total)
                ing_layout.addWidget(cb)
                self._ingredient_checks[ing.id] = (cb, ing)

            scroll.setWidget(ing_container)
            layout.addWidget(scroll)

        # ─── Total calculado ───
        sep3 = QFrame()
        sep3.setFixedHeight(1)
        sep3.setProperty("class", "divider")
        layout.addWidget(sep3)

        total_row = QHBoxLayout()
        total_row.addWidget(QLabel("Total del producto:"), 1)
        self._total_lbl = QLabel(f"{app_config.CURRENCY_SYMBOL}{self.producto.precio:.2f}")
        self._total_lbl.setProperty("class", "title")
        self._total_lbl.setObjectName("variant-total")
        total_row.addWidget(self._total_lbl)
        layout.addLayout(total_row)

        # ─── Botones ───
        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "secondary")
        btn_cancel.setFixedHeight(42)
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)

        btn_add = QPushButton("➕  Agregar a la Orden")
        btn_add.setProperty("class", "success")
        btn_add.setFixedHeight(42)
        btn_add.clicked.connect(self.accept)
        btns.addWidget(btn_add)
        layout.addLayout(btns)

    def _select_variant(self, variant):
        self._selected_variant = variant
        for vid, btn in self._variant_buttons.items():
            if variant is None and vid is None:
                btn.setChecked(True)
            elif variant is not None and vid == variant.id:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
        self._update_total()

    def _update_total(self):
        precio = self.producto.precio
        if self._selected_variant:
            precio += self._selected_variant.precio_adicional
        for cb, ing in self._ingredient_checks.values():
            if cb.isChecked():
                precio += ing.precio_adicional
        self._total_lbl.setText(f"{app_config.CURRENCY_SYMBOL}{precio:.2f}")

    @property
    def precio_final(self) -> float:
        """Precio final incluyendo variante e ingredientes."""
        precio = self.producto.precio
        if self._selected_variant:
            precio += self._selected_variant.precio_adicional
        for cb, ing in self._ingredient_checks.values():
            if cb.isChecked():
                precio += ing.precio_adicional
        return precio

    @property
    def descripcion_item(self) -> str:
        """Descripción textual del item (variante + ingredientes)."""
        partes = []
        if self._selected_variant:
            partes.append(self._selected_variant.nombre)
        extras = []
        for cb, ing in self._ingredient_checks.values():
            if cb.isChecked():
                extras.append(ing.nombre)
        if extras:
            partes.append(f"+{', '.join(extras)}")
        return " • ".join(partes) if partes else ""
