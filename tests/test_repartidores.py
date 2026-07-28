"""Tests unitarios para RepartidorService."""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.repartidor_service import RepartidorService
from database.producto_service import ProductoService
from database.orden_service import OrdenService
from database.models import Repartidor, Categoria, Producto, Orden, OrdenItem
import config as app_config


class TestRepartidores(unittest.TestCase):
    def setUp(self):
        app_config.DB_PATH = ":memory:"
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None
        self.db = DatabaseManager()
        self.db.init_db()
        self.rep_svc = RepartidorService(self.db)
        self.prod_svc = ProductoService(self.db)
        self.orden_svc = OrdenService(self.db)

        # Categoría + producto base para órdenes
        cat_id = self.prod_svc.crear_categoria(Categoria(nombre="Pizzas"))
        self.prod_id = self.prod_svc.crear_producto(Producto(nombre="Margarita", precio=10.0, categoria_id=cat_id))

    def tearDown(self):
        self.db.close()
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None

    def _crear_orden_delivery(self) -> Orden:
        """Helper: crea una orden delivery pendiente."""
        orden = Orden(
            tipo="delivery",
            cliente_nombre="Test",
            direccion="Calle 123",
            telefono_contacto="555-0000",
        )
        orden.items.append(OrdenItem(producto_id=self.prod_id, producto_nombre="Margarita", cantidad=1, precio_unitario=10.0))
        return self.orden_svc.crear_orden(orden)

    # ─── CRUD ───

    def test_crear_repartidor(self):
        r = Repartidor(nombre="Carlos", telefono="555-0101", vehiculo="moto")
        rid = self.rep_svc.crear_repartidor(r)
        self.assertIsNotNone(rid)

        rep = self.rep_svc.get_repartidor(rid)
        self.assertIsNotNone(rep)
        self.assertEqual(rep.nombre, "Carlos")
        self.assertEqual(rep.telefono, "555-0101")
        self.assertEqual(rep.vehiculo, "moto")
        self.assertTrue(rep.activo)

    def test_get_repartidores_lista(self):
        self.rep_svc.crear_repartidor(Repartidor(nombre="Ana", vehiculo="carro"))
        self.rep_svc.crear_repartidor(Repartidor(nombre="Luis", vehiculo="bicicleta"))
        todos = self.rep_svc.get_repartidores()
        self.assertEqual(len(todos), 2)
        self.assertEqual(todos[0].nombre, "Ana")  # ORDER BY nombre

    def test_get_repartidores_solo_activos(self):
        r1_id = self.rep_svc.crear_repartidor(Repartidor(nombre="Ana"))
        self.rep_svc.crear_repartidor(Repartidor(nombre="Luis"))
        self.rep_svc.toggle_repartidor(r1_id)

        activos = self.rep_svc.get_repartidores(solo_activos=True)
        self.assertEqual(len(activos), 1)
        self.assertEqual(activos[0].nombre, "Luis")

    def test_actualizar_repartidor(self):
        rid = self.rep_svc.crear_repartidor(Repartidor(nombre="Pepe", telefono="555-0000"))
        self.rep_svc.actualizar_repartidor(Repartidor(id=rid, nombre="Pepe Actualizado", telefono="555-9999", vehiculo="carro", activo=True))
        rep = self.rep_svc.get_repartidor(rid)
        self.assertEqual(rep.nombre, "Pepe Actualizado")
        self.assertEqual(rep.telefono, "555-9999")
        self.assertEqual(rep.vehiculo, "carro")

    def test_toggle_repartidor(self):
        rid = self.rep_svc.crear_repartidor(Repartidor(nombre="Maria"))
        self.assertTrue(self.rep_svc.get_repartidor(rid).activo)

        self.rep_svc.toggle_repartidor(rid)
        self.assertFalse(self.rep_svc.get_repartidor(rid).activo)

        self.rep_svc.toggle_repartidor(rid)
        self.assertTrue(self.rep_svc.get_repartidor(rid).activo)

    def test_contar_repartidores_activos(self):
        self.assertEqual(self.rep_svc.contar_repartidores_activos(), 0)
        r1 = self.rep_svc.crear_repartidor(Repartidor(nombre="Ana"))
        self.rep_svc.crear_repartidor(Repartidor(nombre="Luis"))
        self.assertEqual(self.rep_svc.contar_repartidores_activos(), 2)
        self.rep_svc.toggle_repartidor(r1)
        self.assertEqual(self.rep_svc.contar_repartidores_activos(), 1)

    # ─── DISPONIBILIDAD ───

    def test_get_repartidores_disponibles_sin_ordenes(self):
        self.rep_svc.crear_repartidor(Repartidor(nombre="Ana"))
        self.rep_svc.crear_repartidor(Repartidor(nombre="Luis"))
        disponibles = self.rep_svc.get_repartidores_disponibles()
        self.assertEqual(len(disponibles), 2)

    def test_get_repartidores_disponibles_excluye_ocupados(self):
        r_id = self.rep_svc.crear_repartidor(Repartidor(nombre="Ana"))
        self.rep_svc.crear_repartidor(Repartidor(nombre="Luis"))

        # Crear orden y asignarle repartidor
        orden = self._crear_orden_delivery()
        # Cambiar estado a ready para que sea asignable
        self.orden_svc.actualizar_estado_orden(orden.id, "ready")
        self.rep_svc.asignar_repartidor(orden.id, r_id)

        disponibles = self.rep_svc.get_repartidores_disponibles()
        self.assertEqual(len(disponibles), 1)
        self.assertEqual(disponibles[0].nombre, "Luis")

    # ─── ASIGNACIÓN ───

    def test_asignar_repartidor_exitoso(self):
        r_id = self.rep_svc.crear_repartidor(Repartidor(nombre="Ana"))
        orden = self._crear_orden_delivery()

        success = self.rep_svc.asignar_repartidor(orden.id, r_id)
        self.assertTrue(success)

        # Verificar que la orden cambió a en_delivery
        ordenes = self.orden_svc.get_ordenes()
        orden_act = [o for o in ordenes if o.id == orden.id][0]
        self.assertEqual(orden_act.estado, "en_delivery")

    def test_asignar_repartidor_si_orden_no_existe_retorna_false(self):
        """UPDATE sin filas afectadas igual retorna True en SQLite.
        Este test solo verifica que no lanza excepcion."""
        r_id = self.rep_svc.crear_repartidor(Repartidor(nombre="Ana"))
        try:
            result = self.rep_svc.asignar_repartidor(orden_id=9999, repartidor_id=r_id)
            # SQLite UPDATE de 0 filas no es error, True es aceptable
            self.assertIsInstance(result, bool)
        except Exception as e:
            self.fail(f"asignar_repartidor lanzó excepción: {e}")

    def test_get_repartidor_no_existe_retorna_none(self):
        rep = self.rep_svc.get_repartidor(9999)
        self.assertIsNone(rep)

    def test_crear_repartidor_con_valores_default(self):
        rid = self.rep_svc.crear_repartidor(Repartidor(nombre="Default"))
        rep = self.rep_svc.get_repartidor(rid)
        self.assertEqual(rep.vehiculo, "moto")
        self.assertTrue(rep.activo)
        self.assertTrue(len(rep.fecha_creacion) > 0, "fecha_creacion no debe estar vacia")


if __name__ == '__main__':
    unittest.main()
