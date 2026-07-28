"""Tests unitarios para OrdenService."""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.auth_service import AuthService
from database.producto_service import ProductoService
from database.orden_service import OrdenService
from database.models import Categoria, Producto, Orden, OrdenItem, Combo, ComboItem
import config as app_config


class TestOrdenes(unittest.TestCase):
    def setUp(self):
        app_config.DB_PATH = ":memory:"
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None
        self.db = DatabaseManager()
        self.db.init_db()
        self.prod_svc = ProductoService(self.db)
        self.orden_svc = OrdenService(self.db)

        self.cat_id = self.prod_svc.crear_categoria(Categoria(nombre="Pizzas"))
        self.prod1_id = self.prod_svc.crear_producto(Producto(nombre="Margarita", precio=10.0, categoria_id=self.cat_id))
        self.prod2_id = self.prod_svc.crear_producto(Producto(nombre="Pepperoni", precio=15.0, categoria_id=self.cat_id))

    def tearDown(self):
        self.db.close()
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None

    # ─── CRUD BÁSICO ───

    def test_creacion_orden_calculos(self):
        orden = Orden(cliente_nombre="Juan Perez", tipo="delivery")
        item1 = OrdenItem(producto_id=self.prod1_id, producto_nombre="Margarita", cantidad=2, precio_unitario=10.0)
        item2 = OrdenItem(producto_id=self.prod2_id, producto_nombre="Pepperoni", cantidad=1, precio_unitario=15.0)

        orden.items.extend([item1, item2])

        orden_guardada = self.orden_svc.crear_orden(orden)
        self.assertIsNotNone(orden_guardada.id)
        self.assertIsNotNone(orden_guardada.numero)

        self.assertEqual(orden_guardada.subtotal, 35.0)
        impuesto_esperado = round(35.0 * app_config.TAX_RATE, 2)
        self.assertEqual(orden_guardada.impuesto, impuesto_esperado)
        self.assertEqual(orden_guardada.total, 35.0 + impuesto_esperado)
        self.assertEqual(orden_guardada.estado, "pending")

    def test_cambios_estado(self):
        orden = Orden(cliente_nombre="Maria Gomez", tipo="local")
        item = OrdenItem(producto_id=self.prod1_id, producto_nombre="Margarita", cantidad=1, precio_unitario=10.0)
        orden.items.append(item)

        orden_guardada = self.orden_svc.crear_orden(orden)

        self.orden_svc.actualizar_estado_orden(orden_guardada.id, "preparing")

        orden_actualizada = [o for o in self.orden_svc.get_ordenes() if o.id == orden_guardada.id][0]
        self.assertEqual(orden_actualizada.estado, "preparing")

    def test_get_ordenes_vacia(self):
        ordenes = self.orden_svc.get_ordenes()
        self.assertEqual(ordenes, ())

    def test_get_ordenes_con_items_count(self):
        orden = Orden(cliente_nombre="Test", tipo="local")
        orden.items.append(OrdenItem(producto_id=self.prod1_id, producto_nombre="Margarita", cantidad=2, precio_unitario=10.0))
        orden.items.append(OrdenItem(producto_id=self.prod2_id, producto_nombre="Pepperoni", cantidad=1, precio_unitario=15.0))
        self.orden_svc.crear_orden(orden)

        resultados = self.orden_svc.get_ordenes_con_items_count()
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]["items_count"], 3)

    # ─── DELIVERY ───

    def test_get_ordenes_delivery_pendientes(self):
        orden_local = Orden(cliente_nombre="Local", tipo="local")
        orden_local.items.append(OrdenItem(producto_id=self.prod1_id, producto_nombre="Margarita", cantidad=1, precio_unitario=10.0))
        self.orden_svc.crear_orden(orden_local)

        orden_delivery = Orden(cliente_nombre="Delivery", tipo="delivery")
        orden_delivery.items.append(OrdenItem(producto_id=self.prod1_id, producto_nombre="Margarita", cantidad=1, precio_unitario=10.0))
        self.orden_svc.crear_orden(orden_delivery)

        pendientes = self.orden_svc.get_ordenes_delivery_pendientes()
        self.assertEqual(len(pendientes), 1)
        self.assertEqual(pendientes[0].tipo, "delivery")

    def test_get_ordenes_en_delivery(self):
        orden = Orden(cliente_nombre="Test", tipo="delivery")
        orden.items.append(OrdenItem(producto_id=self.prod1_id, producto_nombre="Margarita", cantidad=1, precio_unitario=10.0))
        orden = self.orden_svc.crear_orden(orden)

        en_delivery = self.orden_svc.get_ordenes_en_delivery()
        self.assertEqual(len(en_delivery), 0)

        self.orden_svc.actualizar_estado_orden(orden.id, "en_delivery")
        en_delivery = self.orden_svc.get_ordenes_en_delivery()
        self.assertEqual(len(en_delivery), 1)

    def test_get_entregas_hoy(self):
        orden = Orden(cliente_nombre="Test", tipo="delivery")
        orden.items.append(OrdenItem(producto_id=self.prod1_id, producto_nombre="Margarita", cantidad=1, precio_unitario=10.0))
        self.orden_svc.crear_orden(orden)

        entregas = self.orden_svc.get_entregas_hoy()
        self.assertEqual(len(entregas), 1)

    # ─── COMBOS ───

    def test_crear_y_get_combos(self):
        combo = Combo(nombre="Combo Familiar", descripcion="2 pizzas + 1 bebida", precio_total=25.0, ahorro=5.0)
        combo.items.append(ComboItem(producto_id=self.prod1_id, producto_nombre="Margarita", cantidad=2, precio_individual=10.0))
        combo.items.append(ComboItem(producto_id=self.prod2_id, producto_nombre="Pepperoni", cantidad=1, precio_individual=15.0))
        combo_id = self.orden_svc.crear_combo(combo)
        self.assertIsNotNone(combo_id)

        combos = self.orden_svc.get_combos()
        self.assertEqual(len(combos), 1)
        self.assertEqual(combos[0].nombre, "Combo Familiar")
        self.assertEqual(combos[0].precio_total, 25.0)
        self.assertEqual(len(combos[0].items), 2)

    def test_get_combos_solo_activos(self):
        combo = Combo(nombre="Combo 1", precio_total=15.0, ahorro=3.0)
        cid = self.orden_svc.crear_combo(combo)
        self.orden_svc.toggle_combo(cid)

        todos = self.orden_svc.get_combos()
        activos = self.orden_svc.get_combos(solo_activos=True)
        self.assertEqual(len(todos), 1)
        self.assertEqual(len(activos), 0)

    def test_get_combo_items(self):
        combo = Combo(nombre="Combo", precio_total=20.0, ahorro=4.0)
        combo.items.append(ComboItem(producto_id=self.prod1_id, producto_nombre="Margarita", cantidad=1, precio_individual=10.0))
        combo_id = self.orden_svc.crear_combo(combo)

        items = self.orden_svc.get_combo_items(combo_id)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].producto_nombre, "Margarita")

    def test_eliminar_combo(self):
        combo = Combo(nombre="Combo", precio_total=15.0, ahorro=2.0)
        cid = self.orden_svc.crear_combo(combo)
        self.orden_svc.eliminar_combo(cid)
        combos = self.orden_svc.get_combos()
        self.assertEqual(len(combos), 0)

    def test_toggle_combo(self):
        combo = Combo(nombre="Combo", precio_total=15.0, ahorro=2.0)
        cid = self.orden_svc.crear_combo(combo)
        self.orden_svc.toggle_combo(cid)
        self.assertFalse(self.orden_svc.get_combos()[0].activo)
        self.orden_svc.toggle_combo(cid)
        self.assertTrue(self.orden_svc.get_combos()[0].activo)

    # ─── ESTADÍSTICAS ───

    def test_get_ventas_dia(self):
        orden = Orden(cliente_nombre="Test", tipo="local")
        orden.items.append(OrdenItem(producto_id=self.prod1_id, producto_nombre="Margarita", cantidad=2, precio_unitario=10.0))
        self.orden_svc.crear_orden(orden)

        ventas = self.orden_svc.get_ventas_dia()
        self.assertEqual(ventas["total_ordenes"], 1)
        self.assertGreater(ventas["total_ventas"], 0)

    def test_get_conteo_por_estado(self):
        o1 = Orden(cliente_nombre="Test1", tipo="local")
        o1.items.append(OrdenItem(producto_id=self.prod1_id, producto_nombre="Margarita", cantidad=1, precio_unitario=10.0))
        o1 = self.orden_svc.crear_orden(o1)
        self.orden_svc.actualizar_estado_orden(o1.id, "preparing")

        o2 = Orden(cliente_nombre="Test2", tipo="local")
        o2.items.append(OrdenItem(producto_id=self.prod1_id, producto_nombre="Margarita", cantidad=1, precio_unitario=10.0))
        self.orden_svc.crear_orden(o2)

        conteo = self.orden_svc.get_conteo_por_estado()
        self.assertEqual(conteo.get("preparing", 0), 1)
        self.assertEqual(conteo.get("pending", 0), 1)

    # ─── CACHE ───

    def test_cache_get_ordenes_mismo_objeto(self):
        self.orden_svc._clear_cache()
        a = self.orden_svc.get_ordenes()
        b = self.orden_svc.get_ordenes()
        self.assertIs(a, b)

    def test_cache_get_ordenes_se_invalida_al_crear(self):
        self.orden_svc._clear_cache()
        antes = self.orden_svc.get_ordenes()
        orden = Orden(cliente_nombre="Test", tipo="local")
        orden.items.append(OrdenItem(producto_id=self.prod1_id, producto_nombre="Margarita", cantidad=1, precio_unitario=10.0))
        self.orden_svc.crear_orden(orden)
        despues = self.orden_svc.get_ordenes()
        self.assertEqual(len(despues), 1)
        self.assertIsNot(antes, despues)

    def test_cache_get_ordenes_con_items_count_mismo_objeto(self):
        self.orden_svc._clear_cache()
        a = self.orden_svc.get_ordenes_con_items_count()
        b = self.orden_svc.get_ordenes_con_items_count()
        self.assertIs(a, b)

    def test_cache_get_ordenes_con_items_count_se_invalida_al_actualizar_estado(self):
        orden = Orden(cliente_nombre="Test", tipo="local")
        orden.items.append(OrdenItem(producto_id=self.prod1_id, producto_nombre="Margarita", cantidad=1, precio_unitario=10.0))
        orden = self.orden_svc.crear_orden(orden)
        self.orden_svc._clear_cache()

        antes = self.orden_svc.get_ordenes_con_items_count()
        self.orden_svc.actualizar_estado_orden(orden.id, "preparing")
        despues = self.orden_svc.get_ordenes_con_items_count()

        self.assertEqual(len(despues), 1)
        self.assertEqual(despues[0]["orden"].estado, "preparing")


if __name__ == '__main__':
    unittest.main()
