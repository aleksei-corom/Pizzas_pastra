import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('tests/test_views.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_class = """# ================================================
#  POSView - Advanced tests 2 (shortcuts, combos, printing)
# ================================================

class TestPOSViewAdvanced2(unittest.TestCase):
    '''Pruebas avanzadas para POSView - shortcuts con items, escape con busqueda, categoria F1-F8, quick add, multi-combos, pago combinado, impresion.'''

    @classmethod
    def setUpClass(cls):
        cls.app = get_app()

    def setUp(self):
        self.db, self.auth_svc, self.prod_svc, self.orden_svc = _init_db()
        self.cat_id = _seed_minimal(self.prod_svc)
        prod = self.prod_svc.get_productos()[0]
        from database.models import Combo, ComboItem
        self.combo_1 = Combo(nombre="Combo Bebida", precio_total=2.5)
        self.combo_1.items.append(ComboItem(
            producto_id=prod.id, producto_nombre="Cola", cantidad=1, precio_individual=2.5
        ))
        self.orden_svc.crear_combo(self.combo_1)
        self.combo_2 = Combo(nombre="Combo Duo", precio_total=4.0)
        self.combo_2.items.append(ComboItem(
            producto_id=prod.id, producto_nombre="Cola", cantidad=2, precio_individual=2.5
        ))
        self.orden_svc.crear_combo(self.combo_2)

    def tearDown(self):
        if hasattr(self, 'view') and self.view:
            if hasattr(self.view, '_resize_timer'):
                self.view._resize_timer.stop()
            self.view.close()
            self.view.deleteLater()
        self.db.close()
        DatabaseManager._instance = None

    def _create_view(self):
        from views.pos_view import POSView
        view = POSView()
        view.prod_svc = self.prod_svc
        view.orden_svc = self.orden_svc
        self.view = view
        return view

    def test_shortcut_confirm_con_items_llama_confirm(self):
        view = self._create_view()
        prod = self.prod_svc.get_productos()[0]
        view._add_to_order(prod)
        self.assertTrue(view._order_panel._btn_confirm.isEnabled())
        with unittest.mock.patch.object(view._order_panel, '_confirm_order') as mock_confirm:
            view._shortcut_confirm()
            mock_confirm.assert_called_once()

    def test_shortcut_new_order_con_items_limpia(self):
        view = self._create_view()
        prod = self.prod_svc.get_productos()[0]
        view._add_to_order(prod)
        self.assertGreater(len(view._order_panel.items), 0)
        with unittest.mock.patch.object(view._order_panel, 'show_toast') as mock_toast:
            view._shortcut_new_order()
            mock_toast.assert_called_once()
            self.assertIn("limpia", mock_toast.call_args[0][0].lower())
        self.assertEqual(len(view._order_panel.items), 0)

    def test_shortcut_escape_limpia_busqueda(self):
        view = self._create_view()
        view._search.setText("Cola")
        view._search.setFocus()
        self.assertTrue(view._search.hasFocus())
        self.assertTrue(view._search.text())
        view._shortcut_escape()
        self.assertEqual(view._search.text(), "")

    def test_shortcut_category_selecciona_por_indice(self):
        view = self._create_view()
        self.assertGreater(len(view._cat_buttons), 1)
        cat_ids = [cid for cid in view._cat_buttons.keys() if cid is not None and cid != view._COMBO_KEY]
        if not cat_ids:
            self.skipTest("No hay categorias para probar")
        target_cat_id = cat_ids[0]
        all_keys = list(view._cat_buttons.keys())
        idx = all_keys.index(target_cat_id)
        view._shortcut_category(idx)
        self.assertEqual(view._current_category, target_cat_id)

    def test_shortcut_category_indice_fuera_de_rango_no_crashea(self):
        view = self._create_view()
        try:
            view._shortcut_category(999)
            view._shortcut_category(-1)
        except Exception as e:
            self.fail("_shortcut_category con indice invalido lanzo excepcion: " + str(e))

    def test_shortcut_quick_add_agrega_primer_producto(self):
        view = self._create_view()
        items_before = len(view._order_panel.items)
        view._shortcut_quick_add()
        self.assertGreater(len(view._order_panel.items), items_before)

    def test_shortcut_quick_add_sin_cards_no_crashea(self):
        view = self._create_view()
        view._product_cards = []
        try:
            view._shortcut_quick_add()
        except Exception as e:
            self.fail("_shortcut_quick_add sin cards lanzo excepcion: " + str(e))

    def test_display_combos_con_multiples_combos(self):
        view = self._create_view()
        combos = self.orden_svc.get_combos(solo_activos=True)
        self.assertGreaterEqual(len(combos), 2)
        view._display_combos(combos)
        self.assertEqual(len(view._product_cards), len(combos))

    def test_display_combos_vacio_muestra_mensaje(self):
        view = self._create_view()
        view._display_combos([])
        self.assertEqual(len(view._product_cards), 0)

    def test_on_order_confirmed_pago_combinado(self):
        view = self._create_view()
        with unittest.mock.patch('views.pos_view.PaymentDialog') as MockPayment:
            mock_dlg = unittest.mock.MagicMock()
            mock_dlg.exec.return_value = QDialog.DialogCode.Accepted
            mock_dlg.imprimir_recibo = False
            mock_dlg.metodos_pago = [("efectivo", 30.0), ("tarjeta", 20.0)]
            mock_dlg.val_vuelto = unittest.mock.MagicMock()
            mock_dlg.val_vuelto.text.return_value = app_config.CURRENCY_SYMBOL + "0.00"
            mock_dlg.printer_name = None
            mock_dlg.set_orden_data = unittest.mock.MagicMock()
            MockPayment.return_value = mock_dlg
            with unittest.mock.patch('views.pos_view.ModernMessageBox.success') as mock_success:
                items = [OrdenItem(
                    producto_id=self.prod_svc.get_productos()[0].id,
                    producto_nombre="Cola", cantidad=1, precio_unitario=2.5
                )]
                view._on_order_confirmed({
                    'total': 50.0, 'tipo': 'local', 'items': items,
                })
                mock_success.assert_called_once()
                args, _ = mock_success.call_args
                msg = args[2]
                self.assertIn("combinado", msg.lower())
                self.assertIn("efectivo", msg.lower())
                self.assertIn("tarjeta", msg.lower())

    def test_on_order_confirmed_con_impresion_exitosa(self):
        view = self._create_view()
        with unittest.mock.patch('views.pos_view.PaymentDialog') as MockPayment:
            mock_dlg = unittest.mock.MagicMock()
            mock_dlg.exec.return_value = QDialog.DialogCode.Accepted
            mock_dlg.imprimir_recibo = True
            mock_dlg.metodos_pago = [("efectivo", 2.5)]
            mock_dlg.val_vuelto = unittest.mock.MagicMock()
            mock_dlg.val_vuelto.text.return_value = app_config.CURRENCY_SYMBOL + "0.00"
            mock_dlg.printer_name = "EPSON TM-T20"
            mock_dlg.set_orden_data = unittest.mock.MagicMock()
            MockPayment.return_value = mock_dlg
            with unittest.mock.patch('views.pos_view.print_receipt', return_value=(True, "OK")):
                with unittest.mock.patch('views.pos_view.ModernMessageBox.success') as mock_success:
                    items = [OrdenItem(
                        producto_id=self.prod_svc.get_productos()[0].id,
                        producto_nombre="Cola", cantidad=1, precio_unitario=2.5
                    )]
                    view._on_order_confirmed({
                        'total': 2.5, 'tipo': 'local', 'items': items,
                    })
                    mock_success.assert_called_once()
                    args, _ = mock_success.call_args
                    msg = args[2]
                    self.assertIn("🖨", msg)

    def test_on_order_confirmed_con_impresion_fallida(self):
        view = self._create_view()
        with unittest.mock.patch('views.pos_view.PaymentDialog') as MockPayment:
            mock_dlg = unittest.mock.MagicMock()
            mock_dlg.exec.return_value = QDialog.DialogCode.Accepted
            mock_dlg.imprimir_recibo = True
            mock_dlg.metodos_pago = [("efectivo", 2.5)]
            mock_dlg.val_vuelto = unittest.mock.MagicMock()
            mock_dlg.val_vuelto.text.return_value = app_config.CURRENCY_SYMBOL + "0.00"
            mock_dlg.printer_name = "EPSON TM-T20"
            mock_dlg.set_orden_data = unittest.mock.MagicMock()
            MockPayment.return_value = mock_dlg
            with unittest.mock.patch('views.pos_view.print_receipt', return_value=(False, "Error de impresora")):
                with unittest.mock.patch('views.pos_view.ModernMessageBox.success') as mock_success:
                    items = [OrdenItem(
                        producto_id=self.prod_svc.get_productos()[0].id,
                        producto_nombre="Cola", cantidad=1, precio_unitario=2.5
                    )]
                    view._on_order_confirmed({
                        'total': 2.5, 'tipo': 'local', 'items': items,
                    })
                    mock_success.assert_called_once()
                    args, _ = mock_success.call_args
                    msg = args[2]
                    self.assertIn("Fallo", msg)

    def test_on_order_confirmed_excepcion_en_crear_orden_muestra_error(self):
        view = self._create_view()
        with unittest.mock.patch('views.pos_view.PaymentDialog') as MockPayment:
            mock_dlg = unittest.mock.MagicMock()
            mock_dlg.exec.return_value = QDialog.DialogCode.Accepted
            mock_dlg.imprimir_recibo = False
            mock_dlg.metodos_pago = [("efectivo", 10.0)]
            mock_dlg.val_vuelto = unittest.mock.MagicMock()
            mock_dlg.val_vuelto.text.return_value = app_config.CURRENCY_SYMBOL + "0.00"
            mock_dlg.printer_name = None
            mock_dlg.set_orden_data = unittest.mock.MagicMock()
            MockPayment.return_value = mock_dlg
            view.orden_svc.crear_orden = unittest.mock.MagicMock(
                side_effect=Exception("Error de base de datos")
            )
            with unittest.mock.patch('views.pos_view.ModernMessageBox.error') as mock_error:
                items = [OrdenItem(
                    producto_id=self.prod_svc.get_productos()[0].id,
                    producto_nombre="Cola", cantidad=1, precio_unitario=2.5
                )]
                view._on_order_confirmed({
                    'total': 10.0, 'tipo': 'local', 'items': items,
                })
                mock_error.assert_called_once()
                args, _ = mock_error.call_args
                msg = args[2]
                self.assertIn("Error de base de datos", msg)

"""

insertion_marker = 'class TestMenuView(unittest.TestCase):'
idx = content.find(insertion_marker)
if idx < 0:
    print('ERROR: marker not found')
    sys.exit(1)

content = content[:idx] + new_class + content[idx:]

with open('tests/test_views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('SUCCESS: Inserted', len(new_class), 'chars')
print('File now has', len(content), 'chars')
