import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.producto_service import ProductoService
from database.models import Categoria, Producto
import config as app_config


class TestCatalogo(unittest.TestCase):
    def setUp(self):
        app_config.DB_PATH = ":memory:"
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None
        self.db = DatabaseManager()
        self.db.init_db()
        self.prod_svc = ProductoService(self.db)

    def tearDown(self):
        self.db.close()
        if hasattr(DatabaseManager, '_instance'):
            DatabaseManager._instance = None

    # ─── CRUD ───

    def test_crud_categorias(self):
        c1 = Categoria(nombre="Pizzas", activa=True)
        id1 = self.prod_svc.crear_categoria(c1)
        self.assertIsNotNone(id1)

        cats = self.prod_svc.get_categorias()
        self.assertEqual(len(cats), 1)
        self.assertEqual(cats[0].nombre, "Pizzas")

        self.prod_svc.eliminar_categoria(id1)
        cats_active = self.prod_svc.get_categorias(solo_activas=True)
        self.assertEqual(len(cats_active), 0)

    def test_crud_productos(self):
        c_id = self.prod_svc.crear_categoria(Categoria(nombre="Bebidas"))

        p1 = Producto(nombre="Cola", precio=2.5, categoria_id=c_id)
        p1_id = self.prod_svc.crear_producto(p1)

        prods = self.prod_svc.get_productos(solo_disponibles=True)
        self.assertEqual(len(prods), 1)
        self.assertEqual(prods[0].nombre, "Cola")

        res = self.prod_svc.buscar_productos("Col")
        self.assertEqual(len(res), 1)

        self.prod_svc.eliminar_producto(p1_id)
        prods_active = self.prod_svc.get_productos(solo_disponibles=True)
        self.assertEqual(len(prods_active), 0)

    def test_delete_categoria_con_productos_falla(self):
        c_id = self.prod_svc.crear_categoria(Categoria(nombre="Combos"))
        self.prod_svc.crear_producto(Producto(nombre="Combo 1", precio=10.0, categoria_id=c_id))

        with self.assertRaises(ValueError):
            self.prod_svc.eliminar_categoria(c_id)

    # ─── TESTS DE CACHE ───

    def test_cache_get_categorias_mismo_objeto_sin_mutacion(self):
        """Sin mutaciones, get_categorias debe devolver el mismo objeto (cache hit)."""
        self.prod_svc.crear_categoria(Categoria(nombre="Pizzas"))
        self.prod_svc.crear_categoria(Categoria(nombre="Bebidas"))

        # Limpiar cache antes del test
        self.prod_svc._clear_cache()

        primera = self.prod_svc.get_categorias()
        segunda = self.prod_svc.get_categorias()

        self.assertIs(primera, segunda, "get_categorias debe devolver el mismo objeto en cache hit")

    def test_cache_get_categorias_se_invalida_al_crear(self):
        """Crear una categoria debe invalidar la cache de get_categorias."""
        self.prod_svc.crear_categoria(Categoria(nombre="Pizzas"))
        self.prod_svc._clear_cache()

        antes = self.prod_svc.get_categorias()
        self.assertEqual(len(antes), 1)

        self.prod_svc.crear_categoria(Categoria(nombre="Bebidas"))

        despues = self.prod_svc.get_categorias()
        self.assertEqual(len(despues), 2)
        self.assertIsNot(antes, despues, "La cache debe invalidarse al crear categoria")

    def test_cache_get_categorias_se_invalida_al_eliminar(self):
        """Eliminar una categoria debe invalidar la cache de get_categorias."""
        c_id = self.prod_svc.crear_categoria(Categoria(nombre="Pizzas"))
        self.prod_svc._clear_cache()

        antes = self.prod_svc.get_categorias()
        self.assertEqual(len(antes), 1)

        self.prod_svc.eliminar_categoria(c_id)

        despues = self.prod_svc.get_categorias(solo_activas=True)
        self.assertEqual(len(despues), 0)

    def test_cache_get_productos_mismo_objeto_sin_mutacion(self):
        """Sin mutaciones, get_productos debe devolver el mismo objeto (cache hit)."""
        c_id = self.prod_svc.crear_categoria(Categoria(nombre="Bebidas"))
        self.prod_svc.crear_producto(Producto(nombre="Cola", precio=2.5, categoria_id=c_id))
        self.prod_svc._clear_cache()

        primera = self.prod_svc.get_productos()
        segunda = self.prod_svc.get_productos()

        self.assertIs(primera, segunda, "get_productos debe devolver el mismo objeto en cache hit")

    def test_cache_get_productos_se_invalida_al_crear(self):
        """Crear un producto debe invalidar la cache de get_productos."""
        c_id = self.prod_svc.crear_categoria(Categoria(nombre="Bebidas"))
        self.prod_svc.crear_producto(Producto(nombre="Cola", precio=2.5, categoria_id=c_id))
        self.prod_svc._clear_cache()

        antes = self.prod_svc.get_productos()
        self.assertEqual(len(antes), 1)

        self.prod_svc.crear_producto(Producto(nombre="Te", precio=1.5, categoria_id=c_id))

        despues = self.prod_svc.get_productos()
        self.assertEqual(len(despues), 2)
        self.assertIsNot(antes, despues, "La cache debe invalidarse al crear producto")

    def test_cache_get_productos_se_invalida_al_eliminar(self):
        """Eliminar un producto debe invalidar la cache de get_productos."""
        c_id = self.prod_svc.crear_categoria(Categoria(nombre="Bebidas"))
        p_id = self.prod_svc.crear_producto(Producto(nombre="Cola", precio=2.5, categoria_id=c_id))
        self.prod_svc._clear_cache()

        antes = self.prod_svc.get_productos(solo_disponibles=True)
        self.assertEqual(len(antes), 1)

        self.prod_svc.eliminar_producto(p_id)

        despues = self.prod_svc.get_productos(solo_disponibles=True)
        self.assertEqual(len(despues), 0)

    def test_cache_get_productos_se_invalida_al_actualizar(self):
        """Actualizar un producto debe invalidar la cache de get_productos."""
        c_id = self.prod_svc.crear_categoria(Categoria(nombre="Bebidas"))
        p_id = self.prod_svc.crear_producto(Producto(nombre="Cola", precio=2.5, categoria_id=c_id))
        self.prod_svc._clear_cache()

        antes = self.prod_svc.get_productos()
        self.assertEqual(antes[0].nombre, "Cola")

        prod_actualizado = Producto(id=p_id, nombre="Pepsi", precio=2.5, categoria_id=c_id)
        self.prod_svc.actualizar_producto(prod_actualizado)

        despues = self.prod_svc.get_productos()
        self.assertEqual(despues[0].nombre, "Pepsi")
        self.assertIsNot(antes, despues, "La cache debe invalidarse al actualizar producto")

    def test_cache_buscar_productos_mismo_objeto(self):
        """Sin mutaciones, buscar_productos debe devolver el mismo objeto (cache hit)."""
        c_id = self.prod_svc.crear_categoria(Categoria(nombre="Bebidas"))
        self.prod_svc.crear_producto(Producto(nombre="Cola", precio=2.5, categoria_id=c_id))
        self.prod_svc._clear_cache()

        primera = self.prod_svc.buscar_productos("Col")
        segunda = self.prod_svc.buscar_productos("Col")

        self.assertIs(primera, segunda, "buscar_productos debe devolver el mismo objeto en cache hit")

    def test_cache_buscar_productos_se_invalida_al_crear(self):
        """Crear un producto debe invalidar la cache de buscar_productos."""
        c_id = self.prod_svc.crear_categoria(Categoria(nombre="Bebidas"))
        self.prod_svc.crear_producto(Producto(nombre="Cola", precio=2.5, categoria_id=c_id))
        self.prod_svc._clear_cache()

        antes = self.prod_svc.buscar_productos("Col")
        self.assertEqual(len(antes), 1)

        self.prod_svc.crear_producto(Producto(nombre="Cola Light", precio=2.5, categoria_id=c_id))

        despues = self.prod_svc.buscar_productos("Col")
        self.assertEqual(len(despues), 2)
        self.assertIsNot(antes, despues, "La cache debe invalidarse al crear producto")

    def test_cache_clear_efecto_en_todas_las_caches(self):
        """_clear_cache debe invalidar get_categorias, get_productos y buscar_productos simultaneamente."""
        c_id = self.prod_svc.crear_categoria(Categoria(nombre="Bebidas"))
        self.prod_svc.crear_producto(Producto(nombre="Cola", precio=2.5, categoria_id=c_id))
        self.prod_svc._clear_cache()

        cats = self.prod_svc.get_categorias()
        prods = self.prod_svc.get_productos()
        busq = self.prod_svc.buscar_productos("Col")

        # Todas las caches estan llenas
        self.assertIs(self.prod_svc.get_categorias(), cats)
        self.assertIs(self.prod_svc.get_productos(), prods)
        self.assertIs(self.prod_svc.buscar_productos("Col"), busq)

        # Limpiar cache
        self.prod_svc._clear_cache()

        # Despues de limpiar, deben ser objetos nuevos
        self.assertIsNot(self.prod_svc.get_categorias(), cats)
        self.assertIsNot(self.prod_svc.get_productos(), prods)
        self.assertIsNot(self.prod_svc.buscar_productos("Col"), busq)

    def test_cache_args_distintos_no_comparten_cache(self):
        """Diferentes argumentos deben producir diferentes entradas de cache."""
        c_id = self.prod_svc.crear_categoria(Categoria(nombre="Bebidas"))
        self.prod_svc.crear_producto(Producto(nombre="Cola", precio=2.5, categoria_id=c_id))
        self.prod_svc._clear_cache()

        # Mismos args = mismo objeto
        a1 = self.prod_svc.get_productos(categoria_id=c_id)
        a2 = self.prod_svc.get_productos(categoria_id=c_id)
        self.assertIs(a1, a2, "Mismos args deben dar cache hit")

        # Args diferentes = objeto diferente
        b = self.prod_svc.get_productos()  # sin filtro
        self.assertIsNot(a1, b, "Args diferentes deben ser cache miss")


if __name__ == '__main__':
    unittest.main()
