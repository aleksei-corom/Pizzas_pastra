"""Diálogo para crear/editar combos y promociones."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QLineEdit, QDoubleSpinBox, QTextEdit, QFrame, QComboBox,
    QSpinBox,
)
from PySide6.QtCore import Qt

from database.db_manager import DatabaseManager
from database.models import Combo, ComboItem, Producto
from config import CURRENCY_SYMBOL
from views.components import ModernMessageBox


class ComboDialog(QDialog):
    """Diálogo para crear o editar un combo con sus productos."""

    def __init__(self, parent=None, combo: Combo = None, db: DatabaseManager = None):
        super().__init__(parent)
        self.combo = combo
        self.db = db or DatabaseManager()
        self._productos_cache: list[Producto] = []
        self._items_temp: list[ComboItem] = []
        self.setWindowTitle("Editar Combo" if combo else "Nuevo Combo")
        self.setMinimumSize(650, 550)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_ui()
        if combo:
            self._fill_data()
        else:
            self._recalc_savings()

    def _build_ui(self):
        outer = QFrame(self)
        outer.setObjectName("dlgOuter")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(outer)

        layout = QVBoxLayout(outer)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # Título
        title_text = "🎉  Editar Combo" if self.combo else "🎉  Nuevo Combo"
        title = QLabel(title_text)
        title.setProperty("class", "title")
        layout.addWidget(title)

        # ─── Sección: Datos generales ───
        general_frame = QFrame()
        general_frame.setProperty("class", "card-light")
        gf_layout = QVBoxLayout(general_frame)
        gf_layout.setContentsMargins(12, 10, 12, 10)
        gf_layout.setSpacing(8)

        gf_title = QLabel("Datos del Combo")
        gf_title.setProperty("class", "section")
        gf_layout.addWidget(gf_title)

        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # Nombre
        name_col = QVBoxLayout()
        name_col.setSpacing(4)
        lbl_nombre = QLabel("Nombre")
        lbl_nombre.setProperty("class", "caption")
        name_col.addWidget(lbl_nombre)
        self._nombre = QLineEdit()
        self._nombre.setPlaceholderText("Ej: Combo Familiar")
        self._nombre.setFixedHeight(36)
        self._nombre.textChanged.connect(self._recalc_savings)
        name_col.addWidget(self._nombre)
        row1.addLayout(name_col, 2)

        # Icono
        icon_col = QVBoxLayout()
        icon_col.setSpacing(4)
        lbl_icono = QLabel("Icono")
        lbl_icono.setProperty("class", "caption")
        icon_col.addWidget(lbl_icono)
        self._icono = QLineEdit()
        self._icono.setPlaceholderText("🎉")
        self._icono.setFixedWidth(80)
        self._icono.setFixedHeight(36)
        icon_col.addWidget(self._icono)
        row1.addLayout(icon_col)

        # Precio Total
        price_col = QVBoxLayout()
        price_col.setSpacing(4)
        lbl_precio = QLabel("Precio del Combo")
        lbl_precio.setProperty("class", "caption")
        price_col.addWidget(lbl_precio)
        self._precio_total = QDoubleSpinBox()
        self._precio_total.setPrefix(f"{CURRENCY_SYMBOL} ")
        self._precio_total.setRange(0.01, 9999.99)
        self._precio_total.setDecimals(2)
        self._precio_total.setValue(15.00)
        self._precio_total.setFixedHeight(36)
        self._precio_total.valueChanged.connect(self._recalc_savings)
        price_col.addWidget(self._precio_total)
        row1.addLayout(price_col, 1)

        gf_layout.addLayout(row1)

        # Indicador de ahorro (solo lectura)
        savings_row = QHBoxLayout()
        lbl_ahorro = QLabel("Ahorro:")
        lbl_ahorro.setProperty("class", "caption")
        savings_row.addWidget(lbl_ahorro)
        self._ahorro_lbl = QLabel(f"{CURRENCY_SYMBOL}0.00")
        self._ahorro_lbl.setProperty("class", "badge-success")
        savings_row.addWidget(self._ahorro_lbl)
        self._suma_lbl = QLabel("(Suma individual: $0.00)")
        self._suma_lbl.setProperty("class", "caption")
        savings_row.addWidget(self._suma_lbl)
        savings_row.addStretch()
        gf_layout.addLayout(savings_row)

        # Descripción
        lbl_desc = QLabel("Descripción (opcional)")
        lbl_desc.setProperty("class", "caption")
        gf_layout.addWidget(lbl_desc)
        self._descripcion = QTextEdit()
        self._descripcion.setPlaceholderText("Describe los beneficios del combo...")
        self._descripcion.setMaximumHeight(60)
        gf_layout.addWidget(self._descripcion)

        layout.addWidget(general_frame)

        # ─── Sección: Productos del Combo ───
        items_label = QLabel("Productos incluidos")
        items_label.setProperty("class", "section")
        layout.addWidget(items_label)

        self._items_table = QTableWidget(0, 5)
        self._items_table.setHorizontalHeaderLabels(["Producto", "Precio Unit.", "Cantidad", "Subtotal", "Quitar"])
        self._items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in [1, 2, 3, 4]:
            self._items_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self._items_table.verticalHeader().setVisible(False)
        self._items_table.verticalHeader().setDefaultSectionSize(38)
        self._items_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._items_table.setAlternatingRowColors(True)
        layout.addWidget(self._items_table, 1)

        # Formulario para agregar producto
        add_row = QHBoxLayout()
        add_row.setSpacing(8)

        self._prod_combo = QComboBox()
        self._prod_combo.setMinimumWidth(240)
        self._prod_combo.setFixedHeight(36)
        add_row.addWidget(self._prod_combo, 1)

        self._qty_spin = QSpinBox()
        self._qty_spin.setRange(1, 99)
        self._qty_spin.setValue(1)
        self._qty_spin.setFixedWidth(70)
        self._qty_spin.setFixedHeight(36)
        add_row.addWidget(self._qty_spin)

        btn_add_prod = QPushButton("➕ Agregar")
        btn_add_prod.setFixedHeight(36)
        btn_add_prod.clicked.connect(self._add_product_to_combo)
        add_row.addWidget(btn_add_prod)

        layout.addLayout(add_row)

        # ─── Botones de acción ───
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setProperty("class", "divider")
        layout.addWidget(sep)

        btns = QHBoxLayout()
        btns.addStretch()

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "secondary")
        btn_cancel.setFixedHeight(38)
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_cancel)

        btn_save = QPushButton("💾  Guardar Combo")
        btn_save.setFixedHeight(38)
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_save)

        layout.addLayout(btns)

    def _fill_data(self):
        """Rellena datos si es edición."""
        c = self.combo
        self._nombre.setText(c.nombre)
        self._descripcion.setPlainText(c.descripcion)
        self._precio_total.setValue(c.precio_total)
        self._icono.setText(c.icono)
        self._items_temp = list(c.items) if c.items else []
        self._refresh_items_table()

    def _load_productos(self):
        """Carga productos disponibles en el combo."""
        self._productos_cache = self.db.get_productos(solo_disponibles=True)
        self._prod_combo.clear()
        for p in self._productos_cache:
            self._prod_combo.addItem(
                f"{p.icono} {p.nombre} — {CURRENCY_SYMBOL}{p.precio:.2f}",
                p.id
            )

    def _add_product_to_combo(self):
        if not self._productos_cache:
            self._load_productos()
        if not self._productos_cache:
            return

        prod_id = self._prod_combo.currentData()
        cant = self._qty_spin.value()
        producto = next((p for p in self._productos_cache if p.id == prod_id), None)
        if not producto:
            return

        # Si el producto ya está en la lista, sumar cantidad
        for item in self._items_temp:
            if item.producto_id == prod_id:
                item.cantidad += cant
                self._refresh_items_table()
                self._recalc_savings()
                return

        self._items_temp.append(ComboItem(
            producto_id=prod_id,
            producto_nombre=producto.nombre,
            cantidad=cant,
            precio_individual=producto.precio,
        ))
        self._refresh_items_table()
        self._recalc_savings()

    def _refresh_items_table(self):
        self._items_table.setRowCount(len(self._items_temp))
        for i, item in enumerate(self._items_temp):
            prod = next((p for p in self._productos_cache if p.id == item.producto_id), None)
            icono = prod.icono + " " if prod else ""
            self._items_table.setItem(i, 0, QTableWidgetItem(f"{icono}{item.producto_nombre}"))
            self._items_table.setItem(i, 1,
                QTableWidgetItem(f"{CURRENCY_SYMBOL}{item.precio_individual:.2f}"))
            self._items_table.setItem(i, 2, QTableWidgetItem(str(item.cantidad)))
            subtotal = item.cantidad * item.precio_individual
            self._items_table.setItem(i, 3,
                QTableWidgetItem(f"{CURRENCY_SYMBOL}{subtotal:.2f}"))

            btn_del = QPushButton("🗑️")
            btn_del.setFixedSize(32, 32)
            btn_del.setProperty("class", "icon-danger")
            btn_del.clicked.connect(lambda _, idx=i: self._remove_item(idx))
            self._items_table.setCellWidget(i, 4, btn_del)

    def _remove_item(self, idx):
        if 0 <= idx < len(self._items_temp):
            self._items_temp.pop(idx)
            self._refresh_items_table()
            self._recalc_savings()

    def _recalc_savings(self):
        """Calcula el ahorro y actualiza indicadores."""
        suma_individual = sum(
            item.cantidad * item.precio_individual for item in self._items_temp
        )
        precio_combo = self._precio_total.value()
        ahorro = round(max(0, suma_individual - precio_combo), 2)

        self._suma_lbl.setText(f"(Suma individual: {CURRENCY_SYMBOL}{suma_individual:.2f})")
        if ahorro > 0:
            self._ahorro_lbl.setText(f"{CURRENCY_SYMBOL}{ahorro:.2f} de ahorro 🎉")
            self._ahorro_lbl.setProperty("class", "badge-success")
            self._ahorro_lbl.style().unpolish(self._ahorro_lbl)
            self._ahorro_lbl.style().polish(self._ahorro_lbl)
        else:
            self._ahorro_lbl.setText(f"{CURRENCY_SYMBOL}0.00")
            self._ahorro_lbl.setProperty("class", "badge-info")
            self._ahorro_lbl.style().unpolish(self._ahorro_lbl)
            self._ahorro_lbl.style().polish(self._ahorro_lbl)

    def _save(self):
        nombre = self._nombre.text().strip()
        if not nombre:
            ModernMessageBox.warning(self, "Campo Requerido", "El nombre del combo es obligatorio.")
            return
        if not self._items_temp:
            ModernMessageBox.warning(self, "Sin Productos", "Agrega al menos un producto al combo.")
            return

        suma_individual = sum(
            item.cantidad * item.precio_individual for item in self._items_temp
        )
        ahorro = round(max(0, suma_individual - self._precio_total.value()), 2)

        if self.combo is None:
            self.combo = Combo()

        self.combo.nombre = nombre
        self.combo.descripcion = self._descripcion.toPlainText().strip()
        self.combo.precio_total = self._precio_total.value()
        self.combo.ahorro = ahorro
        self.combo.icono = self._icono.text().strip() or "🎉"
        self.combo.items = self._items_temp

        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self._load_productos()
