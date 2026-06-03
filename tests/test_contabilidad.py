import unittest
import os
import sys

# Ensure the root project directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.models import Transaccion

class TestContabilidad(unittest.TestCase):
    def setUp(self):
        import config as app_config
        app_config.DB_PATH = ":memory:" # Use in memory db
        
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None
            
        self.db = DatabaseManager()
        self.db.init_db()
        
        # Add mock product to avoid foreign key errors
        from database.models import Categoria, Producto
        cat_id = self.db.crear_categoria(Categoria(nombre="Pizzas"))
        self.db.crear_producto(Producto(nombre="Pizza", categoria_id=cat_id, precio=100.0))

    def tearDown(self):
        self.db.close()
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None

    def test_crear_transaccion_y_balance(self):
        # Crear un ingreso
        t1 = Transaccion(
            tipo="ingreso",
            monto=500.0,
            descripcion="Venta 1",
            fecha="2026-06-01T12:00:00"
        )
        self.db.crear_transaccion(t1)

        # Crear un egreso
        t2 = Transaccion(
            tipo="egreso",
            monto=100.0,
            descripcion="Compra de insumos",
            fecha="2026-06-01T13:00:00",
            categoria="Insumos"
        )
        self.db.crear_transaccion(t2)

        transacciones = self.db.get_transacciones()
        self.assertEqual(len(transacciones), 2)
        
        balance = self.db.get_balance_contable()
        self.assertEqual(balance["total_ingresos"], 500.0)
        self.assertEqual(balance["total_egresos"], 100.0)
        self.assertEqual(balance["balance_neto"], 400.0)

    def test_crear_orden_genera_transaccion(self):
        from database.models import Orden, OrdenItem
        # Crear una orden
        orden = Orden(cliente_nombre="Test Cliente", tipo="local")
        item = OrdenItem(producto_id=1, producto_nombre="Pizza", cantidad=2, precio_unitario=100.0)
        orden.items.append(item)
        
        # Guardar orden
        orden_guardada = self.db.crear_orden(orden)
        
        # Verificar que se creó una transacción
        transacciones = self.db.get_transacciones()
        self.assertEqual(len(transacciones), 1)
        t = transacciones[0]
        self.assertEqual(t.tipo, "ingreso")
        self.assertEqual(t.monto, orden_guardada.total)
        self.assertEqual(t.referencia_orden_id, orden_guardada.id)
        self.assertIn("Venta #", t.descripcion)

if __name__ == '__main__':
    unittest.main()

