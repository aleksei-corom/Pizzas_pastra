"""Script para empaquetar la aplicación FastBite POS."""

import os
import subprocess
import sys

# Forzar codificación UTF-8 para la consola en Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


def build():
    print("🚀 Iniciando empaquetado de FastBite POS...")

    # Instalar pyinstaller si no está
    print("Verificando dependencias de empaquetado...")
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)

    # Empaquetar
    print("Construyendo ejecutable...")
    try:
        subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--clean", "FastBitePOS.spec"],
            check=True
        )
        print("\n✅ Empaquetado exitoso.")
        print(f"El ejecutable se encuentra en: {os.path.abspath('dist/FastBitePOS.exe')}")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error durante el empaquetado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build()
