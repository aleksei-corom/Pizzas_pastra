"""Tests unitarios para database/seed_data.py - seed de datos iniciales."""
import unittest
import unittest.mock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from database.models import Categoria, Producto, ProductoVariante, ProductoIngrediente
from database.auth_service import AuthService
from database.config_service import ConfigService
import config as app_config


def _init_db():
    """Inicializa DB en memoria y retorna DatabaseManager."""
    app_config.DB_PATH = ":memory:"
    DatabaseManager._instance = None
    db = DatabaseManager()
    db.init_db()
    return db


class TestSeedDatabase(unittest.TestCase):
    """Pruebas para seed_database()."""

    def setUp(self):
        self.db = _init_db()

    def tearDown(self):
        self.db.close()
        DatabaseManager._instance = None

    def _count_tables(self):
        """Cuenta registros en cada tabla principal."""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM categorias")
        cats = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM productos")
        prods = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM configuracion")
        configs = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM producto_ingredientes")
        ings = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM producto_variantes")
        vars_ = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM combos")
        combos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM combo_items")
        items = cursor.fetchone()[0]
        return cats, prods, users, configs, ings, vars_, combos, items

    def test_seed_inserts_categories(self):
        """Debe insertar 6 categorías."""
        from database.seed_data import seed_database
        seed_database()
        cats, prods, users, configs, ings, vars_, combos, items = self._count_tables()
        self.assertEqual(cats, 6)

    def test_seed_inserts_products(self):
        """Debe insertar productos (24 productos de demo)."""
        from database.seed_data import seed_database
        seed_database()
        cats, prods, users, configs, ings, vars_, combos, items = self._count_tables()
        self.assertEqual(prods, 24)

    def test_seed_inserts_admin_user(self):
        """Debe insertar el usuario admin por defecto."""
        from database.seed_data import seed_database
        seed_database()
        cats, prods, users, configs, ings, vars_, combos, items = self._count_tables()
        self.assertGreaterEqual(users, 1)

    def test_seed_admin_user_can_login(self):
        """El usuario admin debe poder autenticarse."""
        from database.seed_data import seed_database
        seed_database()
        auth_svc = AuthService(self.db)
        user = auth_svc.verificar_password("admin", "admin123")
        self.assertIsNotNone(user)
        self.assertEqual(user.rol, "admin")

    def test_seed_inserts_config(self):
        """Debe insertar valores de configuración por defecto."""
        from database.seed_data import seed_database
        seed_database()
        cfg_svc = ConfigService()
        self.assertIsNotNone(cfg_svc.get_config("business_name"))
        self.assertIsNotNone(cfg_svc.get_config("tax_rate"))

    def test_seed_inserts_ingredients(self):
        """Debe insertar ingredientes adicionales."""
        from database.seed_data import seed_database
        seed_database()
        cats, prods, users, configs, ings, vars_, combos, items = self._count_tables()
        self.assertEqual(ings, 14)

    def test_seed_inserts_variants(self):
        """Debe insertar variantes (4 por cada producto de pizza, 6 pizzas = 24 variantes)."""
        from database.seed_data import seed_database
        seed_database()
        cats, prods, users, configs, ings, vars_, combos, items = self._count_tables()
        self.assertEqual(vars_, 24)

    def test_seed_inserts_combos(self):
        """Debe insertar combos y items de combo."""
        from database.seed_data import seed_database
        seed_database()
        cats, prods, users, configs, ings, vars_, combos, items = self._count_tables()
        self.assertEqual(combos, 6)
        self.assertGreater(items, 0)

    def test_seed_skip_if_not_empty(self):
        """Si la DB no está vacía, solo debe insertar config defaults (no duplicar datos)."""
        from database.seed_data import seed_database
        # Primera llamada: llena la DB
        seed_database()
        cats_1, prods_1, _, _, _, _, _, _ = self._count_tables()

        # Segunda llamada: DB no está vacía, solo agrega config
        seed_database()
        cats_2, prods_2, _, _, _, _, _, _ = self._count_tables()

        self.assertEqual(cats_1, cats_2)
        self.assertEqual(prods_1, prods_2)

    def test_seed_creates_correct_category_data(self):
        """Las categorías deben tener nombres, iconos y orden correctos."""
        from database.seed_data import seed_database
        seed_database()

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT nombre, icono, orden FROM categorias ORDER BY orden")
        rows = cursor.fetchall()

        expected = [
            ("Pizzas", "🍕", 1),
            ("Hamburguesas", "🍔", 2),
            ("Hot Dogs", "🌭", 3),
            ("Complementos", "🍟", 4),
            ("Bebidas", "🥤", 5),
            ("Postres", "🍰", 6),
        ]
        for (nombre, icono, orden), (exp_name, exp_icono, exp_orden) in zip(rows, expected):
            self.assertEqual(nombre, exp_name)
            self.assertEqual(icono, exp_icono)
            self.assertEqual(orden, exp_orden)

    def test_seed_creates_correct_product_examples(self):
        """Productos específicos deben existir con precio correcto."""
        from database.seed_data import seed_database
        seed_database()

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT nombre, precio FROM productos WHERE nombre = ?", ("Pizza Margarita",))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertAlmostEqual(row[1], 8.50)

        cursor.execute("SELECT nombre, precio FROM productos WHERE nombre = ?", ("Coca-Cola",))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertAlmostEqual(row[1], 1.50)

        cursor.execute("SELECT nombre, precio FROM productos WHERE nombre = ?", ("Hamburguesa Clásica",))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertAlmostEqual(row[1], 6.50)

    def test_seed_variants_have_correct_prices(self):
        """Las variantes deben tener precios adicionales correctos."""
        from database.seed_data import seed_database
        seed_database()

        cursor = self.db.conn.cursor()
        # Personal = -2.00
        cursor.execute("""
            SELECT v.nombre, v.precio_adicional FROM producto_variantes v
            JOIN productos p ON p.id = v.producto_id
            WHERE p.nombre = ? AND v.nombre = ?
        """, ("Pizza Margarita", "Personal"))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertAlmostEqual(row[1], -2.00)

        # Jumbo = +5.00
        cursor.execute("""
            SELECT v.nombre, v.precio_adicional FROM producto_variantes v
            JOIN productos p ON p.id = v.producto_id
            WHERE p.nombre = ? AND v.nombre = ?
        """, ("Pizza Margarita", "Jumbo"))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertAlmostEqual(row[1], 5.00)

    def test_seed_combos_have_correct_ahorro(self):
        """Los combos deben tener ahorro calculado correctamente."""
        from database.seed_data import seed_database
        seed_database()

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT nombre, precio_total, ahorro FROM combos ORDER BY nombre")
        rows = cursor.fetchall()

        # Combo Familiar: Pizza Suprema($13) + 2 Cola($1.5x2=$3) + Papas Fritas($2.5) = $18.50
        # precio_total = $18.00, ahorro = 18.50 - 18.00 = $0.50
        for nombre, precio_total, ahorro in rows:
            if nombre == "Combo Familiar":
                self.assertAlmostEqual(precio_total, 18.00)
                self.assertAlmostEqual(ahorro, 0.50)

    def test_seed_config_defaults_sets_all_keys(self):
        """_seed_config_defaults debe establecer todas las claves de configuración."""
        from database.seed_data import _seed_config_defaults
        _seed_config_defaults()

        cfg_svc = ConfigService()
        expected_keys = [
            "business_name", "business_slogan", "business_phone", "business_address",
            "currency_symbol", "currency_code", "tax_rate",
            "printer_name", "printer_auto_cut", "printer_paper_width",
            "printer_codepage", "printer_print_qr", "printer_save_pdf",
        ]
        for key in expected_keys:
            self.assertIsNotNone(cfg_svc.get_config(key), f"Config '{key}' debe existir")

    def test_seed_admin_user_creates_if_no_users(self):
        """_seed_admin_user debe crear admin si no hay usuarios."""
        from database.seed_data import _seed_admin_user
        auth_svc = AuthService(self.db)
        _seed_admin_user(auth_svc)

        user = auth_svc.verificar_password("admin", "admin123")
        self.assertIsNotNone(user)

    def test_seed_admin_user_skips_if_users_exist(self):
        """_seed_admin_user no debe crear admin si ya hay usuarios."""
        from database.seed_data import _seed_admin_user
        auth_svc = AuthService(self.db)
        # Crear un usuario primero
        auth_svc.crear_usuario("existing", "pass123", "Existing", "admin")
        # Llamar seed_admin_user — no debe crear otro
        _seed_admin_user(auth_svc)

        users = auth_svc.get_usuarios()
        self.assertEqual(len(users), 1)  # Solo el que creamos

    def test_seed_variants_creates_four_per_pizza(self):
        """_seed_variants debe crear 4 variantes por producto de pizza."""
        from database.seed_data import _seed_variants
        from database.producto_service import ProductoService

        prod_svc = ProductoService(self.db)
        cat_id = prod_svc.crear_categoria(Categoria(nombre="Pizzas", icono="🍕"))
        prod_svc.crear_producto(Producto(nombre="Pizza Test", precio=10.0, categoria_id=cat_id))
        cat_ids = {"Pizzas": cat_id}

        _seed_variants(prod_svc, cat_ids)

        variantes = prod_svc.get_variantes(1)
        self.assertEqual(len(variantes), 4)

        nombres = [v.nombre for v in variantes]
        self.assertIn("Personal", nombres)
        self.assertIn("Mediana", nombres)
        self.assertIn("Familiar", nombres)
        self.assertIn("Jumbo", nombres)

    def test_seed_variants_no_pizza_category(self):
        """_seed_variants no debe fallar si no hay categoría Pizzas."""
        from database.seed_data import _seed_variants
        from database.producto_service import ProductoService
        prod_svc = ProductoService(self.db)
        try:
            _seed_variants(prod_svc, {})
        except Exception as e:
            self.fail(f"_seed_variants lanzó excepción con dict vacío: {e}")

    def test_seed_ingredients_creates_all(self):
        """_seed_ingredients debe crear 14 ingredientes."""
        from database.seed_data import _seed_ingredients
        from database.producto_service import ProductoService
        prod_svc = ProductoService(self.db)

        _seed_ingredients(prod_svc)

        ings = prod_svc.get_ingredientes()
        self.assertEqual(len(ings), 14)

    def test_seed_ingredients_have_correct_categories(self):
        """Los ingredientes deben tener categorías variadas."""
        from database.seed_data import _seed_ingredients
        from database.producto_service import ProductoService
        prod_svc = ProductoService(self.db)

        _seed_ingredients(prod_svc)

        ings = prod_svc.get_ingredientes()
        categorias = set(i.categoria for i in ings)
        self.assertIn("Quesos", categorias)
        self.assertIn("Carnes", categorias)
        self.assertIn("Vegetales", categorias)
        self.assertIn("Salsas", categorias)

    def _create_all_combo_products(self, prod_svc, cat_id):
        """Helper: crea todos los productos referenciados por combos_data en seed_data.py."""
        combo_product_names = [
            ("Pizza Suprema", 13.0), ("Coca-Cola", 1.5), ("Papas Fritas", 2.5),
            ("Pizza Margarita", 8.5), ("Hamburguesa Clásica", 6.5), ("Sprite", 1.5),
            ("Hamburguesa Doble", 9.0), ("Aros de Cebolla", 3.0), ("Cerveza", 3.0),
            ("Hot Dog Clásico", 3.5), ("Nuggets x6", 4.0), ("Jugo Natural", 2.5),
            ("Helado", 2.5), ("Brownie", 3.5),
        ]
        for nombre, precio in combo_product_names:
            prod_svc.crear_producto(Producto(nombre=nombre, precio=precio, categoria_id=cat_id, disponible=True))

    def test_seed_combos_creates_six_combos(self):
        """_seed_combos debe crear 6 combos."""
        from database.seed_data import _seed_combos
        from database.producto_service import ProductoService
        from database.orden_service import OrdenService

        prod_svc = ProductoService(self.db)
        orden_svc = OrdenService(self.db)

        cat_id = prod_svc.crear_categoria(Categoria(nombre="Test", icono="🍕"))
        self._create_all_combo_products(prod_svc, cat_id)

        _seed_combos(prod_svc, orden_svc, {})

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM combos")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 6)

        cursor.execute("SELECT COUNT(*) FROM combo_items")
        items_count = cursor.fetchone()[0]
        self.assertGreater(items_count, 0)

    def test_seed_combos_has_named_combos(self):
        """Los combos deben tener nombres específicos."""
        from database.seed_data import _seed_combos
        from database.producto_service import ProductoService
        from database.orden_service import OrdenService

        prod_svc = ProductoService(self.db)
        orden_svc = OrdenService(self.db)

        cat_id = prod_svc.crear_categoria(Categoria(nombre="Test", icono="🍕"))
        self._create_all_combo_products(prod_svc, cat_id)

        _seed_combos(prod_svc, orden_svc, {})

        cursor = self.db.conn.cursor()
        cursor.execute("SELECT nombre FROM combos ORDER BY nombre")
        rows = cursor.fetchall()
        names = [r[0] for r in rows]
        self.assertIn("Combo Familiar", names)
        self.assertIn("Combo Pizza + Bebida", names)
        self.assertIn("Combo Hamburguesa", names)

    def test_seed_combos_without_products(self):
        """_seed_combos no debe fallar si no hay productos."""
        from database.seed_data import _seed_combos
        from database.producto_service import ProductoService
        from database.orden_service import OrdenService
        prod_svc = ProductoService(self.db)
        orden_svc = OrdenService(self.db)

        try:
            _seed_combos(prod_svc, orden_svc, {"Pizzas": 999})
        except Exception as e:
            self.fail(f"_seed_combos lanzó excepción sin productos: {e}")


if __name__ == '__main__':
    unittest.main()
