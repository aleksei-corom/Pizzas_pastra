import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.models import Categoria, Producto, Orden, OrdenItem
import config as app_config

class TestOrdenes(unittest.TestCase):
    def setUp(self):
        app_config.DB_PATH = ":memory:"
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None
        self.db = DatabaseManager()
        self.db.init_db()

        # Configurar datos iniciales para las órdenes
        self.cat_id = self.db.crear_categoria(Categoria(nombre="Pizzas"))
        self.prod1_id = self.db.crear_producto(Producto(nombre="Margarita", precio=10.0, categoria_id=self.cat_id))
        self.prod2_id = self.db.crear_producto(Producto(nombre="Pepperoni", precio=15.0, categoria_id=self.cat_id))

    def tearDown(self):
        self.db.close()
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None

    def test_creacion_orden_calculos(self):
        orden = Orden(cliente_nombre="Juan Perez", tipo="delivery")
        item1 = OrdenItem(producto_id=self.prod1_id, producto_nombre="Margarita", cantidad=2, precio_unitario=10.0)
        item2 = OrdenItem(producto_id=self.prod2_id, producto_nombre="Pepperoni", cantidad=1, precio_unitario=15.0)
        
        orden.items.extend([item1, item2])
        
        # Subtotal debería ser 20 + 15 = 35.0
        # Total debería ser 35.0 + (35.0 * TAX_RATE)
        
        orden_guardada = self.db.crear_orden(orden)
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
        
        orden_guardada = self.db.crear_orden(orden)
        
        # Obtener y cambiar estado
        self.db.actualizar_estado_orden(orden_guardada.id, "preparing")
        
        orden_actualizada = [o for o in self.db.get_ordenes() if o.id == orden_guardada.id][0]
        self.assertEqual(orden_actualizada.estado, "preparing")

if __name__ == '__main__':
    unittest.main()
