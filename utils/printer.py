"""Módulo de impresión ESC/POS para impresoras térmicas de recibos.

Soporta:
- Impresión directa vía win32print (RAW) a cualquier impresora Windows
- Comandos ESC/POS: corte, negrita, alineación, tamaño de fuente
- Code pages CP437/CP850 para caracteres especiales (ñ, tildes)
- Formato de recibo optimizado para papel térmico 58mm y 80mm
- Vista previa HTML (compatibilidad con QTextBrowser)
- Detección de impresoras disponibles
"""

import os
import logging
from typing import Optional
from io import BytesIO
import base64
from datetime import datetime

import qrcode

import config as app_config

logger = logging.getLogger(__name__)

# ─── ESC/POS Command Constants ───
ESC = b"\x1b"
GS = b"\x1d"
LF = b"\x0a"

# Init printer
CMD_INIT = ESC + b"@"  # 1B 40

# Alignment: 0=left, 1=center, 2=right
CMD_ALIGN_LEFT = ESC + b"\x61\x00"
CMD_ALIGN_CENTER = ESC + b"\x61\x01"
CMD_ALIGN_RIGHT = ESC + b"\x61\x02"

# Bold: n=1 on, n=0 off
CMD_BOLD_ON = ESC + b"\x45\x01"
CMD_BOLD_OFF = ESC + b"\x45\x00"

# Font size: GS ! n (n = height<<4 | width), 0=normal, 0x11=2x, 0x22=3x, etc.
CMD_FONT_NORMAL = GS + b"\x21\x00"
CMD_FONT_DOUBLE_H = GS + b"\x21\x01"       # 2x width
CMD_FONT_DOUBLE_V = GS + b"\x21\x10"       # 2x height
CMD_FONT_DOUBLE_HV = GS + b"\x21\x11"      # 2x both

# Character spacing
CMD_CHAR_SPACE_DEFAULT = ESC + b"\x20\x00"

# Line spacing: ESC 2 (default 30 dots) / ESC 3 n (n/360 inch)
CMD_LINE_SPACING_DEFAULT = ESC + b"\x32"
CMD_LINE_SPACING_NARROW = ESC + b"\x33\x18"  # 24 dots (~3mm)

# Code page: ESC t n
# n=0: CP437 (USA/Europe Standard)
# n=2: CP850 (Multilingual Latin I)
# n=17: CP862 (Latin/Thai)
# n=255: CP1252
CMD_CODEPAGE_437 = ESC + b"\x74\x00"
CMD_CODEPAGE_850 = ESC + b"\x74\x02"

# Cut paper: GS V m
# m=0: full cut, m=1: partial cut, m=66: full cut with feed
CMD_CUT_FULL = GS + b"\x56\x00"
CMD_CUT_PARTIAL = GS + b"\x56\x01"

# Feed paper: ESC d n (feed n lines)
CMD_FEED_3 = ESC + b"\x64\x03"
CMD_FEED_5 = ESC + b"\x64\x05"

# Underline: ESC - n (n=0 off, n=1 on, n=2 double)
CMD_UNDERLINE_OFF = ESC + b"\x2d\x00"
CMD_UNDERLINE_ON = ESC + b"\x2d\x01"


def get_available_printers() -> list[str]:
    """Retorna lista de nombres de impresoras disponibles en Windows."""
    try:
        import win32print
        printers = win32print.EnumPrinters(2)  # PRINTER_ENUM_LOCAL | PRINTER_ENUM_CONNECTIONS
        return sorted(set(p[2] for p in printers))
    except ImportError:
        logger.warning("pywin32 no instalado. No se pueden listar impresoras.")
        return []
    except Exception as e:
        logger.error(f"Error al listar impresoras: {e}")
        return []


def get_default_printer() -> Optional[str]:
    """Retorna la impresora predeterminada de Windows."""
    try:
        import win32print
        return win32print.GetDefaultPrinter()
    except ImportError:
        return None
    except Exception:
        return None


def check_printer_status(printer_name: str) -> bool:
    """Verifica si una impresora está conectada y disponible.

    Abre el handle de la impresora vía win32print y lo cierra
    inmediatamente. Si OpenPrinter tiene éxito, la impresora
    está al menos registrada en el sistema (conectada/online).

    Args:
        printer_name: Nombre exacto de la impresora en Windows.

    Returns:
        True si la impresora está accesible, False en caso contrario.
    """
    if not printer_name:
        return False
    try:
        import win32print
        handle = win32print.OpenPrinter(printer_name)
        win32print.ClosePrinter(handle)
        return True
    except Exception:
        return False


def format_receipt_text(orden, items, paper_width: int = 48) -> str:
    """Genera texto plano formateado para impresora térmica.

    Args:
        orden: Objeto Orden
        items: Lista de OrdenItem
        paper_width: Ancho en caracteres (32 para 58mm, 48 para 80mm)

    Returns:
        Texto plano con formato para ESC/POS
    """
    sep = "=" * paper_width
    dash = "-" * paper_width

    lines = []

    # Header
    lines.append("")
    lines.append(app_config.BUSINESS_NAME.center(paper_width))
    if app_config.BUSINESS_SLOGAN:
        lines.append(app_config.BUSINESS_SLOGAN.center(paper_width))
    lines.append(app_config.BUSINESS_ADDRESS.center(paper_width))
    if app_config.BUSINESS_PHONE:
        lines.append(f"Tel: {app_config.BUSINESS_PHONE}".center(paper_width))
    lines.append(sep)

    # Order info
    lines.append(f"ORDEN #: {orden.numero}")
    fecha = orden.fecha_creacion[:16] if orden.fecha_creacion else ""
    lines.append(f"FECHA:   {fecha}")
    tipo_labels = {"local": "Comer Aqui", "takeout": "Para Llevar", "delivery": "Delivery"}
    lines.append(f"TIPO:    {tipo_labels.get(orden.tipo, orden.tipo)}")
    if orden.cliente_nombre:
        lines.append(f"CLIENTE: {orden.cliente_nombre}")
    lines.append(dash)

    # Items header
    lines.append(f"{'CANT':>4} {'DESCRIPCION':<{paper_width-18}} {'PRECIO':>7} {'TOTAL':>7}")
    lines.append(dash)

    # Items
    for item in items:
        nombre = item.producto_nombre[:paper_width - 20]
        qty_str = f"x{item.cantidad}"
        price_str = f"{app_config.CURRENCY_SYMBOL}{item.precio_unitario:.2f}"
        total_str = f"{app_config.CURRENCY_SYMBOL}{item.subtotal:.2f}"
        lines.append(f"{qty_str:>4} {nombre:<{paper_width-18}} {price_str:>7} {total_str:>7}")

    lines.append(dash)

    # Totals
    subtotal_str = f"{app_config.CURRENCY_SYMBOL}{orden.subtotal:.2f}"
    lines.append(f"{'SUBTOTAL:':>{paper_width-8}} {subtotal_str:>8}")

    tax_str = f"{app_config.CURRENCY_SYMBOL}{orden.impuesto:.2f}"
    tax_label = f"IVA ({int(app_config.TAX_RATE*100)}%):"
    lines.append(f"{tax_label:>{paper_width-8}} {tax_str:>8}")

    if hasattr(orden, 'costo_delivery') and orden.costo_delivery > 0:
        delivery_str = f"{app_config.CURRENCY_SYMBOL}{orden.costo_delivery:.2f}"
        lines.append(f"{'DELIVERY:':>{paper_width-8}} {delivery_str:>8}")

    lines.append(sep)
    total_str = f"{app_config.CURRENCY_SYMBOL}{orden.total:.2f}"
    lines.append(f"{'TOTAL':>{paper_width-8}} {total_str:>8}")
    lines.append(sep)

    if orden.notas:
        lines.append(f"NOTAS: {orden.notas}")
        lines.append(dash)

    # Delivery info
    if orden.tipo == "delivery":
        if hasattr(orden, 'direccion') and orden.direccion:
            lines.append(f"DIRECCION: {orden.direccion}")
        if hasattr(orden, 'telefono_contacto') and orden.telefono_contacto:
            lines.append(f"TELEFONO: {orden.telefono_contacto}")
        lines.append(dash)

    # Footer
    lines.append("")
    lines.append("Gracias por su compra!".center(paper_width))
    lines.append("")
    lines.append("FastBite POS".center(paper_width))
    lines.append("")

    return "\n".join(lines)


def format_receipt_html(orden, items, include_qr=True) -> str:
    """Genera el HTML para el recibo (vista previa en pantalla).

    Args:
        orden: Objeto Orden.
        items: Lista de OrdenItem.
        include_qr: Si True, incluye QR generado con qrcode como base64.
    """
    items_html = ""
    for item in items:
        items_html += f"""
        <tr>
            <td style="padding: 4px 0; font-size: 11px;">{item.producto_nombre} <br><small>x{item.cantidad} @ {app_config.CURRENCY_SYMBOL}{item.precio_unitario:.2f}</small></td>
            <td style="padding: 4px 0; font-size: 11px; text-align: right;">{app_config.CURRENCY_SYMBOL}{item.subtotal:.2f}</td>
        </tr>
        """

    # Generar QR code para vista previa (antes del template)
    qr_section_html = ""
    if include_qr:
        try:
            qr_data = (
                f"Orden: {orden.numero}\n"
                f"Total: {app_config.CURRENCY_SYMBOL}{orden.total:.2f}\n"
                f"{app_config.BUSINESS_NAME}\n"
                f"{app_config.BUSINESS_PHONE}"
            )
            qr_img = qrcode.make(qr_data)
            buf = BytesIO()
            qr_img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            qr_section_html = f'''
        <div class="divider"></div>
        <div class="center">
            <img src="data:image/png;base64,{b64}" style="width: 100px; height: 100px;" alt="QR">
            <br><small>#{orden.numero}</small>
        </div>
        '''
        except Exception:
            pass

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Courier New', Courier, monospace; font-size: 12px; color: #000; margin: 0; padding: 0; }}
            h2, h3, h4 {{ margin: 4px 0; text-align: center; }}
            .divider {{ border-top: 1px dashed #000; margin: 8px 0; }}
            table {{ width: 100%; border-collapse: collapse; }}
            .right {{ text-align: right; }}
            .bold {{ font-weight: bold; }}
            .center {{ text-align: center; }}
        </style>
    </head>
    <body>
        <h2>{app_config.BUSINESS_NAME}</h2>
        <div class="center"><small>{app_config.BUSINESS_SLOGAN}</small></div>
        <div class="center"><small>{app_config.BUSINESS_ADDRESS}</small></div>
        <div class="center"><small>Tel: {app_config.BUSINESS_PHONE}</small></div>

        <div class="divider"></div>
        <div><b>Orden #:</b> {orden.numero}</div>
        <div><b>Fecha:</b> {orden.fecha_creacion[:16] if orden.fecha_creacion else ''}</div>
        <div><b>Tipo:</b> {orden.tipo}</div>

        <div class="divider"></div>
        <table>
            <tr>
                <th style="text-align: left; font-size: 11px; border-bottom: 1px solid #000; padding-bottom: 4px;">Descripcion</th>
                <th style="text-align: right; font-size: 11px; border-bottom: 1px solid #000; padding-bottom: 4px;">Monto</th>
            </tr>
            {items_html}
        </table>

        <div class="divider"></div>
        <table>
            <tr>
                <td>Subtotal:</td>
                <td class="right">{app_config.CURRENCY_SYMBOL}{orden.subtotal:.2f}</td>
            </tr>
            <tr>
                <td>IVA ({int(app_config.TAX_RATE*100)}%):</td>
                <td class="right">{app_config.CURRENCY_SYMBOL}{orden.impuesto:.2f}</td>
            </tr>
            <tr>
                <td class="bold" style="font-size: 14px;">TOTAL:</td>
                <td class="right bold" style="font-size: 14px;">{app_config.CURRENCY_SYMBOL}{orden.total:.2f}</td>
            </tr>
        </table>

        <div class="divider"></div>
        <div class="center">
            <p>Gracias por su compra!</p>
        </div>
        {qr_section_html}
    </body>
    </html>
    """
    return html


class ESCPOSPrinter:
    """Controlador de impresora térmica vía ESC/POS usando win32print.

    Envía comandos RAW directamente a la cola de impresión de Windows,
    sin necesidad de reemplazar drivers USB con libusb.
    """

    def __init__(self, printer_name: Optional[str] = None,
                 auto_cut: bool = True,
                 paper_width: int = 48,
                 codepage: str = "cp850"):
        """Inicializa el controlador.

        Args:
            printer_name: Nombre de la impresora en Windows. None = predeterminada.
            auto_cut: Si True, envía comando de corte al finalizar.
            paper_width: Ancho en caracteres (32 para 58mm, 48 para 80mm).
            codepage: Codificación para caracteres especiales ('cp437' o 'cp850').
        """
        self.printer_name = printer_name
        self.auto_cut = auto_cut
        self.paper_width = paper_width
        self._codepage = codepage
        self._hprinter = None

    @property
    def codepage(self) -> str:
        return self._codepage

    @codepage.setter
    def codepage(self, value: str):
        if value.lower() in ("cp437", "cp850"):
            self._codepage = value.lower()

    def _encode(self, text: str) -> bytes:
        """Codifica texto al code page configurado."""
        try:
            return text.encode(self._codepage, errors="replace")
        except LookupError:
            return text.encode("cp437", errors="replace")

    def open(self) -> bool:
        """Abre la conexión con la impresora."""
        try:
            import win32print
            name = self.printer_name or get_default_printer()
            if not name:
                logger.error("No hay impresora configurada ni predeterminada.")
                return False
            self._hprinter = win32print.OpenPrinter(name)
            return True
        except ImportError:
            logger.error("pywin32 no instalado. pip install pywin32")
            return False
        except Exception as e:
            logger.error(f"Error al abrir impresora '{self.printer_name}': {e}")
            return False

    def close(self):
        """Cierra la conexión con la impresora."""
        if self._hprinter:
            try:
                import win32print
                win32print.ClosePrinter(self._hprinter)
            except Exception:
                pass
            self._hprinter = None

    def write(self, data: bytes) -> bool:
        """Escribe datos RAW en la impresora."""
        if not self._hprinter:
            logger.error("Impresora no abierta. Llama a open() primero.")
            return False
        try:
            import win32print
            win32print.WritePrinter(self._hprinter, data)
            return True
        except Exception as e:
            logger.error(f"Error al escribir en impresora: {e}")
            return False

    def start_doc(self, doc_name: str = "FastBite POS Receipt") -> bool:
        """Inicia un nuevo documento de impresión."""
        if not self._hprinter:
            return False
        try:
            import win32print
            win32print.StartDocPrinter(self._hprinter, 1, (doc_name, None, "RAW"))
            win32print.StartPagePrinter(self._hprinter)
            return True
        except Exception as e:
            logger.error(f"Error al iniciar documento: {e}")
            return False

    def end_doc(self) -> bool:
        """Finaliza el documento de impresión."""
        if not self._hprinter:
            return False
        try:
            import win32print
            win32print.EndPagePrinter(self._hprinter)
            win32print.EndDocPrinter(self._hprinter)
            return True
        except Exception as e:
            logger.error(f"Error al finalizar documento: {e}")
            return False

    def init(self):
        """Inicializa la impresora (restablece configuración)."""
        self.write(CMD_INIT)
        self.write(CMD_CODEPAGE_850 if self._codepage == "cp850" else CMD_CODEPAGE_437)
        self.write(CMD_LINE_SPACING_NARROW)

    def set_bold(self, enabled: bool = True):
        self.write(CMD_BOLD_ON if enabled else CMD_BOLD_OFF)

    def set_align(self, align: str = "left"):
        if align == "center":
            self.write(CMD_ALIGN_CENTER)
        elif align == "right":
            self.write(CMD_ALIGN_RIGHT)
        else:
            self.write(CMD_ALIGN_LEFT)

    def set_font_double(self, width: bool = False, height: bool = False):
        if width and height:
            self.write(CMD_FONT_DOUBLE_HV)
        elif height:
            self.write(CMD_FONT_DOUBLE_V)
        elif width:
            self.write(CMD_FONT_DOUBLE_H)
        else:
            self.write(CMD_FONT_NORMAL)

    def writeln(self, text: str = ""):
        """Escribe una línea de texto + salto de línea."""
        self.write(self._encode(text) + LF)

    def write_centered(self, text: str):
        """Escribe texto centrado."""
        self.set_align("center")
        self.writeln(text)
        self.set_align("left")

    def write_bold_line(self, text: str):
        """Escribe una línea en negrita."""
        self.set_bold(True)
        self.writeln(text)
        self.set_bold(False)

    def feed(self, lines: int = 3):
        """Avanza papel n líneas."""
        self.write(ESC + b"\x64" + bytes([lines]))

    def cut(self, full: bool = True):
        """Corta el papel."""
        self.write(CMD_CUT_FULL if full else CMD_CUT_PARTIAL)

    # ─── QR Code ───

    def print_qr(self, data: str, module_size: int = 6, error_level: str = "M"):
        """Genera e imprime un código QR.

        Usa la biblioteca qrcode para generar el QR y lo envía a la
        impresora usando los comandos ESC/POS GS ( k para QR.

        Args:
            data: Texto/datos a codificar en el QR.
            module_size: Tamaño del módulo en puntos (1-16).
                        Recomendado: 4 (58mm), 6 (80mm).
            error_level: Nivel de corrección de errores:
                        'L' (7%), 'M' (15%), 'Q' (25%), 'H' (30%).
        """
        try:
            ec_map = {"L": 48, "M": 49, "Q": 50, "H": 51}
            ec = ec_map.get(error_level.upper(), 49)

            qr = qrcode.QRCode(
                version=None,  # auto-fit
                error_correction={
                    "L": qrcode.constants.ERROR_CORRECT_L,
                    "M": qrcode.constants.ERROR_CORRECT_M,
                    "Q": qrcode.constants.ERROR_CORRECT_Q,
                    "H": qrcode.constants.ERROR_CORRECT_H,
                }.get(error_level.upper(), qrcode.constants.ERROR_CORRECT_M),
                box_size=1,
                border=0,
            )
            qr.add_data(data)
            qr.make(fit=True)

            # Obtener matriz de píxeles (True=negro, False=blanco)
            matrix = qr.get_matrix()
            size = len(matrix)

            # Para ESC/POS, renderizamos como bitmap usando GS v 0
            # (rastrer bit image command) que es más universal
            self._print_qr_bitmap(matrix, size, module_size)

        except ImportError:
            logger.warning("qrcode library not installed. pip install qrcode[pil]")
        except Exception as e:
            logger.error(f"Error generando QR: {e}")

    def _print_qr_bitmap(self, matrix: list, size: int, module_size: int):
        """Renderiza la matriz QR como imagen raster ESC/POS.

        Usa el comando GS v 0 (print raster bit image) que es
        soportado por la mayoría de impresoras térmicas.

        Args:
            matrix: Matriz booleana del QR (True=negro).
            size: Tamaño de la matriz (size x size).
            module_size: Escala de cada módulo en puntos.
        """
        # Calcular dimensiones en puntos
        px_size = size * module_size
        # Redondear a múltiplo de 8 para bytes
        bytes_x = (px_size + 7) // 8
        width_bytes = bytes_x * 8

        # Construir datos de bitmap
        bitmap_data = bytearray()
        for y in range(px_size):
            src_y = y // module_size
            for bx in range(bytes_x):
                byte_val = 0
                for bit in range(8):
                    src_x = (bx * 8 + bit) // module_size
                    if src_x < size and matrix[src_y][src_x]:
                        byte_val |= (1 << (7 - bit))
                bitmap_data.append(byte_val)

        # GS v 0 m xL xH yL yH d1...dk
        # m = 0 (normal), 1 (double-width), 2 (double-height), 3 (both)
        # xL, xH = width in bytes, yL, yH = height in dots
        xl = bytes_x % 256
        xh = bytes_x // 256
        yl = px_size % 256
        yh = px_size // 256

        cmd = GS + b"v\x30\x00" + bytes([xl, xh, yl, yh]) + bytes(bitmap_data)
        self.write(cmd)

    def print_receipt(self, orden, items) -> tuple[bool, str]:
        """Imprime un recibo completo.

        Args:
            orden: Objeto Orden con datos de la orden.
            items: Lista de OrdenItem.

        Returns:
            (True, mensaje) si éxito, (False, mensaje_error) si falla.
        """
        if not self.open():
            return False, "No se pudo abrir la impresora."

        try:
            self.start_doc(f"Receipt #{orden.numero}")
            self.init()

            # ─── Title ───
            self.set_font_double(width=True, height=True)
            self.write_centered(app_config.BUSINESS_NAME)
            self.set_font_double()

            # Slogan + address
            if app_config.BUSINESS_SLOGAN:
                self.write_centered(app_config.BUSINESS_SLOGAN)
            self.write_centered(app_config.BUSINESS_ADDRESS)
            if app_config.BUSINESS_PHONE:
                self.write_centered(f"Tel: {app_config.BUSINESS_PHONE}")

            # Separator
            self.writeln("=" * min(self.paper_width, 42))

            # ─── Order Info ───
            self.write_bold_line(f"ORDEN #: {orden.numero}")
            fecha = orden.fecha_creacion[:16] if orden.fecha_creacion else ""
            self.writeln(f"FECHA: {fecha}")
            tipo_labels = {"local": "Comer Aqui", "takeout": "Para Llevar", "delivery": "Delivery"}
            self.writeln(f"TIPO: {tipo_labels.get(orden.tipo, orden.tipo)}")

            # Separator
            self.writeln("-" * min(self.paper_width, 42))

            # ─── Items ───
            self.set_bold(True)
            self.writeln(f"{'CANT':>4} {'DESCRIPCION':<{28}} {'TOTAL':>7}")
            self.set_bold(False)
            self.writeln("-" * min(self.paper_width, 42))

            for item in items:
                nombre = item.producto_nombre[:26]
                qty = f"x{item.cantidad}"
                total = f"{app_config.CURRENCY_SYMBOL}{item.subtotal:.2f}"
                self.writeln(f"{qty:>4} {nombre:<{28}} {total:>7}")

            self.writeln("-" * min(self.paper_width, 42))

            # ─── Totals ───
            subtotal_str = f"{app_config.CURRENCY_SYMBOL}{orden.subtotal:.2f}"
            self.writeln(f"{'SUBTOTAL:':>{35}} {subtotal_str:>7}")

            tax_str = f"{app_config.CURRENCY_SYMBOL}{orden.impuesto:.2f}"
            self.writeln(f"{f'IVA ({int(app_config.TAX_RATE*100)}%):':>{35}} {tax_str:>7}")

            if hasattr(orden, 'costo_delivery') and orden.costo_delivery > 0:
                delivery_str = f"{app_config.CURRENCY_SYMBOL}{orden.costo_delivery:.2f}"
                self.writeln(f"{'DELIVERY:':>{35}} {delivery_str:>7}")

            self.writeln("=" * min(self.paper_width, 42))

            # Total bold + double
            self.set_font_double(width=True, height=False)
            total_str = f"{app_config.CURRENCY_SYMBOL}{orden.total:.2f}"
            self.write_bold_line(f"{'TOTAL':>{27}} {total_str:>10}")
            self.set_font_double()

            # ─── Notes ───
            if orden.notas:
                self.writeln(f"NOTAS: {orden.notas}")
                self.writeln("-" * min(self.paper_width, 42))

            # ─── Delivery Info ───
            if orden.tipo == "delivery":
                if hasattr(orden, 'direccion') and orden.direccion:
                    self.writeln(f"DIR: {orden.direccion}")
                if hasattr(orden, 'telefono_contacto') and orden.telefono_contacto:
                    self.writeln(f"TEL: {orden.telefono_contacto}")
                self.writeln("-" * min(self.paper_width, 42))

            # ─── QR Code (si configurado) ───
            self._print_qr_if_enabled(orden)

            # ─── Footer ───
            self.writeln("")
            self.write_centered("Gracias por su compra!")
            self.write_centered(app_config.APP_NAME)

            # Feed + Cut
            self.feed(3)
            if self.auto_cut:
                self.cut(full=True)

            self.end_doc()
            self.close()

            return True, "Recibo impreso exitosamente."

        except Exception as e:
            self.close()
            logger.error(f"Error imprimiendo recibo: {e}")
            return False, f"Error al imprimir: {e}"

    def _print_qr_if_enabled(self, orden):
        """Imprime QR con info de la orden si la configuración lo habilita."""
        try:
            from database.db_manager import DatabaseManager
            db = DatabaseManager()
            qr_enabled = db.get_config("printer_print_qr")
            if qr_enabled == "0":
                return
        except Exception:
            return  # Si no hay DB o config, no hacer QR

        # Construir datos del QR
        qr_data = (
            f"Orden: {orden.numero}\n"
            f"Total: {app_config.CURRENCY_SYMBOL}{orden.total:.2f}\n"
            f"{app_config.BUSINESS_NAME}\n"
            f"{app_config.BUSINESS_PHONE}"
        )

        # Espacio antes del QR
        self.writeln("")
        self.set_align("center")

        # Módulo según ancho de papel
        module = 4 if self.paper_width <= 32 else 6
        self.print_qr(qr_data, module_size=module, error_level="M")

        # Texto debajo del QR
        self.set_align("center")
        self.writeln(f"#{orden.numero}")
        self.set_align("left")

    def print_test(self) -> tuple[bool, str]:
        """Imprime una página de prueba para verificar la configuración."""
        if not self.open():
            return False, "No se pudo abrir la impresora."

        try:
            self.start_doc("FastBite POS - Test Page")
            self.init()

            self.set_font_double(width=True, height=True)
            self.write_centered("=== TEST ===")
            self.set_font_double()
            self.writeln("")
            self.write_centered("FastBite POS")
            self.writeln("")
            self.writeln("-" * min(self.paper_width, 42))

            lines = [
                "Impresora termica configurada.",
                f"Codificacion: {self._codepage}",
                f"Auto-cut: {'SI' if self.auto_cut else 'NO'}",
                f"Ancho: {self.paper_width} cols",
                "",
                "Caracteres especiales:",

            ]
            # Test special chars
            test_chars = "Espanol: n~n~n~  tildes: a_e_i_o_u_  A_E_I_O_U_"
            test_chars_coded = (
                "Espanol: \xf1\xd1\xf1\xd1  "
                "tildes: \xe1\xe9\xed\xf3\xfa  \xc1\xc9\xcd\xd3\xda"
            )
            lines.append(test_chars)
            lines.append(test_chars_coded)
            lines.append("")
            lines.append("FastBite POS v" + app_config.APP_VERSION)
            lines.append("")

            for line in lines:
                self.writeln(line)

            # QR de prueba
            self.writeln("")
            self.set_align("center")
            self.print_qr("FastBite POS - Test", module_size=6, error_level="M")
            self.set_align("center")
            self.writeln("Escanea para verificar QR")
            self.set_align("left")

            self.writeln("=" * min(self.paper_width, 42))
            self.write_centered("Test completado OK!")

            self.feed(3)
            if self.auto_cut:
                self.cut(full=True)

            self.end_doc()
            self.close()

            return True, "Pagina de prueba impresa correctamente."

        except Exception as e:
            self.close()
            return False, f"Error en prueba: {e}"


# ─── Respaldo de Recibos en PDF ───

def save_receipt_pdf(orden, items) -> tuple[bool, str]:
    """Guarda el recibo como PDF en la carpeta de respaldos.

    Usa PySide6.QtPrintSupport.QPrinter para generar PDF desde
    el HTML del recibo. El archivo se guarda en:
    {APP_DATA_DIR}/receipts/{YYYYMMDD}_{numero_orden}.pdf

    Returns:
        (True, ruta_del_archivo) si éxito, (False, mensaje_error) si falla.
    """
    try:
        # Verificar si está habilitado en config
        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        cfg = db.get_config("printer_save_pdf")
        if cfg == "0":
            return False, "PDF backup disabled in config"
    except Exception:
        pass  # Si no hay DB, intentar igual

    try:
        from PySide6.QtGui import QTextDocument
        from PySide6.QtPrintSupport import QPrinter
        from PySide6.QtCore import QMarginsF, QSizeF

        # Carpeta de respaldos
        receipts_dir = os.path.join(app_config.APP_DATA_DIR, "receipts")
        os.makedirs(receipts_dir, exist_ok=True)

        # Nombre de archivo: fecha + numero_orden
        fecha = orden.fecha_creacion[:10] if orden.fecha_creacion else "unknown"
        safe_numero = orden.numero.replace("/", "-").replace("\\", "-")
        filename = f"{fecha}_{safe_numero}.pdf"
        filepath = os.path.join(receipts_dir, filename)

        # Generar HTML del recibo
        html = format_receipt_html(orden, items, include_qr=True)

        # Configurar impresora PDF
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(filepath)
        printer.setPageSize(QPrinter.PageSize.Custom)
        # Tamaño típico de recibo térmico: 80mm x 297mm
        printer.setPageSizeMM(QSizeF(80, 297))
        printer.setFullPage(True)

        # Renderizar HTML a PDF
        doc = QTextDocument()
        doc.setHtml(html)
        doc.setPageSize(QSizeF(printer.pageRect(QPrinter.Unit.Millimeter).size().width(), -1))
        doc.print_(printer)

        logger.info(f"Recibo PDF guardado: {filepath}")

        # Limpiar recibos antiguos (>30 días)
        _cleanup_old_receipts(receipts_dir, keep_days=30)

        return True, filepath

    except Exception as e:
        logger.error(f"Error al guardar recibo PDF: {e}")
        return False, f"Error al guardar PDF: {e}"


def _cleanup_old_receipts(receipts_dir: str, keep_days: int = 30):
    """Elimina recibos PDF más antiguos que keep_days."""
    try:
        now = datetime.now()
        for fname in os.listdir(receipts_dir):
            if not fname.endswith('.pdf'):
                continue
            fpath = os.path.join(receipts_dir, fname)
            mtime = os.path.getmtime(fpath)
            age_days = (now.timestamp() - mtime) / 86400
            if age_days > keep_days:
                os.remove(fpath)
                logger.debug(f"Recibo antiguo eliminado: {fpath}")
    except Exception as e:
        logger.warning(f"Error limpiando recibos antiguos: {e}")


# ─── Función de compatibilidad (usada desde payment_dialog) ───
def print_receipt(orden, items, printer_name=None, auto_cut=None, paper_width=None):
    """Imprime un recibo usando ESC/POS. Compatible con la API anterior.
    Antes de imprimir, guarda automáticamente un backup PDF del recibo.

    Args:
        orden: Objeto Orden
        items: Lista de OrdenItem
        printer_name: Nombre de impresora o None (usa config/defecto)
        auto_cut: True/False o None (usa config)
        paper_width: 48 (80mm) o 32 (58mm) o None (usa config)

    Returns:
        (success: bool, message: str)
    """
    # ─── Backup PDF automático antes de imprimir ───
    pdf_ok, pdf_path = save_receipt_pdf(orden, items)

    # Leer configuración desde DB (o usar defaults)
    try:
        from database.db_manager import DatabaseManager
        db = DatabaseManager()
        cfg_printer = db.get_config("printer_name") or printer_name
        cfg_auto_cut = db.get_config("printer_auto_cut")
        cfg_paper = db.get_config("printer_paper_width")
        cfg_codepage = db.get_config("printer_codepage")

        if auto_cut is None:
            auto_cut = cfg_auto_cut != "0" if cfg_auto_cut is not None else True

        if paper_width is None and cfg_paper:
            paper_width = int(cfg_paper)
        if paper_width is None:
            paper_width = 48

        codepage = cfg_codepage or "cp850"
    except Exception:
        if auto_cut is None:
            auto_cut = True
        if paper_width is None:
            paper_width = 48
        codepage = "cp850"
        cfg_printer = printer_name

    printer = ESCPOSPrinter(
        printer_name=cfg_printer,
        auto_cut=auto_cut,
        paper_width=paper_width,
        codepage=codepage,
    )
    success, msg = printer.print_receipt(orden, items)

    # Si el PDF se guardó bien, agregarlo al mensaje
    if pdf_ok:
        msg += f"\n📄 PDF: {pdf_path}"

    return success, msg
