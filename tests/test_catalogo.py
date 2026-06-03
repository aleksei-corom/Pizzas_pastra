import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.models import Categoria, Producto
import config as app_config

class TestCatalogo(unittest.TestCase):
    def setUp(self):
        app_config.DB_PATH = ":memory:"
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None
        self.db = DatabaseManager()
        self.db.init_db()

    def tearDown(self):
        self.db.close()
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None

    def test_crud_categorias(self):
        # Create
        c1 = Categoria(nombre="Pizzas", activa=True)
        id1 = self.db.crear_categoria(c1)
        self.assertIsNotNone(id1)

        cats = self.db.get_categorias()
        self.assertEqual(len(cats), 1)
        self.assertEqual(cats[0].nombre, "Pizzas")

        # Soft Delete empty category
        self.db.eliminar_categoria(id1)
        cats_active = self.db.get_categorias(solo_activas=True)
        self.assertEqual(len(cats_active), 0)

    def test_crud_productos(self):
        c_id = self.db.crear_categoria(Categoria(nombre="Bebidas"))
        
        # Create Product
        p1 = Producto(nombre="Cola", precio=2.5, categoria_id=c_id)
        p1_id = self.db.crear_producto(p1)

        prods = self.db.get_productos(solo_disponibles=True)
        self.assertEqual(len(prods), 1)
        self.assertEqual(prods[0].nombre, "Cola")

        # Search
        res = self.db.buscar_productos("Col")
        self.assertEqual(len(res), 1)

        # Soft Delete product
        self.db.eliminar_producto(p1_id)
        prods_active = self.db.get_productos(solo_disponibles=True)
        self.assertEqual(len(prods_active), 0)

    def test_delete_categoria_con_productos_falla(self):
        c_id = self.db.crear_categoria(Categoria(nombre="Combos"))
        self.db.crear_producto(Producto(nombre="Combo 1", precio=10.0, categoria_id=c_id))

        with self.assertRaises(ValueError):
            self.db.eliminar_categoria(c_id)

if __name__ == '__main__':
    unittest.main()
