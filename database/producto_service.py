"""Servicio de gestión de productos, categorías, variantes e ingredientes."""

from typing import Optional

from database.db_manager import DatabaseManager
from database.models import Categoria, Producto, ProductoVariante, ProductoIngrediente, row_to_model


class ProductoService:
    """Maneja productos, categorías, variantes e ingredientes."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self._db = db or DatabaseManager()
        # Cache manual: evita el memory leak de @lru_cache en métodos de instancia
        self._cache: dict = {}

    def _clear_cache(self):
        """Invalida todas las caches de consultas."""
        self._cache.clear()

    # ─── CATEGORÍAS ───

    def get_categorias(self, solo_activas: bool = True) -> tuple[Categoria, ...]:
        key = ("categorias", solo_activas)
        if key in self._cache:
            return self._cache[key]
        q = "SELECT * FROM categorias"
        if solo_activas:
            q += " WHERE activa = 1"
        q += " ORDER BY orden, nombre"
        rows = self._db.conn.execute(q).fetchall()
        result = tuple(row_to_model(Categoria, r) for r in rows)
        self._cache[key] = result
        return result

    def crear_categoria(self, cat: Categoria) -> int:
        self._clear_cache()
        cur = self._db.conn.execute(
            "INSERT INTO categorias (nombre, icono, orden, activa) VALUES (?, ?, ?, ?)",
            (cat.nombre, cat.icono, cat.orden, int(cat.activa))
        )
        self._db.conn.commit()
        return cur.lastrowid

    def actualizar_categoria(self, cat: Categoria):
        self._clear_cache()
        self._db.conn.execute(
            "UPDATE categorias SET nombre=?, icono=?, orden=?, activa=? WHERE id=?",
            (cat.nombre, cat.icono, cat.orden, int(cat.activa), cat.id)
        )
        self._db.conn.commit()

    def eliminar_categoria(self, cat_id: int):
        """Soft-delete: desactiva la categoría en lugar de borrarla."""
        self._clear_cache()
        row = self._db.conn.execute(
            "SELECT COUNT(*) as cnt FROM productos WHERE categoria_id = ? AND disponible = 1",
            (cat_id,)
        ).fetchone()
        if row["cnt"] > 0:
            raise ValueError(
                f"No se puede eliminar: la categoría tiene {row['cnt']} producto(s) activo(s)."
            )
        self._db.conn.execute(
            "UPDATE categorias SET activa = 0 WHERE id = ?", (cat_id,)
        )
        self._db.conn.commit()

    # ─── PRODUCTOS ───

    def get_productos(self, categoria_id: Optional[int] = None,
                      solo_disponibles: bool = False) -> tuple[Producto, ...]:
        # FIX: Verificar cache ANTES de construir la query (evita trabajo innecesario)
        key = ("productos", categoria_id, solo_disponibles)
        if key in self._cache:
            return self._cache[key]

        q = """
            SELECT p.*, c.nombre as categoria_nombre
            FROM productos p
            JOIN categorias c ON p.categoria_id = c.id
        """
        params = []
        conditions = []
        if categoria_id:
            conditions.append("p.categoria_id = ?")
            params.append(categoria_id)
        if solo_disponibles:
            conditions.append("p.disponible = 1")
        if conditions:
            q += " WHERE " + " AND ".join(conditions)
        q += " ORDER BY c.orden, p.nombre"
        rows = self._db.conn.execute(q, params).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            result.append(Producto(
                id=d["id"], nombre=d["nombre"], descripcion=d["descripcion"],
                precio=d["precio"], categoria_id=d["categoria_id"],
                categoria_nombre=d.get("categoria_nombre", ""),
                disponible=bool(d["disponible"]), icono=d.get("icono", ""),
                tiene_variantes=bool(d.get("tiene_variantes", 0))
            ))
        result_tuple = tuple(result)
        self._cache[key] = result_tuple
        return result_tuple

    def buscar_productos(self, texto: str) -> tuple[Producto, ...]:
        key = ("buscar", texto)
        if key in self._cache:
            return self._cache[key]
        q = """
            SELECT p.*, c.nombre as categoria_nombre
            FROM productos p
            JOIN categorias c ON p.categoria_id = c.id
            WHERE p.disponible = 1 AND (p.nombre LIKE ? OR p.descripcion LIKE ?)
            ORDER BY p.nombre
        """
        pat = f"%{texto}%"
        rows = self._db.conn.execute(q, (pat, pat)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            result.append(Producto(
                id=d["id"], nombre=d["nombre"], descripcion=d["descripcion"],
                precio=d["precio"], categoria_id=d["categoria_id"],
                categoria_nombre=d.get("categoria_nombre", ""),
                disponible=bool(d["disponible"]), icono=d.get("icono", ""),
                tiene_variantes=bool(d.get("tiene_variantes", 0))
            ))
        result_tuple = tuple(result)
        self._cache[key] = result_tuple
        return result_tuple


    def crear_producto(self, prod: Producto) -> int:
        self._clear_cache()
        cur = self._db.conn.execute(
            "INSERT INTO productos (nombre, descripcion, precio, categoria_id, disponible, icono) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (prod.nombre, prod.descripcion, prod.precio, prod.categoria_id,
             int(prod.disponible), prod.icono)
        )
        self._db.conn.commit()
        return cur.lastrowid

    def actualizar_producto(self, prod: Producto):
        self._clear_cache()
        self._db.conn.execute(
            "UPDATE productos SET nombre=?, descripcion=?, precio=?, categoria_id=?, "
            "disponible=?, icono=? WHERE id=?",
            (prod.nombre, prod.descripcion, prod.precio, prod.categoria_id,
             int(prod.disponible), prod.icono, prod.id)
        )
        self._db.conn.commit()

    def toggle_disponibilidad(self, prod_id: int):
        self._clear_cache()
        self._db.conn.execute(
            "UPDATE productos SET disponible = NOT disponible WHERE id=?", (prod_id,)
        )
        self._db.conn.commit()

    def eliminar_producto(self, prod_id: int):
        """Soft-delete: marca como no disponible en lugar de borrar."""
        self._clear_cache()
        self._db.conn.execute(
            "UPDATE productos SET disponible = 0 WHERE id = ?", (prod_id,)
        )
        self._db.conn.commit()

    # ─── VARIANTES ───

    def get_variantes(self, producto_id: int) -> list[ProductoVariante]:
        rows = self._db.conn.execute(
            "SELECT * FROM producto_variantes WHERE producto_id = ? ORDER BY orden",
            (producto_id,)
        ).fetchall()
        return [row_to_model(ProductoVariante, r) for r in rows]

    def crear_variante(self, v: ProductoVariante) -> int:
        self._clear_cache()
        try:
            self._db.conn.execute("BEGIN IMMEDIATE")
            cur = self._db.conn.execute(
                "INSERT INTO producto_variantes (producto_id, nombre, precio_adicional, orden) "
                "VALUES (?, ?, ?, ?)",
                (v.producto_id, v.nombre, v.precio_adicional, v.orden)
            )
            self._db.conn.execute(
                "UPDATE productos SET tiene_variantes=1 WHERE id=?", (v.producto_id,)
            )
            self._db.conn.commit()
        except Exception:
            self._db.conn.rollback()
            raise
        return cur.lastrowid

    def eliminar_variante(self, variante_id: int):
        self._clear_cache()
        try:
            self._db.conn.execute("BEGIN IMMEDIATE")
            v = self._db.conn.execute(
                "SELECT producto_id FROM producto_variantes WHERE id=?", (variante_id,)
            ).fetchone()
            prod_id = v["producto_id"] if v else None
            self._db.conn.execute("DELETE FROM producto_variantes WHERE id=?", (variante_id,))
            if prod_id:
                restantes = self._db.conn.execute(
                    "SELECT COUNT(*) as cnt FROM producto_variantes WHERE producto_id=?", (prod_id,)
                ).fetchone()["cnt"]
                if restantes == 0:
                    self._db.conn.execute(
                        "UPDATE productos SET tiene_variantes=0 WHERE id=?", (prod_id,)
                    )
            self._db.conn.commit()
        except Exception:
            self._db.conn.rollback()
            raise

    # ─── INGREDIENTES ───

    def get_ingredientes(self, producto_id: Optional[int] = None,
                         solo_activos: bool = False) -> list[ProductoIngrediente]:
        if producto_id:
            q = "SELECT * FROM producto_ingredientes WHERE (producto_id = ? OR producto_id IS NULL)"
            params = [producto_id]
            if solo_activos:
                q += " AND activo = 1"
            q += " ORDER BY categoria, nombre"
            rows = self._db.conn.execute(q, params).fetchall()
        else:
            q = "SELECT * FROM producto_ingredientes"
            if solo_activos:
                q += " WHERE activo = 1"
            q += " ORDER BY categoria, nombre"
            rows = self._db.conn.execute(q).fetchall()
        return [row_to_model(ProductoIngrediente, r) for r in rows]

    def crear_ingrediente(self, ing: ProductoIngrediente) -> int:
        self._clear_cache()
        cur = self._db.conn.execute(
            "INSERT INTO producto_ingredientes (producto_id, nombre, precio_adicional, categoria, activo) "
            "VALUES (?, ?, ?, ?, ?)",
            (ing.producto_id, ing.nombre, ing.precio_adicional, ing.categoria, int(ing.activo))
        )
        self._db.conn.commit()
        return cur.lastrowid

    def eliminar_ingrediente(self, ing_id: int):
        self._clear_cache()
        self._db.conn.execute("DELETE FROM producto_ingredientes WHERE id=?", (ing_id,))
        self._db.conn.commit()

    # ─── ESTADÍSTICAS DE PRODUCTO ───

    def get_productos_populares(self, limit: int = 5) -> list[dict]:
        rows = self._db.conn.execute(
            "SELECT producto_nombre, SUM(cantidad) as total_cantidad, "
            "SUM(cantidad * precio_unitario) as total_ventas "
            "FROM orden_items oi "
            "JOIN ordenes o ON oi.orden_id = o.id "
            "WHERE o.estado != 'cancelled' "
            "GROUP BY producto_nombre "
            "ORDER BY total_cantidad DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
