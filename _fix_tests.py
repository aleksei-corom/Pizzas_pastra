import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('tests/test_views.py', 'r', encoding='utf-8') as f:
    content = f.read()

fixes = [
    # Fix 1: PaymentDialog mock target - change 'views.pos_view.PaymentDialog' to 'views.components.payment_dialog.PaymentDialog'
    ("with unittest.mock.patch('views.pos_view.PaymentDialog') as MockPayment:",
     "with unittest.mock.patch('views.components.payment_dialog.PaymentDialog') as MockPayment:"),

    # Fix 2: print_receipt mock target - change 'views.pos_view.print_receipt' to 'utils.printer.print_receipt'
    ("with unittest.mock.patch('views.pos_view.print_receipt', return_value=(True, \"OK\")):",
     "with unittest.mock.patch('utils.printer.print_receipt', return_value=(True, \"OK\")):"),
    ("with unittest.mock.patch('views.pos_view.print_receipt', return_value=(False, \"Error de impresora\")):",
     "with unittest.mock.patch('utils.printer.print_receipt', return_value=(False, \"Error de impresora\")):"),

    # Fix 3: "Fallo" -> "Fall\u00f3" (accented)
    ('self.assertIn("Fallo", msg)',
     'self.assertIn("Fall\u00f3", msg)'),

    # Fix 4: Add view.show() before setFocus() in escape test
    ('        view._search.setText("Cola")\n        view._search.setFocus()',
     '        view.show()\n        view._search.setText("Cola")\n        view._search.setFocus()'),
]

count = 0
for old, new in fixes:
    c = content.count(old)
    if c > 0:
        content = content.replace(old, new)
        count += c
        print(f"Replaced '{old[:40]}...' x{c}")
    else:
        print(f"NOT FOUND: '{old[:40]}...'")

with open('tests/test_views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nTotal replacements: {count}")
print(f"File size: {len(content)}")
