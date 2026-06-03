"""Datos iniciales para la base de datos de Pizzas Pastra."""

from database.db_manager import DatabaseManager
from database.models import Categoria, Producto
import config


def seed_database():
    """Inserta categorías, productos y configuración demo si la DB está vacía."""
    db = DatabaseManager()

    if not db.is_empty():
        # Aún así aseguramos que existan las claves de configuración básicas
        _seed_config_defaults(db)
        return

    # ─── Categorías ───
    categorias = [
        Categoria(nombre="Pizzas", icono="🍕", orden=1),
        Categoria(nombre="Hamburguesas", icono="🍔", orden=2),
        Categoria(nombre="Hot Dogs", icono="🌭", orden=3),
        Categoria(nombre="Complementos", icono="🍟", orden=4),
        Categoria(nombre="Bebidas", icono="🥤", orden=5),
        Categoria(nombre="Postres", icono="🍰", orden=6),
    ]

    cat_ids = {}
    for cat in categorias:
        cat_id = db.crear_categoria(cat)
        cat_ids[cat.nombre] = cat_id

    # ─── Productos ───
    productos = [
        # Pizzas
        Producto(nombre="Pizza Margarita", descripcion="Salsa de tomate, mozzarella y albahaca",
                 precio=8.50, categoria_id=cat_ids["Pizzas"], icono="🍕"),
        Producto(nombre="Pizza Pepperoni", descripcion="Pepperoni, mozzarella y salsa de tomate",
                 precio=9.50, categoria_id=cat_ids["Pizzas"], icono="🍕"),
        Producto(nombre="Pizza Hawaiana", descripcion="Jamón, piña, mozzarella",
                 precio=10.00, categoria_id=cat_ids["Pizzas"], icono="🍕"),
        Producto(nombre="Pizza BBQ Chicken", descripcion="Pollo, cebolla, salsa BBQ, mozzarella",
                 precio=11.50, categoria_id=cat_ids["Pizzas"], icono="🍕"),
        Producto(nombre="Pizza 4 Quesos", descripcion="Mozzarella, cheddar, parmesano, gorgonzola",
                 precio=12.00, categoria_id=cat_ids["Pizzas"], icono="🧀"),
        Producto(nombre="Pizza Suprema", descripcion="Pepperoni, jamón, pimiento, champiñones, cebolla",
                 precio=13.00, categoria_id=cat_ids["Pizzas"], icono="🍕"),

        # Hamburguesas
        Producto(nombre="Hamburguesa Clásica", descripcion="Carne 150g, lechuga, tomate, cebolla",
                 precio=6.50, categoria_id=cat_ids["Hamburguesas"], icono="🍔"),
        Producto(nombre="Hamburguesa Doble", descripcion="Doble carne, doble queso, bacon",
                 precio=9.00, categoria_id=cat_ids["Hamburguesas"], icono="🍔"),
        Producto(nombre="Hamburguesa BBQ", descripcion="Carne, bacon, aros de cebolla, salsa BBQ",
                 precio=8.50, categoria_id=cat_ids["Hamburguesas"], icono="🍔"),
        Producto(nombre="Hamburguesa Veggie", descripcion="Hamburguesa vegetal, aguacate, lechuga",
                 precio=7.50, categoria_id=cat_ids["Hamburguesas"], icono="🥬"),

        # Hot Dogs
        Producto(nombre="Hot Dog Clásico", descripcion="Salchicha, mostaza, ketchup",
                 precio=3.50, categoria_id=cat_ids["Hot Dogs"], icono="🌭"),
        Producto(nombre="Hot Dog Especial", descripcion="Salchicha, queso, bacon, jalapeños",
                 precio=5.00, categoria_id=cat_ids["Hot Dogs"], icono="🌭"),

        # Complementos
        Producto(nombre="Papas Fritas", descripcion="Papas fritas crujientes",
                 precio=2.50, categoria_id=cat_ids["Complementos"], icono="🍟"),
        Producto(nombre="Aros de Cebolla", descripcion="Aros de cebolla empanizados",
                 precio=3.00, categoria_id=cat_ids["Complementos"], icono="🧅"),
        Producto(nombre="Nuggets x6", descripcion="6 piezas de nuggets de pollo",
                 precio=4.00, categoria_id=cat_ids["Complementos"], icono="🍗"),
        Producto(nombre="Ensalada César", descripcion="Lechuga, croutones, parmesano, aderezo césar",
                 precio=5.00, categoria_id=cat_ids["Complementos"], icono="🥗"),

        # Bebidas
        Producto(nombre="Coca-Cola", descripcion="Lata 355ml",
                 precio=1.50, categoria_id=cat_ids["Bebidas"], icono="🥤"),
        Producto(nombre="Sprite", descripcion="Lata 355ml",
                 precio=1.50, categoria_id=cat_ids["Bebidas"], icono="🥤"),
        Producto(nombre="Agua Mineral", descripcion="Botella 500ml",
                 precio=1.00, categoria_id=cat_ids["Bebidas"], icono="💧"),
        Producto(nombre="Jugo Natural", descripcion="Vaso 400ml (naranja, limón o piña)",
                 precio=2.50, categoria_id=cat_ids["Bebidas"], icono="🍊"),
        Producto(nombre="Cerveza", descripcion="Botella 330ml",
                 precio=3.00, categoria_id=cat_ids["Bebidas"], icono="🍺"),

        # Postres
        Producto(nombre="Brownie", descripcion="Brownie de chocolate con nueces",
                 precio=3.50, categoria_id=cat_ids["Postres"], icono="🍫"),
        Producto(nombre="Helado", descripcion="2 bolas (vainilla, chocolate o fresa)",
                 precio=2.50, categoria_id=cat_ids["Postres"], icono="🍨"),
        Producto(nombre="Tiramisú", descripcion="Porción individual",
                 precio=4.50, categoria_id=cat_ids["Postres"], icono="🍰"),
    ]

    for prod in productos:
        db.crear_producto(prod)

    # ─── Variantes de ejemplo (tamaños para pizzas) ───
    _seed_variants(db, cat_ids)

    # ─── Ingredientes adicionales ───
    _seed_ingredients(db)

    # ─── Combos y Promociones ───
    _seed_combos(db, cat_ids)

    # ─── Configuración Inicial ───
    _seed_config_defaults(db)

    # ─── Usuario Admin por Defecto ───
    _seed_admin_user(db)

    print(f"[OK] Base de datos inicializada con {len(categorias)} categorias, {len(productos)} productos y configuración.")


def _seed_config_defaults(db: DatabaseManager):
    """Inserta valores por defecto en la tabla configuracion si no existen."""
    defaults = {
        "business_name": config.BUSINESS_NAME,
        "business_slogan": config.BUSINESS_SLOGAN,
        "business_phone": config.BUSINESS_PHONE,
        "business_address": config.BUSINESS_ADDRESS,
        "currency_symbol": config.CURRENCY_SYMBOL,
        "tax_rate": str(config.TAX_RATE),
        # Defaults de impresión térmica
        "printer_name": config.PRINTER_NAME,
        "printer_auto_cut": "1" if config.PRINTER_AUTO_CUT else "0",
        "printer_paper_width": str(config.PRINTER_PAPER_WIDTH),
        "printer_codepage": config.PRINTER_CODEPAGE,
        "printer_print_qr": "1" if config.PRINTER_PRINT_QR else "0",
        "printer_save_pdf": "1" if config.PRINTER_SAVE_PDF else "0",
    }
    for clave, valor in defaults.items():
        if db.get_config(clave) is None:
            db.set_config(clave, valor)


def _seed_variants(db: DatabaseManager, cat_ids: dict):
    """Crea variantes de tamaño para productos de pizza."""
    from database.models import ProductoVariante

    pizza_id = cat_ids.get("Pizzas")
    if not pizza_id:
        return

    # Obtener productos de la categoría Pizzas
    productos_pizza = [p for p in db.get_productos(categoria_id=pizza_id)]

    variantes_data = [
        ("Personal", -2.00, 1),
        ("Mediana", 0.00, 2),
        ("Familiar", 3.00, 3),
        ("Jumbo", 5.00, 4),
    ]

    for prod in productos_pizza:
        for nombre, precio_adicional, orden in variantes_data:
            db.crear_variante(ProductoVariante(
                producto_id=prod.id,
                nombre=nombre,
                precio_adicional=precio_adicional,
                orden=orden,
            ))

    print(f"[OK] Variantes creadas para {len(productos_pizza)} productos de pizza")


def _seed_ingredients(db: DatabaseManager):
    """Crea ingredientes adicionales disponibles."""
    from database.models import ProductoIngrediente

    ingredientes = [
        # Quesos
        ProductoIngrediente(nombre="Queso Mozzarella Extra", precio_adicional=1.50, categoria="Quesos", producto_id=None),
        ProductoIngrediente(nombre="Queso Cheddar", precio_adicional=1.50, categoria="Quesos", producto_id=None),
        ProductoIngrediente(nombre="Queso Parmesano", precio_adicional=1.00, categoria="Quesos", producto_id=None),
        # Carnes
        ProductoIngrediente(nombre="Pepperoni Extra", precio_adicional=1.50, categoria="Carnes", producto_id=None),
        ProductoIngrediente(nombre="Jamón", precio_adicional=1.50, categoria="Carnes", producto_id=None),
        ProductoIngrediente(nombre="Pollo", precio_adicional=2.00, categoria="Carnes", producto_id=None),
        ProductoIngrediente(nombre="Bacon", precio_adicional=1.50, categoria="Carnes", producto_id=None),
        # Vegetales
        ProductoIngrediente(nombre="Champiñones", precio_adicional=1.00, categoria="Vegetales", producto_id=None),
        ProductoIngrediente(nombre="Cebolla", precio_adicional=0.75, categoria="Vegetales", producto_id=None),
        ProductoIngrediente(nombre="Pimiento", precio_adicional=0.75, categoria="Vegetales", producto_id=None),
        ProductoIngrediente(nombre="Aceitunas", precio_adicional=1.00, categoria="Vegetales", producto_id=None),
        # Salsas
        ProductoIngrediente(nombre="Salsa BBQ", precio_adicional=0.50, categoria="Salsas", producto_id=None),
        ProductoIngrediente(nombre="Salsa Ranch", precio_adicional=0.50, categoria="Salsas", producto_id=None),
        ProductoIngrediente(nombre="Salsa de Ajo", precio_adicional=0.50, categoria="Salsas", producto_id=None),
    ]

    for ing in ingredientes:
        db.crear_ingrediente(ing)

    print(f"[OK] {len(ingredientes)} ingredientes adicionales creados")


def _seed_combos(db: DatabaseManager, cat_ids: dict):
    """Crea combos y promociones de ejemplo."""
    from database.models import Combo, ComboItem

    productos = db.get_productos(solo_disponibles=True)
    prod_by_name = {p.nombre: p for p in productos}

    combos_data = [
        {
            "nombre": "Combo Familiar",
            "descripcion": "Una pizza familiar + 2 bebidas + papas. ¡La mejor opción para compartir!",
            "precio_total": 18.00,
            "icono": "👨‍👩‍👧‍👦",
            "items": [
                ("Pizza Suprema", 1),
                ("Coca-Cola", 2),
                ("Papas Fritas", 1),
            ],
        },
        {
            "nombre": "Combo Pizza + Bebida",
            "descripcion": "Tu pizza favorita con una bebida refrescante",
            "precio_total": 10.00,
            "icono": "🍕",
            "items": [
                ("Pizza Margarita", 1),
                ("Coca-Cola", 1),
            ],
        },
        {
            "nombre": "Combo Hamburguesa",
            "descripcion": "Hamburguesa clásica + papas + bebida",
            "precio_total": 9.50,
            "icono": "🍔",
            "items": [
                ("Hamburguesa Clásica", 1),
                ("Papas Fritas", 1),
                ("Sprite", 1),
            ],
        },
        {
            "nombre": "Combo Doble",
            "descripcion": "Hamburguesa doble + aros de cebolla + cerveza",
            "precio_total": 14.00,
            "icono": "🍻",
            "items": [
                ("Hamburguesa Doble", 1),
                ("Aros de Cebolla", 1),
                ("Cerveza", 1),
            ],
        },
        {
            "nombre": "Combo Infantil",
            "descripcion": "Hot dog clásico + nuggets + jugo natural + postre",
            "precio_total": 8.50,
            "icono": "🧒",
            "items": [
                ("Hot Dog Clásico", 1),
                ("Nuggets x6", 1),
                ("Jugo Natural", 1),
                ("Helado", 1),
            ],
        },
        {
            "nombre": "Combo Postre",
            "descripcion": "Brownie + helado. ¡El antojo perfecto!",
            "precio_total": 5.00,
            "icono": "🍫",
            "items": [
                ("Brownie", 1),
                ("Helado", 1),
            ],
        },
    ]

    created = 0
    for cd in combos_data:
        items = []
        suma_individual = 0.0
        for nombre_prod, cantidad in cd["items"]:
            prod = prod_by_name.get(nombre_prod)
            if not prod:
                continue
            items.append(ComboItem(
                producto_id=prod.id,
                producto_nombre=prod.nombre,
                cantidad=cantidad,
                precio_individual=prod.precio,
            ))
            suma_individual += prod.precio * cantidad

        if not items:
            continue

        ahorro = round(max(0, suma_individual - cd["precio_total"]), 2)
        combo = Combo(
            nombre=cd["nombre"],
            descripcion=cd["descripcion"],
            precio_total=cd["precio_total"],
            ahorro=ahorro,
            icono=cd["icono"],
            items=items,
        )
        db.crear_combo(combo)
        created += 1

    print(f"[OK] {created} combos/promociones creados")


def _seed_admin_user(db: DatabaseManager):
    """Crea usuario admin por defecto si no existen usuarios."""
    if not db.hay_usuarios():
        db.crear_usuario(
            username="admin",
            password="admin123",
            nombre_completo="Administrador",
            rol="admin"
        )
        print("[OK] Usuario admin creado (admin / admin123)")
