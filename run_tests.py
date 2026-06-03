"""Test runner para Pizzas Pastra."""
import unittest
import sys
import os

if __name__ == '__main__':
    # Asegurar que el directorio raíz esté en el path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    # Descubrir y ejecutar todos los tests en la carpeta tests/
    print("Iniciando Suite de Pruebas de Pizzas Pastra...")
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\nTodos los tests pasaron exitosamente.")
        sys.exit(0)
    else:
        print(f"\nFallaron {len(result.failures) + len(result.errors)} tests.")
        sys.exit(1)
