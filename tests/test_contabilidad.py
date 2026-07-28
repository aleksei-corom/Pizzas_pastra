"""Tests unitarios para ContabilidadService."""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.contabilidad_service import ContabilidadService
from database.producto_service import ProductoService
from database.orden_service import OrdenService
from database.models import Transaccion, Categoria, Producto, Orden, OrdenItem


class TestContabilidad(unittest.TestCase):
    def setUp(self):
        import config as app_config
        app_config.DB_PATH = ":memory:"

        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None

        self.db = DatabaseManager()
        self.db.init_db()
        self.cont_svc = ContabilidadService(self.db)
        self.prod_svc = ProductoService(self.db)
        self.orden_svc = OrdenService(self.db)

        cat_id = self.prod_svc.crear_categoria(Categoria(nombre="Pizzas"))
        self.prod_svc.crear_producto(Producto(nombre="Pizza", categoria_id=cat_id, precio=100.0))

    def tearDown(self):
        self.db.close()
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None

    # ─── CRUD ───

    def test_crear_transaccion_y_balance(self):
        t1 = Transaccion(
            tipo="ingreso",
            monto=500.0,
            descripcion="Venta 1",
            fecha="2026-06-01T12:00:00"
        )
        self.cont_svc.crear_transaccion(t1)

        t2 = Transaccion(
            tipo="egreso",
            monto=100.0,
            descripcion="Compra de insumos",
            fecha="2026-06-01T13:00:00",
            categoria="Insumos"
        )
        self.cont_svc.crear_transaccion(t2)

        transacciones = self.cont_svc.get_transacciones()
        self.assertEqual(len(transacciones), 2)

        balance = self.cont_svc.get_balance_contable()
        self.assertEqual(balance["total_ingresos"], 500.0)
        self.assertEqual(balance["total_egresos"], 100.0)
        self.assertEqual(balance["balance_neto"], 400.0)

    def test_crear_orden_genera_transaccion(self):
        orden = Orden(cliente_nombre="Test Cliente", tipo="local")
        item = OrdenItem(producto_id=1, producto_nombre="Pizza", cantidad=2, precio_unitario=100.0)
        orden.items.append(item)

        orden_guardada = self.orden_svc.crear_orden(orden)

        transacciones = self.cont_svc.get_transacciones()
        self.assertEqual(len(transacciones), 1)
        t = transacciones[0]
        self.assertEqual(t.tipo, "ingreso")
        self.assertEqual(t.monto, orden_guardada.total)
        self.assertEqual(t.referencia_orden_id, orden_guardada.id)
        self.assertIn("Venta #", t.descripcion)

    # ─── FILTROS ───

    def test_get_transacciones_filtro_por_fecha(self):
        self.cont_svc.crear_transaccion(Transaccion(tipo="ingreso", monto=100, fecha="2026-06-01T10:00:00"))
        self.cont_svc.crear_transaccion(Transaccion(tipo="ingreso", monto=200, fecha="2026-06-02T10:00:00"))

        todas = self.cont_svc.get_transacciones()
        self.assertEqual(len(todas), 2)

        filtradas = self.cont_svc.get_transacciones(fecha="2026-06-01")
        self.assertEqual(len(filtradas), 1)
        self.assertEqual(filtradas[0].monto, 100)

    def test_get_transacciones_filtro_por_categoria(self):
        self.cont_svc.crear_transaccion(Transaccion(tipo="egreso", monto=50, categoria="Insumos", fecha="2026-06-01T10:00:00"))
        self.cont_svc.crear_transaccion(Transaccion(tipo="egreso", monto=30, categoria="Servicios", fecha="2026-06-01T11:00:00"))

        filtradas = self.cont_svc.get_transacciones(categoria="Insumos")
        self.assertEqual(len(filtradas), 1)
        self.assertEqual(filtradas[0].monto, 50)

    def test_get_transacciones_filtro_por_tipo(self):
        self.cont_svc.crear_transaccion(Transaccion(tipo="ingreso", monto=500, fecha="2026-06-01T10:00:00"))
        self.cont_svc.crear_transaccion(Transaccion(tipo="egreso", monto=100, fecha="2026-06-01T11:00:00"))

        ingresos = self.cont_svc.get_transacciones(tipo="ingreso")
        egresos = self.cont_svc.get_transacciones(tipo="egreso")
        self.assertEqual(len(ingresos), 1)
        self.assertEqual(len(egresos), 1)

    def test_get_transacciones_filtros_combinados(self):
        self.cont_svc.crear_transaccion(Transaccion(tipo="egreso", monto=50, categoria="Insumos", fecha="2026-06-01T10:00:00"))
        self.cont_svc.crear_transaccion(Transaccion(tipo="egreso", monto=30, categoria="Insumos", fecha="2026-06-02T10:00:00"))
        self.cont_svc.crear_transaccion(Transaccion(tipo="ingreso", monto=500, categoria="Ventas", fecha="2026-06-01T11:00:00"))

        filtradas = self.cont_svc.get_transacciones(
            fecha="2026-06-01",
            tipo="egreso",
            categoria="Insumos",
        )
        self.assertEqual(len(filtradas), 1)
        self.assertEqual(filtradas[0].monto, 50)

    # ─── BALANCE ───

    def test_balance_vacio(self):
        balance = self.cont_svc.get_balance_contable()
        self.assertEqual(balance["total_ingresos"], 0)
        self.assertEqual(balance["total_egresos"], 0)
        self.assertEqual(balance["balance_neto"], 0)

    def test_balance_con_multiples_transacciones(self):
        self.cont_svc.crear_transaccion(Transaccion(tipo="ingreso", monto=100, fecha="2026-06-01T10:00:00"))
        self.cont_svc.crear_transaccion(Transaccion(tipo="ingreso", monto=50, fecha="2026-06-01T11:00:00"))
        self.cont_svc.crear_transaccion(Transaccion(tipo="egreso", monto=30, fecha="2026-06-01T12:00:00"))

        balance = self.cont_svc.get_balance_contable()
        self.assertEqual(balance["total_ingresos"], 150)
        self.assertEqual(balance["total_egresos"], 30)
        self.assertEqual(balance["balance_neto"], 120)

    def test_balance_con_solo_egresos(self):
        self.cont_svc.crear_transaccion(Transaccion(tipo="egreso", monto=100, fecha="2026-06-01T10:00:00"))

        balance = self.cont_svc.get_balance_contable()
        self.assertEqual(balance["total_ingresos"], 0)
        self.assertEqual(balance["total_egresos"], 100)
        self.assertEqual(balance["balance_neto"], -100)

    # ─── LÍMITES ───

    def test_get_transacciones_respeta_limit(self):
        for i in range(5):
            self.cont_svc.crear_transaccion(Transaccion(tipo="ingreso", monto=float(i), fecha=f"2026-06-01T{i:02d}:00:00"))

        todas = self.cont_svc.get_transacciones()
        self.assertEqual(len(todas), 5)

        limitadas = self.cont_svc.get_transacciones(limit=3)
        self.assertEqual(len(limitadas), 3)


if __name__ == '__main__':
    unittest.main()
