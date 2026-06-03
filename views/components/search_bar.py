"""Barra de búsqueda con icono."""

from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Qt


class SearchBar(QLineEdit):
    """Input de búsqueda con placeholder e icono de lupa."""

    def __init__(self, placeholder="Buscar...", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(f"🔍  {placeholder}")
        self.setClearButtonEnabled(True)
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QLineEdit {
                background-color: #334155;
                color: #f1f5f9;
                border: 1.5px solid #475569;
                border-radius: 10px;
                padding: 8px 16px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #e63946;
                background-color: #1e293b;
            }
            QLineEdit::placeholder {
                color: #94a3b8;
            }
        """)
