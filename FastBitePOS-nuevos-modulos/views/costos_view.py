"""Vista Analizador de Costos y Recetas.

Módulo diferenciador que permite:
- Construir recetas con desglose de ingredientes y costos
- Analizar márgenes de ganancia por producto
- Comparar costo real vs precio de venta
- Sugerir precios basados en margen objetivo
- Identificar ingredientes más costosos
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFrame, QProgressBar, QTabWidget, QDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from database.receta_service import RecetaService
from database.producto_service import ProductoService
from database.models import Receta
from views.layouts import create_page_header, create_stats_grid
from views.components import CardWidget, StatusBadge, ModernMessageBox
from views.components.receta_dialog import RecetaDialog
import config as app_config


class CostosView(QWidget):
    """Vista de análisis de costos y recetas con tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._svc = RecetaService()
        self._prod_svc = ProductoService()
        self._build_ui()
        self.cargar_datos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Header
        btn_nuevo = QPushButton("+ Nueva Receta")
        btn_nuevo.clicked.connect(self._nueva_receta)
        header = create_page_header(
            "\U0001f9c1  Costos y Recetas",
            "Analiza márgenes y costos reales de tus productos",
            actions=[btn_nuevo]
        )
        layout.addLayout(header)

        # Stats
        self._stats_layout = QHBoxLayout()
        layout.addLayout(self._stats_layout)

        # Tabs
        self._tabs = QTabWidget()
        self._tabs.setObjectName("main-tabs")

        # Tab 1: Análisis de márgenes
        self._tab_margenes = QWidget()
        self._build_tab_margenes()
        self._tabs.addTab(self._tab_margenes, "\U0001f4ca  Márgenes")

        # Tab 2: Recetas
        self._tab_recetas = QWidget()
        self._build_tab_recetas()
        self._tabs.addTab(self._tab_recetas, "\U0001f373  Recetas")

        # Tab 3: Ingredientes
        self._tab_ingredientes = QWidget()
        self._build_tab_ingredientes()
        self._tabs.addTab(self._tab_ingredientes, "\U0001f33f  Ingredientes")

        layout.addWidget(self._tabs, 1)

    # ─── TAB MÁRGENES ────────────────────────────────────────

    def _build_tab_margenes(self):
        layout = QVBoxLayout(self._tab_margenes)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        self._tabla_margenes = QTableWidget(0, 8)
        self._tabla_margenes.setHorizontalHeaderLabels([
            "Producto", "Categoría", "Precio Venta", "Costo/Porción",
            "Margen Bruto", "Margen Neto", "Precio Sugerido", ""
        ])
        self._tabla_margenes.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._tabla_margenes.horizontalHeader().setSectionResizeMode(
            7, QHeaderView.ResizeMode.Fixed
        )
        self._tabla_margenes.setColumnWidth(2, 100)
        self._tabla_margenes.setColumnWidth(3, 100)
        self._tabla_margenes.setColumnWidth(4, 100)
        self._tabla_margenes.setColumnWidth(5, 100)
        self._tabla_margenes.setColumnWidth(6, 110)
        self._tabla_margenes.setColumnWidth(7, 80)
        self._tabla_margenes.verticalHeader().setVisible(False)
        self._tabla_margenes.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla_margenes.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabla_margenes.setAlternatingRowColors(True)
        layout.addWidget(self._tabla_margenes, 1)

    # ─── TAB RECETAS ─────────────────────────────────────────

    def _build_tab_recetas(self):
        layout = QVBoxLayout(self._tab_recetas)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        self._tabla_recetas = QTableWidget(0, 6)
        self._tabla_recetas.setHorizontalHeaderLabels([
            "Receta", "Producto", "Porciones",
            "Costo Total", "Costo/Porción", ""
        ])
        self._tabla_recetas.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._tabla_recetas.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self._tabla_recetas.horizontalHeader().setSectionResizeMode(
            5, QHeaderView.ResizeMode.Fixed
        )
        self._tabla_recetas.setColumnWidth(2, 80)
        self._tabla_recetas.setColumnWidth(3, 100)
        self._tabla_recetas.setColumnWidth(4, 100)
        self._tabla_recetas.setColumnWidth(5, 80)
        self._tabla_recetas.verticalHeader().setVisible(False)
        self._tabla_recetas.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla_recetas.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabla_recetas.setAlternatingRowColors(True)
        layout.addWidget(self._tabla_recetas, 1)

    # ─── TAB INGREDIENTES ─────────────────────────────────────

    def _build_tab_ingredientes(self):
        layout = QVBoxLayout(self._tab_ingredientes)
        layout.setContentsMargins(0, 12, 0, 0)
        layout.setSpacing(12)

        lbl = QLabel("\U0001f33f  Top Ingredientes por Costo Total")
        lbl.setProperty("class", "section")
        layout.addWidget(lbl)

        self._tabla_ingredientes = QTableWidget(0, 3)
        self._tabla_ingredientes.setHorizontalHeaderLabels([
            "Ingrediente", "Costo Total", "Veces Usado"
        ])
        self._tabla_ingredientes.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self._tabla_ingredientes.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )
        self._tabla_ingredientes.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed
        )
        self._tabla_ingredientes.setColumnWidth(1, 120)
        self._tabla_ingredientes.setColumnWidth(2, 100)
        self._tabla_ingredientes.verticalHeader().setVisible(False)
        self._tabla_ingredientes.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla_ingredientes.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabla_ingredientes.setAlternatingRowColors(True)
        layout.addWidget(self._tabla_ingredientes, 1)

    # ─── CARGA DE DATOS ──────────────────────────────────────

    def cargar_datos(self):
        self._load_stats()
        self._load_margenes()
        self._load_recetas()
        self._load_ingredientes()

    def _load_stats(self):
        resumen = self._svc.get_resumen_costos()
        stats_data = [
            {'label': 'Recetas Activas', 'value': str(resumen['total_recetas']),
             'status': 'info'},
            {'label': 'Margen Promedio', 'value': f"{resumen['margen_promedio']}%",
             'status': 'success' if resumen['margen_promedio'] >= 60 else 'warning'},
            {'label': 'Costo Promedio', 'value': f"{app_config.CURRENCY_SYMBOL}{resumen['costo_promedio']:.2f}",
             'status': 'info'},
            {'label': 'Bajo Margen', 'value': str(len(resumen.get('productos_bajo_margen', []))),
             'badge': 'Atención' if resumen.get('productos_bajo_margen') else None,
             'status': 'danger' if resumen.get('productos_bajo_margen') else 'success'},
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

    def _load_margenes(self):
        analisis = self._svc.get_analisis_margenes()
        self._tabla_margenes.setRowCount(len(analisis))

        for i, a in enumerate(analisis):
            self._tabla_margenes.setItem(i, 0, QTableWidgetItem(a['producto_nombre']))
            self._tabla_margenes.setItem(i, 1, QTableWidgetItem(a['categoria_nombre']))
            self._tabla_margenes.setItem(i, 2, QTableWidgetItem(
                f"{app_config.CURRENCY_SYMBOL}{a['precio_venta']:.2f}"
            ))
            self._tabla_margenes.setItem(i, 3, QTableWidgetItem(
                f"{app_config.CURRENCY_SYMBOL}{a['costo_porcion']:.2f}"
            ))

            margen_bruto = a['margen_bruto']
            item_mb = QTableWidgetItem(f"{margen_bruto}%")
            # Colorear según margen
            if margen_bruto >= 65:
                item_mb.setForeground(QColor("#34d399"))
            elif margen_bruto >= 50:
                item_mb.setForeground(QColor("#fbbf24"))
            else:
                item_mb.setForeground(QColor("#f87171"))
            self._tabla_margenes.setItem(i, 4, item_mb)

            self._tabla_margenes.setItem(i, 5, QTableWidgetItem(
                f"{a['margen_neto']}%"
            ))

            sugerido = a['precio_sugerido']
            item_sug = QTableWidgetItem(
                f"{app_config.CURRENCY_SYMBOL}{sugerido:.2f}" if sugerido > 0 else "N/A"
            )
            if sugerido > a['precio_venta'] > 0:
                item_sug.setForeground(QColor("#f87171"))
            self._tabla_margenes.setItem(i, 6, item_sug)

            btn_edit = QPushButton("\U0001f4dd")
            btn_edit.setProperty("class", "ghost")
            btn_edit.setFixedWidth(50)
            rec_id = a['receta_id']
            btn_edit.clicked.connect(lambda checked, rid=rec_id: self._editar_receta(rid))
            self._tabla_margenes.setCellWidget(i, 7, btn_edit)

    def _load_recetas(self):
        recetas = self._svc.get_recetas()
        self._tabla_recetas.setRowCount(len(recetas))
        for i, r in enumerate(recetas):
            self._tabla_recetas.setItem(i, 0, QTableWidgetItem(r.nombre))
            prod_name = "Sin asociar"
            if r.producto_id:
                prod = self._prod_svc.get_producto(r.producto_id)
                if prod:
                    prod_name = prod.nombre
            self._tabla_recetas.setItem(i, 1, QTableWidgetItem(prod_name))
            self._tabla_recetas.setItem(i, 2, QTableWidgetItem(str(r.porciones)))
            self._tabla_recetas.setItem(i, 3, QTableWidgetItem(
                f"{app_config.CURRENCY_SYMBOL}{r.costo_total:.2f}"
            ))
            self._tabla_recetas.setItem(i, 4, QTableWidgetItem(
                f"{app_config.CURRENCY_SYMBOL}{r.costo_porcion:.2f}"
            ))

            btn_del = QPushButton("\u2716")
            btn_del.setProperty("class", "danger-ghost")
            btn_del.setFixedWidth(50)
            btn_del.clicked.connect(lambda checked, rid=r.id: self._eliminar_receta(rid))
            self._tabla_recetas.setCellWidget(i, 5, btn_del)

    def _load_ingredientes(self):
        ingredientes = self._svc.get_top_ingredientes_costo()
        self._tabla_ingredientes.setRowCount(len(ingredientes))
        for i, ing in enumerate(ingredientes):
            self._tabla_ingredientes.setItem(i, 0, QTableWidgetItem(ing['nombre']))
            self._tabla_ingredientes.setItem(i, 1, QTableWidgetItem(
                f"{app_config.CURRENCY_SYMBOL}{ing['costo_total']:.2f}"
            ))
            self._tabla_ingredientes.setItem(i, 2, QTableWidgetItem(str(ing['veces_usado'])))

    # ─── ACCIONES ────────────────────────────────────────────

    def _nueva_receta(self):
        productos = self._prod_svc.get_productos()
        dlg = RecetaDialog(productos=productos, parent=self)
        if dlg.exec():
            receta = dlg.get_receta()
            try:
                self._svc.crear_receta(receta)
                self.cargar_datos()
            except Exception as e:
                ModernMessageBox.error(self, "Error", f"No se pudo guardar: {e}")

    def _editar_receta(self, receta_id: int):
        receta = self._svc.get_receta(receta_id)
        if not receta:
            return
        productos = self._prod_svc.get_productos()
        dlg = RecetaDialog(productos=productos, receta=receta, parent=self)
        if dlg.exec():
            receta = dlg.get_receta()
            try:
                self._svc.actualizar_receta(receta)
                self.cargar_datos()
            except Exception as e:
                ModernMessageBox.error(self, "Error", f"No se pudo actualizar: {e}")

    def _eliminar_receta(self, receta_id: int):
        result = ModernMessageBox.question(
            self, "Eliminar Receta",
            "¿Estás seguro de eliminar esta receta?"
        )
        if result == QDialog.DialogCode.Accepted:
            self._svc.eliminar_receta(receta_id)
            self.cargar_datos()
