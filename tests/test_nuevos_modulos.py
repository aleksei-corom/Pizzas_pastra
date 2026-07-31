"""Pruebas unitarias para los 3 nuevos módulos: CRM (Clientes), Costos (Recetas) y Asistente IA."""

import os
import tempfile
import unittest
import config as app_config
from database.db_manager import DatabaseManager
from database.models import Cliente, Premio, Receta, RecetaIngrediente
from database.cliente_service import ClienteService
from database.receta_service import RecetaService
from database.asistente_service import AsistenteService


class TestNuevosModulos(unittest.TestCase):

    def setUp(self):
        self.tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.tmp_db.close()
        self.db_path = self.tmp_db.name
        
        # Iniciar db en archivo temporal
        DatabaseManager._instance = None
        app_config.DB_PATH = self.db_path
        self.db = DatabaseManager()
        self.db.init_db()

        self.cliente_service = ClienteService(self.db)
        self.receta_service = RecetaService(self.db)
        self.asistente_service = AsistenteService(self.db)

    def tearDown(self):
        DatabaseManager._instance = None
        if os.path.exists(self.db_path):
            try:
                os.unlink(self.db_path)
            except OSError:
                pass

    def test_cliente_crud_and_puntos(self):
        # Crear cliente
        c = Cliente(nombre="Juan Perez", telefono="555-1234", email="juan@example.com")
        cid = self.cliente_service.crear_cliente(c)
        self.assertIsNotNone(cid)

        # Buscar cliente por teléfono
        buscado = self.cliente_service.buscar_por_telefono("555-1234")
        self.assertIsNotNone(buscado)
        self.assertEqual(buscado.nombre, "Juan Perez")

        # Acumular puntos
        puntos_ganados = self.cliente_service.acumular_puntos(cid, 50.0)
        self.assertGreater(puntos_ganados, 0)
        
        c_actualizado = self.cliente_service.get_cliente(cid)
        self.assertEqual(c_actualizado.puntos, puntos_ganados)

    def test_receta_crud(self):
        # Crear receta con ingredientes
        ing = RecetaIngrediente(nombre="Harina", cantidad=1.0, unidad="kg", costo_unitario=2.5, subtotal=2.5)
        r = Receta(nombre="Masa Tradicional", porciones=4, ingredientes=[ing])
        rid = self.receta_service.crear_receta(r)
        self.assertIsNotNone(rid)

        receta_cargada = self.receta_service.get_receta(rid)
        self.assertIsNotNone(receta_cargada)
        self.assertEqual(len(receta_cargada.ingredientes), 1)

    def test_asistente_insights(self):
        insights = self.asistente_service.generar_insights()
        self.assertIsInstance(insights, list)


if __name__ == "__main__":
    unittest.main()
