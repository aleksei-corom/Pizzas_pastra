"""Test runner para FastBite POS."""
import unittest
import sys
import os
import signal

if __name__ == '__main__':
    # Asegurar que el directorio raíz esté en el path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    # Timeout global para evitar hangs en GitHub Actions
    TIMEOUT_SECONDS = 480  # 8 minutos

    def _timeout_handler(signum, frame):
        print(f"\n\n[TIMEOUT] Los tests excedieron {TIMEOUT_SECONDS}s — posible hang detectado.")
        sys.exit(124)

    # Configurar timeout (solo funciona en Unix/CI)
    if hasattr(signal, 'SIGALRM'):
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(TIMEOUT_SECONDS)

    print("Iniciando Suite de Pruebas de FastBite POS...")
    print(f"Timeout global: {TIMEOUT_SECONDS}s\n")
    loader = unittest.TestLoader()
    start_dir = os.path.join(project_root, 'tests')
    suite = loader.discover(start_dir, pattern='test_*.py')

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Cancelar timeout al finalizar
    if hasattr(signal, 'SIGALRM'):
        signal.alarm(0)

    if result.wasSuccessful():
        print(f"\nTodos los tests pasaron exitosamente ({result.testsRun}).")
        sys.exit(0)
    else:
        print(f"\nFallaron {len(result.failures) + len(result.errors)} de {result.testsRun} tests.")
        sys.exit(1)
