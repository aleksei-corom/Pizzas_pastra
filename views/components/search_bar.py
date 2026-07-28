"""Barra de búsqueda con icono — theme-aware."""

from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Qt
from views.themes.theme_helper import th


class SearchBar(QLineEdit):
    """Input de búsqueda con placeholder e icono de lupa.

    Usa tokens del tema activo en vez de colores hardcodeados,
    garantizando consistencia visual en cualquier tema.
    """

    def __init__(self, placeholder="Buscar...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(f"\U0001f50d  {placeholder}")
        self.setClearButtonEnabled(True)
        self.setFixedHeight(40)
        self._apply_style()

    def _apply_style(self):
        """Aplica estilos usando tokens del tema activo."""
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {th('bg_input')};
                color: {th('fg')};
                border: 1.5px solid {th('border')};
                border-radius: 10px;
                padding: 8px 16px;
                font-size: 14px;
            }}
            QLineEdit:focus {{
                border-color: {th('primary')};
                background-color: {th('bg_card')};
            }}
            QLineEdit::placeholder {{
                color: {th('fg_muted')};
            }}
        """)
