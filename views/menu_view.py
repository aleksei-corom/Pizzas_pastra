"""Vista Menú — Gestión de categorías y productos."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit, QCheckBox,
    QFrame,
)
from PySide6.QtCore import Qt

from database.producto_service import ProductoService
from database.orden_service import OrdenService
from database.models import Producto, Categoria, ProductoVariante, ProductoIngrediente
import config as app_config
from views.components import ModernMessageBox, SearchBar
from views.layouts import create_page_header, create_form_row
from views.components.combo_dialog import ComboDialog


class VariantesDialog(QDialog):
    """Diálogo para gestionar variantes (tamaños) de un producto."""

    def __init__(self, parent=None, producto=None, db=None):
        super().__init__(parent)
        self.producto = producto
        self.prod_svc = db if isinstance(db, ProductoService) else ProductoService()
        self.setWindowTitle(f"Variantes - {producto.nombre}" if producto else "Variantes")
        self.setMinimumSize(500, 400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        outer = QFrame(self)
        outer.setObjectName("dlgOuter")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(outer)

        layout = QVBoxLayout(outer)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)

        icono = self.producto.icono or "🍽️"
        title = QLabel(f"📏  Variantes — {icono} {self.producto.nombre}")
        title.setProperty("class", "title")
        layout.addWidget(title)

        # Tabla de variantes
        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Nombre", "Precio Adicional", "Orden", "Eliminar"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in [1, 2, 3]:
            self._table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self._table, 1)

        # Formulario para nueva variante
        form = QHBoxLayout()
        form.setSpacing(8)

        self._var_nombre = QLineEdit()
        self._var_nombre.setPlaceholderText("Ej: Mediana, Familiar...")
        self._var_nombre.setFixedHeight(36)
        form.addWidget(self._var_nombre, 1)

        self._var_precio = QDoubleSpinBox()
        self._var_precio.setPrefix(f"{app_config.CURRENCY_SYMBOL} ")
        self._var_precio.setRange(0, 999999.99)
        self._var_precio.setDecimals(2)
        self._var_precio.setValue(2.00)
        self._var_precio.setFixedHeight(36)
        self._var_precio.setFixedWidth(120)
        form.addWidget(self._var_precio)

        btn_add = QPushButton("➕ Agregar")
        btn_add.setFixedHeight(36)
        btn_add.clicked.connect(self._agregar_variante)
        form.addWidget(btn_add)
        layout.addLayout(form)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setProperty("class", "divider")
        layout.addWidget(sep)

        btn_close = QPushButton("Cerrar")
        btn_close.setProperty("class", "secondary")
        btn_close.setFixedHeight(38)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

    def cargar_datos(self):
        variantes = self.prod_svc.get_variantes(self.producto.id)
        self._table.setRowCount(len(variantes))
        for i, v in enumerate(variantes):
            self._table.setItem(i, 0, QTableWidgetItem(v.nombre))
            self._table.setItem(i, 1,
                QTableWidgetItem(f"{app_config.CURRENCY_SYMBOL}{v.precio_adicional:.2f}"))
            self._table.setItem(i, 2, QTableWidgetItem(str(v.orden)))

            btn_del = QPushButton("🗑️")
            btn_del.setFixedSize(32, 32)
            btn_del.setProperty("class", "icon-danger")
            btn_del.clicked.connect(lambda _, vid=v.id: self._eliminar_variante(vid))
            self._table.setCellWidget(i, 3, btn_del)
            self._table.setRowHeight(i, 38)

    def _agregar_variante(self):
        nombre = self._var_nombre.text().strip()
        if not nombre:
            ModernMessageBox.warning(self, "Campo Requerido", "El nombre de la variante es obligatorio.")
            return
        v = ProductoVariante(
            producto_id=self.producto.id,
            nombre=nombre,
            precio_adicional=self._var_precio.value(),
            orden=self._table.rowCount() + 1,
        )
        self.prod_svc.crear_variante(v)
        self._var_nombre.clear()
        self._var_precio.setValue(2.00)
        self.cargar_datos()

    def _eliminar_variante(self, vid):
        self.prod_svc.eliminar_variante(vid)
        self.cargar_datos()


class ProductDialog(QDialog):
    """Diálogo para crear/editar un producto."""

    def __init__(self, parent=None, producto=None, categorias=None):
        super().__init__(parent)
        self.producto = producto
        self.setWindowTitle("Editar Producto" if producto else "Nuevo Producto")
        self.setMinimumWidth(480)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_ui(categorias or [])
        if producto:
            self._fill_data()

    def _build_ui(self, categorias):
        outer = QFrame(self)
        outer.setObjectName("dlgOuter")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(outer)

        layout = QVBoxLayout(outer)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # Título
        title_text = "✏️  Editar Producto" if self.producto else "➕  Nuevo Producto"
        title = QLabel(title_text)
        title.setProperty("class", "title")
        layout.addWidget(title)

        # Campos
        self._nombre = QLineEdit()
        self._nombre.setPlaceholderText("Nombre del producto")
        layout.addLayout(create_form_row("Nombre", self._nombre, required=True))

        self._categoria = QComboBox()
        for cat in categorias:
            self._categoria.addItem(f"{cat.icono} {cat.nombre}", cat.id)
        layout.addLayout(create_form_row("Categoría", self._categoria, required=True))

        self._precio = QDoubleSpinBox()
        self._precio.setPrefix(f"{app_config.CURRENCY_SYMBOL} ")
        self._precio.setMaximum(9999999.99)
        self._precio.setDecimals(2)
        layout.addLayout(create_form_row("Precio", self._precio, required=True))

        self._icono = QLineEdit()
        self._icono.setPlaceholderText("Emoji (ej: 🍕)")
        self._icono.setMaximumWidth(120)
        layout.addLayout(create_form_row("Icono", self._icono))

        self._descripcion = QTextEdit()
        self._descripcion.setPlaceholderText("Descripción del producto...")
        self._descripcion.setMaximumHeight(80)
        layout.addLayout(create_form_row("Descripción", self._descripcion))

        self._disponible = QCheckBox("Producto disponible")
        self._disponible.setChecked(True)
        layout.addWidget(self._disponible)

        # Botones
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

        btn_save = QPushButton("💾  Guardar")
        btn_save.setFixedHeight(38)
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _fill_data(self):
        p = self.producto
        self._nombre.setText(p.nombre)
        self._precio.setValue(p.precio)
        self._icono.setText(p.icono)
        self._descripcion.setPlainText(p.descripcion)
        self._disponible.setChecked(p.disponible)
        idx = self._categoria.findData(p.categoria_id)
        if idx >= 0:
            self._categoria.setCurrentIndex(idx)

    def _save(self):
        nombre = self._nombre.text().strip()
        if not nombre:
            ModernMessageBox.warning(self, "Campo Requerido", "El nombre es obligatorio.")
            return

        if self.producto is None:
            self.producto = Producto()

        self.producto.nombre = nombre
        self.producto.categoria_id = self._categoria.currentData()
        self.producto.precio = self._precio.value()
        self.producto.icono = self._icono.text().strip() or "🍽️"
        self.producto.descripcion = self._descripcion.toPlainText().strip()
        self.producto.disponible = self._disponible.isChecked()
        self.accept()


class CategoryDialog(QDialog):
    """Diálogo para crear/editar una categoría."""

    def __init__(self, parent=None, categoria=None):
        super().__init__(parent)
        self.categoria = categoria
        self.setWindowTitle("Editar Categoría" if categoria else "Nueva Categoría")
        self.setMinimumWidth(400)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_ui()
        if categoria:
            self._fill_data()

    def _build_ui(self):
        outer = QFrame(self)
        outer.setObjectName("dlgOuter")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(outer)

        layout = QVBoxLayout(outer)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        title_text = "✏️  Editar Categoría" if self.categoria else "📁  Nueva Categoría"
        title = QLabel(title_text)
        title.setProperty("class", "title")
        layout.addWidget(title)

        self._nombre = QLineEdit()
        self._nombre.setPlaceholderText("Nombre de la categoría")
        layout.addLayout(create_form_row("Nombre", self._nombre, required=True))

        self._icono = QLineEdit()
        self._icono.setPlaceholderText("Emoji (ej: 🍕)")
        self._icono.setMaximumWidth(120)
        layout.addLayout(create_form_row("Icono", self._icono))

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

        btn_save = QPushButton("💾  Guardar")
        btn_save.setFixedHeight(38)
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _fill_data(self):
        self._nombre.setText(self.categoria.nombre)
        self._icono.setText(self.categoria.icono)

    def _save(self):
        nombre = self._nombre.text().strip()
        if not nombre:
            ModernMessageBox.warning(self, "Campo Requerido", "El nombre es obligatorio.")
            return

        if self.categoria is None:
            self.categoria = Categoria(
                nombre=nombre,
                icono=self._icono.text().strip() or "📁",
                orden=0,
                activa=1
            )
        else:
            self.categoria.nombre = nombre
            self.categoria.icono = self._icono.text().strip() or "📁"

        self.accept()


class CategoryManagerDialog(QDialog):
    """Diálogo para gestionar las categorías (listado)."""

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.prod_svc = db if isinstance(db, ProductoService) else ProductoService()
        self.setWindowTitle("Gestionar Categorías")
        self.setMinimumSize(500, 450)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        outer = QFrame(self)
        outer.setObjectName("dlgOuter")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(outer)

        layout = QVBoxLayout(outer)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("📁  Gestionar Categorías")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()

        btn_new = QPushButton("➕  Nueva Categoría")
        btn_new.setFixedHeight(36)
        btn_new.clicked.connect(self._nueva_categoria)
        header.addWidget(btn_new)
        layout.addLayout(header)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["Icono", "Nombre", "Editar", "Eliminar"])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in [0, 2, 3]:
            self._table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

        btn_close = QPushButton("Cerrar")
        btn_close.setProperty("class", "secondary")
        btn_close.setFixedHeight(38)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

    def cargar_datos(self):
        categorias = self.prod_svc.get_categorias(solo_activas=False)
        self._table.setRowCount(len(categorias))
        for i, cat in enumerate(categorias):
            self._table.setItem(i, 0, QTableWidgetItem(cat.icono))
            self._table.setItem(i, 1, QTableWidgetItem(cat.nombre))

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(36, 36)
            btn_edit.setProperty("class", "icon-warning")
            btn_edit.clicked.connect(lambda _, c=cat: self._editar_categoria(c))
            self._table.setCellWidget(i, 2, btn_edit)

            btn_del = QPushButton("🗑️")
            btn_del.setFixedSize(36, 36)
            btn_del.setProperty("class", "icon-danger")
            btn_del.clicked.connect(lambda _, cid=cat.id: self._eliminar_categoria(cid))
            self._table.setCellWidget(i, 3, btn_del)

    def _nueva_categoria(self):
        dlg = CategoryDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.prod_svc.crear_categoria(dlg.categoria)
            self.cargar_datos()

    def _editar_categoria(self, categoria):
        dlg = CategoryDialog(self, categoria=categoria)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.prod_svc.actualizar_categoria(dlg.categoria)
            self.cargar_datos()

    def _eliminar_categoria(self, cat_id):
        result = ModernMessageBox.question(
            self, "Desactivar Categoría",
            "¿Estás seguro de que deseas desactivar esta categoría?\nNo se podrá desactivar si tiene productos activos."
        )
        if result == QDialog.DialogCode.Accepted:
            try:
                self.prod_svc.eliminar_categoria(cat_id)
                self.cargar_datos()
            except ValueError as e:
                ModernMessageBox.error(
                    self, "Error al Desactivar", str(e)
                )
            except Exception as e:
                ModernMessageBox.error(
                    self, "Error Inesperado",
                    f"No se pudo completar la operación: {e}"
                )


class ComboManagementDialog(QDialog):
    """Diálogo para gestionar combos/promociones (listado + CRUD)."""

    def __init__(self, parent=None, db=None):
        super().__init__(parent)
        self.orden_svc = db if isinstance(db, OrdenService) else OrdenService()
        self.prod_svc = ProductoService()
        self.setWindowTitle("Gestionar Combos")
        self.setMinimumSize(650, 500)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        outer = QFrame(self)
        outer.setObjectName("dlgOuter")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.addWidget(outer)

        layout = QVBoxLayout(outer)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        header = QHBoxLayout()
        title = QLabel("🎉  Gestionar Combos y Promociones")
        title.setProperty("class", "title")
        header.addWidget(title)
        header.addStretch()

        btn_new = QPushButton("➕  Nuevo Combo")
        btn_new.setFixedHeight(36)
        btn_new.clicked.connect(self._nuevo_combo)
        header.addWidget(btn_new)
        layout.addLayout(header)

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels(["Icono", "Nombre", "Items", "Precio", "Ahorro", "Acciones"])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in [0, 2, 3, 4, 5]:
            self._table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, 1)

        btn_close = QPushButton("Cerrar")
        btn_close.setProperty("class", "secondary")
        btn_close.setFixedHeight(38)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

    def cargar_datos(self):
        combos = self.orden_svc.get_combos(solo_activos=False)
        self._table.setRowCount(len(combos))
        for i, c in enumerate(combos):
            self._table.setItem(i, 0, QTableWidgetItem(c.icono or "🎉"))
            self._table.setItem(i, 1, QTableWidgetItem(c.nombre))
            self._table.setItem(i, 2, QTableWidgetItem(str(len(c.items))))
            self._table.setItem(i, 3, QTableWidgetItem(f"{app_config.CURRENCY_SYMBOL}{c.precio_total:.2f}"))
            ahorro_text = f"{app_config.CURRENCY_SYMBOL}{c.ahorro:.2f}" if c.ahorro > 0 else "—"
            self._table.setItem(i, 4, QTableWidgetItem(ahorro_text))

            # Acciones
            actions_w = QWidget()
            actions_l = QHBoxLayout(actions_w)
            actions_l.setContentsMargins(4, 2, 4, 2)
            actions_l.setSpacing(4)

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(32, 32)
            btn_edit.setProperty("class", "icon-warning")
            btn_edit.clicked.connect(lambda _, combo=c: self._editar_combo(combo))
            actions_l.addWidget(btn_edit)

            btn_toggle = QPushButton("✅" if c.activo else "❌")
            btn_toggle.setFixedSize(32, 32)
            btn_toggle.setProperty("class", "icon-success" if c.activo else "icon-danger")
            btn_toggle.setToolTip("Desactivar" if c.activo else "Activar")
            btn_toggle.clicked.connect(lambda _, cid=c.id: self._toggle_combo(cid))
            actions_l.addWidget(btn_toggle)

            self._table.setCellWidget(i, 5, actions_w)

    def _nuevo_combo(self):
        dlg = ComboDialog(self, db=self.prod_svc)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.orden_svc.crear_combo(dlg.combo)
            ModernMessageBox.success(self, "Combo Creado", f"{dlg.combo.nombre} creado exitosamente.")
            self.cargar_datos()

    def _editar_combo(self, combo):
        dlg = ComboDialog(self, combo=combo, db=self.prod_svc)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Para editar: eliminar el combo viejo y crear el nuevo
            self.orden_svc.eliminar_combo(combo.id)
            self.orden_svc.crear_combo(dlg.combo)
            ModernMessageBox.success(self, "Combo Actualizado", f"{dlg.combo.nombre} actualizado.")
            self.cargar_datos()

    def _toggle_combo(self, combo_id):
        self.orden_svc.toggle_combo(combo_id)
        self.cargar_datos()


class MenuView(QWidget):
    """Vista de gestión del menú con tabla de productos y CRUD."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.prod_svc = ProductoService()
        self.orden_svc = OrdenService()
        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(20)

        # Header con botón nuevo
        btn_cats = QPushButton("📁  Categorías")
        btn_cats.setFixedHeight(40)
        btn_cats.setProperty("class", "secondary")
        btn_cats.clicked.connect(self._gestionar_categorias)

        btn_combos = QPushButton("🎉  Combos")
        btn_combos.setFixedHeight(40)
        btn_combos.setProperty("class", "secondary")
        btn_combos.clicked.connect(self._gestionar_combos)

        btn_new = QPushButton("➕  Nuevo Producto")
        btn_new.setFixedHeight(40)
        btn_new.clicked.connect(self._nuevo_producto)
        layout.addLayout(create_page_header(
            "📋  Gestión del Menú",
            "Administra tus productos, categorías y combos",
            actions=[btn_cats, btn_combos, btn_new]
        ))

        # Filtros
        filters = QHBoxLayout()
        filters.setSpacing(12)
        self._search = SearchBar("Buscar producto...")
        self._search.setMaximumWidth(300)
        self._search.textChanged.connect(self._filtrar)
        filters.addWidget(self._search)

        self._cat_filter = QComboBox()
        self._cat_filter.addItem("Todas las categorías", None)
        self._cat_filter.setMinimumWidth(200)
        self._cat_filter.currentIndexChanged.connect(self._filtrar)
        filters.addWidget(self._cat_filter)
        filters.addStretch()
        layout.addLayout(filters)

        # Tabla
        self._table = QTableWidget(0, 8)
        self._table.setHorizontalHeaderLabels([
            "", "Nombre", "Categoría", "Precio", "Variantes", "Estado", "Editar", "Eliminar"
        ])
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for col in [0, 3, 4, 5, 6, 7]:
            self._table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(42)
        self._table.verticalHeader().setMinimumSectionSize(36)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table, 1)

    def cargar_datos(self):
        """Carga productos y categorías."""
        self._load_categorias_filter()
        self._filtrar()

    def _load_categorias_filter(self):
        self._cat_filter.clear()
        self._cat_filter.addItem("Todas las categorías", None)
        for cat in self.prod_svc.get_categorias(solo_activas=False):
            self._cat_filter.addItem(f"{cat.icono} {cat.nombre}", cat.id)

    def _filtrar(self):
        search_text = self._search.text().strip()
        cat_id = self._cat_filter.currentData()

        if search_text:
            productos = self.prod_svc.buscar_productos(search_text)
            if cat_id:
                productos = [p for p in productos if p.categoria_id == cat_id]
        else:
            productos = self.prod_svc.get_productos(categoria_id=cat_id)

        self._populate_table(productos)

    def _populate_table(self, productos):
        self._table.setRowCount(len(productos))
        for i, prod in enumerate(productos):
            self._table.setItem(i, 0, QTableWidgetItem(prod.icono))
            self._table.setItem(i, 1, QTableWidgetItem(prod.nombre))
            self._table.setItem(i, 2, QTableWidgetItem(prod.categoria_nombre))
            self._table.setItem(i, 3, QTableWidgetItem(f"{app_config.CURRENCY_SYMBOL}{prod.precio:.2f}"))

            # Columna variantes
            btn_vars = QPushButton("📏" if prod.tiene_variantes else "➕")
            btn_vars.setFixedSize(36, 36)
            btn_vars.setToolTip("Gestionar variantes" if prod.tiene_variantes else "Agregar variantes")
            btn_vars.setProperty("class", "icon-warning" if prod.tiene_variantes else "icon-action")
            btn_vars.clicked.connect(lambda _, p=prod: self._gestionar_variantes(p))
            self._table.setCellWidget(i, 4, btn_vars)

            estado_text = "✅ Disponible" if prod.disponible else "❌ No disponible"
            self._table.setItem(i, 5, QTableWidgetItem(estado_text))

            btn_edit = QPushButton("✏️")
            btn_edit.setFixedSize(36, 36)
            btn_edit.setProperty("class", "icon-warning")
            btn_edit.clicked.connect(lambda _, p=prod: self._editar_producto(p))
            self._table.setCellWidget(i, 6, btn_edit)

            btn_del = QPushButton("🗑️")
            btn_del.setFixedSize(36, 36)
            btn_del.setProperty("class", "icon-danger")
            btn_del.clicked.connect(lambda _, pid=prod.id: self._eliminar_producto(pid))
            self._table.setCellWidget(i, 7, btn_del)

    def _nuevo_producto(self):
        categorias = self.prod_svc.get_categorias()
        dlg = ProductDialog(self, categorias=categorias)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.prod_svc.crear_producto(dlg.producto)
            ModernMessageBox.success(self, "Producto Creado", f"{dlg.producto.nombre} agregado al menú.")
            self.cargar_datos()

    def _editar_producto(self, producto):
        categorias = self.prod_svc.get_categorias()
        dlg = ProductDialog(self, producto=producto, categorias=categorias)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.prod_svc.actualizar_producto(dlg.producto)
            ModernMessageBox.success(self, "Producto Actualizado", f"{dlg.producto.nombre} actualizado.")
            self.cargar_datos()

    def _eliminar_producto(self, prod_id):
        result = ModernMessageBox.question(
            self, "Desactivar Producto",
            "¿Estás seguro de que deseas desactivar este producto?\nEl producto quedará como 'No disponible' en el menú."
        )
        if result == QDialog.DialogCode.Accepted:
            self.prod_svc.eliminar_producto(prod_id)
            self.cargar_datos()

    def _gestionar_variantes(self, producto):
        dlg = VariantesDialog(self, producto=producto, db=self.prod_svc)
        dlg.exec()
        self.cargar_datos()

    def _gestionar_categorias(self):
        dlg = CategoryManagerDialog(self, db=self.prod_svc)
        dlg.exec()
        self.cargar_datos()

    def _gestionar_combos(self):
        """Abre el diálogo de gestión de combos."""
        dlg = ComboManagementDialog(self, db=self.orden_svc)
        dlg.exec()
        self.cargar_datos()
