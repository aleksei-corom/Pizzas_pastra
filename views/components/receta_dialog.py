"""Diálogo de creación/edición de recetas con ingredientes dinámicos."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QDoubleSpinBox, QSpinBox, QAbstractItemView,
    QFrame,
)
from PySide6.QtCore import Qt

from database.models import Receta, RecetaIngrediente

UNIDADES = ["unidad", "kg", "g", "l", "ml", "cda", "cdt", "oz", "lb"]


class RecetaDialog(QDialog):
    """Diálogo para crear o editar una receta con ingredientes."""

    def __init__(self, productos: list = None, receta: Receta = None, parent=None):
        super().__init__(parent)
        self._productos = productos or []
        self._receta = receta or Receta()
        self._ingredientes = []
        self.setWindowTitle("Editar Receta" if receta else "Nueva Receta")
        self.setMinimumSize(650, 500)
        self.setModal(True)
        self._build_ui()

        if receta and receta.ingredientes:
            self._ingredientes = list(receta.ingredientes)
            self._refresh_table()
            self._nombre.setText(receta.nombre)
            self._porciones.setValue(receta.porciones)
            self._set_producto(receta.producto_id)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        titulo = QLabel("\U0001f373  Receta del Producto")
        titulo.setProperty("class", "title")
        layout.addWidget(titulo)

        # Formulario superior
        form_row = QHBoxLayout()
        form_row.setSpacing(12)

        # Producto asociado
        col_prod = QVBoxLayout()
        col_prod.setSpacing(4)
        lbl_prod = QLabel("Producto")
        lbl_prod.setProperty("class", "section")
        self._producto_combo = QComboBox()
        self._producto_combo.setMinimumHeight(36)
        self._producto_combo.addItem("-- Sin asociar --", None)
        for p in self._productos:
            self._producto_combo.addItem(f"{p.nombre} (${p.precio:.2f})", p.id)
        col_prod.addWidget(lbl_prod)
        col_prod.addWidget(self._producto_combo)
        form_row.addLayout(col_prod, 2)

        # Nombre de la receta
        col_nombre = QVBoxLayout()
        col_nombre.setSpacing(4)
        lbl_nombre = QLabel("Nombre de la receta")
        lbl_nombre.setProperty("class", "section")
        self._nombre = QLineEdit()
        self._nombre.setPlaceholderText("Ej: Pizza Margherita Familiar")
        self._nombre.setMinimumHeight(36)
        col_nombre.addWidget(lbl_nombre)
        col_nombre.addWidget(self._nombre)
        form_row.addLayout(col_nombre, 2)

        # Porciones
        col_porc = QVBoxLayout()
        col_porc.setSpacing(4)
        lbl_porc = QLabel("Porciones")
        lbl_porc.setProperty("class", "section")
        self._porciones = QSpinBox()
        self._porciones.setMinimum(1)
        self._porciones.setMaximum(100)
        self._porciones.setValue(1)
        self._porciones.setMinimumHeight(36)
        col_porc.addWidget(lbl_porc)
        col_porc.addWidget(self._porciones)
        form_row.addLayout(col_porc, 1)

        layout.addLayout(form_row)

        # Tabla de ingredientes
        lbl_ing = QLabel("Ingredientes")
        lbl_ing.setProperty("class", "section")
        layout.addWidget(lbl_ing)

        self._tabla = QTableWidget(0, 5)
        self._tabla.setHorizontalHeaderLabels([
            "Ingrediente", "Cantidad", "Unidad", "Costo Unit. ($)", "Subtotal ($)"
        ])
        self._tabla.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._tabla.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )
        self._tabla.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed
        )
        self._tabla.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Fixed
        )
        self._tabla.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Fixed
        )
        self._tabla.setColumnWidth(1, 90)
        self._tabla.setColumnWidth(2, 80)
        self._tabla.setColumnWidth(3, 110)
        self._tabla.setColumnWidth(4, 100)
        self._tabla.verticalHeader().setVisible(False)
        self._tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self._tabla.setMaximumHeight(220)
        layout.addWidget(self._tabla)

        # Botones agregar/eliminar ingrediente
        ing_btn_row = QHBoxLayout()
        btn_add = QPushButton("+ Agregar Ingrediente")
        btn_add.setProperty("class", "secondary")
        btn_add.clicked.connect(self._add_row)
        ing_btn_row.addWidget(btn_add)

        btn_remove = QPushButton("- Eliminar Seleccionado")
        btn_remove.setProperty("class", "danger-ghost")
        btn_remove.clicked.connect(self._remove_row)
        ing_btn_row.addWidget(btn_remove)
        ing_btn_row.addStretch()

        # Total
        self._total_label = QLabel("Costo total: $0.00")
        self._total_label.setProperty("class", "title")
        ing_btn_row.addWidget(self._total_label)

        layout.addLayout(ing_btn_row)

        # Botones
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "secondary")
        btn_cancel.setFixedHeight(38)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("Guardar Receta")
        btn_save.setFixedHeight(38)
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._accept)
        btn_row.addWidget(btn_save)

        layout.addLayout(btn_row)

    def _set_producto(self, producto_id):
        for i in range(self._producto_combo.count()):
            if self._producto_combo.itemData(i) == producto_id:
                self._producto_combo.setCurrentIndex(i)
                break

    def _add_row(self):
        row = self._tabla.rowCount()
        self._tabla.insertRow(row)

        # Nombre editable
        name_item = QTableWidgetItem("")
        name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self._tabla.setItem(row, 0, name_item)

        # Cantidad
        qty = QDoubleSpinBox()
        qty.setDecimals(2)
        qty.setMinimum(0.01)
        qty.setValue(1.0)
        qty.valueChanged.connect(lambda: self._update_subtotal(row))
        self._tabla.setCellWidget(row, 1, qty)

        # Unidad
        unit = QComboBox()
        unit.addItems(UNIDADES)
        self._tabla.setCellWidget(row, 2, unit)

        # Costo unitario
        cost = QDoubleSpinBox()
        cost.setDecimals(2)
        cost.setMinimum(0.0)
        cost.setPrefix("$ ")
        cost.valueChanged.connect(lambda: self._update_subtotal(row))
        self._tabla.setCellWidget(row, 3, cost)

        # Subtotal (no editable)
        sub_item = QTableWidgetItem("$ 0.00")
        sub_item.setFlags(sub_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        self._tabla.setItem(row, 4, sub_item)

    def _remove_row(self):
        rows = set(item.row() for item in self._tabla.selectedItems())
        for row in sorted(rows, reverse=True):
            self._tabla.removeRow(row)
        self._update_total()

    def _update_subtotal(self, row):
        qty_widget = self._tabla.cellWidget(row, 1)
        cost_widget = self._tabla.cellWidget(row, 3)
        if qty_widget and cost_widget:
            subtotal = qty_widget.value() * cost_widget.value()
            self._tabla.item(row, 4).setText(f"$ {subtotal:.2f}")
        self._update_total()

    def _update_total(self):
        total = 0.0
        for row in range(self._tabla.rowCount()):
            qty_widget = self._tabla.cellWidget(row, 1)
            cost_widget = self._tabla.cellWidget(row, 3)
            if qty_widget and cost_widget:
                total += qty_widget.value() * cost_widget.value()
        self._total_label.setText(f"Costo total: ${total:.2f}")

    def _refresh_table(self):
        self._tabla.setRowCount(0)
        for ing in self._ingredientes:
            self._add_row()
            row = self._tabla.rowCount() - 1
            self._tabla.item(row, 0).setText(ing.nombre)
            self._tabla.cellWidget(row, 1).setValue(ing.cantidad)

            # Set unidad combo
            unit_combo = self._tabla.cellWidget(row, 2)
            idx = unit_combo.findText(ing.unidad)
            if idx >= 0:
                unit_combo.setCurrentIndex(idx)

            self._tabla.cellWidget(row, 3).setValue(ing.costo_unitario)
            self._update_subtotal(row)

    def _accept(self):
        if not self._nombre.text().strip():
            self._nombre.setFocus()
            return
        if self._tabla.rowCount() == 0:
            return
        self.accept()

    def get_receta(self) -> Receta:
        ingredientes = []
        for row in range(self._tabla.rowCount()):
            nombre = self._tabla.item(row, 0).text().strip()
            if not nombre:
                continue
            qty = self._tabla.cellWidget(row, 1).value()
            unidad = self._tabla.cellWidget(row, 2).currentText()
            costo = self._tabla.cellWidget(row, 3).value()
            ingredientes.append(RecetaIngrediente(
                nombre=nombre, cantidad=qty, unidad=unidad,
                costo_unitario=costo, subtotal=round(qty * costo, 2)
            ))

        prod_id = self._producto_combo.currentData()
        receta = self._receta
        receta.nombre = self._nombre.text().strip()
        receta.porciones = self._porciones.value()
        receta.producto_id = prod_id
        receta.ingredientes = ingredientes
        return receta
