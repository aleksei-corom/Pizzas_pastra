"""Smoke test: ejecuta la app por 5s y verifica que no crashea al iniciar.

Uso:
    python smoke_test.py

Exit codes:
    0  — App inició correctamente (no crasheó en 5s)
    1  — App crasheó al iniciar (Traceback en stderr)
    2  — Error interno del smoke test
"""

import subprocess
import sys
import os
import time


def main() -> int:
    project_root = os.path.dirname(os.path.abspath(__file__))

    print("=" * 50)
    print("SMOKE TEST — FastBite POS")
    print(f"Project root: {project_root}")
    print("=" * 50)

    # Lanzar la app en background
    proc = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=project_root,
        text=True,
    )

    start = time.monotonic()
    timed_out = False

    try:
        stdout, stderr = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        timed_out = True
        proc.kill()
        stdout, stderr = proc.communicate(timeout=5)

    elapsed = time.monotonic() - start

    # Mostrar logs de la app
    if stdout:
        for line in stdout.splitlines():
            if any(kw in line.lower() for kw in ("info", "error", "warning", "iniciando")):
                print(f"[APP] {line}")

    if stderr:
        CRASH_KEYWORDS = (
            "traceback", "error:", "exception",
            "attributeerror", "typeerror", "valueerror",
            "keyerror", "importerror", "modulenotfounderror",
            "runtimeerror", "indexerror", "zerodivisionerror",
        )
        has_traceback = any(kw in stderr.lower() for kw in CRASH_KEYWORDS)
        if has_traceback:
            print("\n[STDERR] — ERROR DETECTADO:")
            print(stderr)
            print("\n[FAIL] La app crasheo durante el inicio.")
            print(f"Tiempo hasta el crash: {elapsed:.1f}s")
            return 1
        else:
            # Warnings sin traceback no son fatales
            for line in stderr.splitlines():
                if line.strip():
                    print(f"[STDERR] {line}")

    if timed_out:
        print(f"\n[PASS] App ejecutada por 5.0s sin crashear.")
        return 0
    else:
        print(f"\n[FAIL] App termino inesperadamente tras {elapsed:.1f}s (exit code {proc.returncode}).")
        if stderr:
            print("[STDERR]:")
            print(stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
