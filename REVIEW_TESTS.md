# Revisión de Tests — FastBitePOS
## Análisis de hangs en GitHub Actions CI

---

## Resumen Ejecutivo

Se revisaron **12 archivos de test** con **256 métodos de prueba** que se ejecutan en la pipeline de CI (`ci.yml`) usando PySide6 en modo offscreen con xvfb.

Se identificaron **12 hallazgos** (3 críticos, 4 altos, 3 medios, 2 bajos) que explican por qué los tests se quedan colgados en GitHub Actions.

---

## Hallazgos

### CRÍTICOS (causan hangs directos)

#### C-01: Timers de Qt no detenidos en tearDown → proceso nunca termina
- **Archivos**: `tests/test_views.py` (TestMainWindow, TestKitchenDisplayView)
- **Problema**: `MainWindow` crea 3 QTimers (`_timer` clock 1s, `_printer_timer` 30s, `_printer_timer` singleShot 100ms) y `KitchenDisplayView` crea otros 3 (`_refresh_timer`, `_clock_timer`, `_timer_updater`). Los `tearDown` solo detienen algunos, no todos. Los timers siguen disparando señales después de `close()`/`deleteLater()`, impidiendo que el proceso de test finalice limpiamente.
- **Fix**: Helper `_stop_all_timers()` que detiene recursivamente todos los QTimer. Aplicado a todos los tearDown de vistas con timers.

#### C-02: No hay timeout global en el test runner
- **Archivo**: `run_tests.py`
- **Problema**: Si un solo test se cuelga (por un QTimer, un QEventLoop, o un mock mal configurado), **toda la suite se cuelga indefinidamente**. GitHub Actions tiene timeout por job (6h por defecto) pero no por step de tests.
- **Fix**: `signal.SIGALRM` con timeout de 480s (8 min) en `run_tests.py`.

#### C-03: `showMaximized()` en offscreen sin display real
- **Archivos**: `tests/test_views.py` (TestLoginView)
- **Problema**: `LoginView.showEvent()` llama a `showMaximized()`. En CI con `QT_QPA_PLATFORM=offscreen`, `showMaximized()` puede intentar negociar geometry con un display virtual que no responde, causando que el event loop se quede esperando.
- **Fix**: Mock de `showMaximized` a `lambda: None` en `_create_view()`.

### ALTOS

#### A-01: `check_printer_status` / `get_default_printer` en CI sin win32
- **Archivo**: `tests/test_views.py` (TestMainWindow)
- **Problema**: `MainWindow.__init__()` llama `QTimer.singleShot(100, self._update_printer_status)` que eventualmente llama `check_printer_status()` y `get_default_printer()`. En Linux CI, estos usan `win32print` mock que puede comportarse impredeciblemente.
- **Fix**: Mock explícito de `check_printer_status` y `get_default_printer` en `setUp()` de TestMainWindow.

#### A-02: `smoke_test.py` sin timeout SIGALRM
- **Archivo**: `smoke_test.py`
- **Problema**: Usa `proc.communicate(timeout=5)` para la app, pero si `main.py` queda en estado zombie o el pipe se bloquea, el smoke test mismo se cuelga.
- **Fix**: `signal.SIGALRM` como timeout global de 35s.

#### A-03: `xvfb-run -a` escope lento y poco fiable
- **Archivo**: `.github/workflows/ci.yml`
- **Problema**: `xvfb-run -a` busca un display libre con race conditions. En runners de CI con recursos limitados, esto puede fallar silenciosamente o tomar mucho tiempo.
- **Fix**: Arrancar `Xvfb :99` explícitamente antes de los tests y usar `DISPLAY=:99`.

#### A-04: `smoke_test_completo.py` sin timeout
- **Archivo**: `smoke_test_completo.py`
- **Problema**: Usa `os._exit()` para forzar salida (bueno), pero si el test se queda colgado *antes* de llegar al final (por ejemplo en la fase de imports), no hay protección.
- **Fix**: `signal.SIGALRM` con timeout de 180s.

### MEDIOS

#### M-01: LoadingSpinner timer (16ms) no se detiene en tests
- **Archivo**: `tests/test_components.py`
- **Problema**: Los tests de `LoadingSpinner` verifican que el timer funciona pero nunca lo detienen. Aunque el GC eventualmente destruye el widget, el timer puede seguir disparando señales hasta el siguiente ciclo.
- **Fix**: `spinner._timer.stop()` + `spinner.deleteLater()` al final de cada test.

#### M-02: `QTimer.singleShot(500, lambda: None)` inútil en test
- **Archivo**: `tests/test_components.py` (test_static_information)
- **Problema**: El test de `ModernMessageBox.information()` schedula un singleShot que no hace nada. Si en algún momento el test intenta realmente ejecutar `d.exec()`, colgará el event loop sin poder cerrar el diálogo.
- **Fix**: Mock completo de `ModernMessageBox.information` o no ejecutarlo en absoluto. El test actual solo verifica que el método existe (es correcto), pero el dead code es confuso.

#### M-03: `tests/__init__.py` faltante
- **Problema**: La carpeta `tests/` no tiene `__init__.py`, lo cual funciona con `unittest.TestLoader.discover()` pero puede causar problemas con imports relativos o herramientas de cobertura.
- **Fix**: Agregar `tests/__init__.py` con docstring.

### BAJOS

#### B-01: Tests duplicados en TestPOSView y TestPOSViewAdvanced
- **Archivo**: `tests/test_views.py`
- **Problema**: `_insert_tests.py` genera código duplicado que se inyecta en el archivo. Los tests `_shortcut_*` y `_on_order_confirmed_*` aparecen en `TestPOSViewAdvanced2` (insertados) con lógica muy similar a los de `TestPOSViewAdvanced`.
- **Impacto**: Bajo, solo añade tiempo de ejecución.

#### B-02: 256 tests en un solo runner
- **Impacto**: Con 256 tests, si uno falla, el reporte es largo. Considerar separar en suites (unit, integration, gui) para paralelizar.

---

## Archivos Modificados

| Archivo | Cambios | Prioridad |
|---------|---------|-----------|
| `.github/workflows/ci.yml` | Xvfb explícito + timeout por step | Crítica |
| `run_tests.py` | SIGALRM timeout global 480s | Crítica |
| `smoke_test.py` | SIGALRM timeout + QT_QPA_PLATFORM=offscreen | Alta |
| `smoke_test_completo.py` | SIGALRM timeout 180s | Alta |
| `tests/test_views.py` | `_stop_all_timers()` helper, mock showMaximized, mock printer | Crítica |
| `tests/test_components.py` | `_stop_all_timers()` helper, stop spinner timers | Media |
| `tests/__init__.py` | Nuevo archivo (paquete) | Media |

---

## Cómo Aplicar

### Opción A: Copiar archivos modificados
```bash
# Descomprimir el ZIP
unzip FastBitePOS-tests-fix.zip
cd FastBitePOS-tests-fix/mejoras

# Copiar archivos a tu repo local
cp run_tests.py /ruta/a/tu/repo/
cp smoke_test.py /ruta/a/tu/repo/
cp smoke_test_completo.py /ruta/a/tu/repo/
cp tests/test_views.py /ruta/a/tu/repo/tests/
cp tests/test_components.py /ruta/a/tu/repo/tests/
cp tests/__init__.py /ruta/a/tu/repo/tests/
cp ci.yml /ruta/a/tu/repo/.github/workflows/ci.yml
```

### Opción B: Aplicar parches
```bash
cd /ruta/a/tu/repo
for patch in /ruta/al/zip/patches/*.patch; do
    patch -p1 < "$patch"
done
```

---

## Verificación Post-Fix

```bash
# Ejecutar tests localmente
QT_QPA_PLATFORM=offscreen python run_tests.py

# Ejecutar smoke tests
QT_QPA_PLATFORM=offscreen python smoke_test.py
QT_QPA_PLATFORM=offscreen python smoke_test_completo.py --headless
```

Si todo funciona, subir a GitHub y verificar que la pipeline de CI pasa.
