
from PySide6.QtWidgets import QLabel


class AvatarWidget(QLabel):
    """Avatar circular con iniciales — theme-aware.

    Si no se pasa color, usa el color primario del tema activo.
    """

    def __init__(self, initials="", size=40, color=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        from PySide6.QtCore import Qt
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Color del tema activo si no se especifica
        if color is None:
            try:
                from views.themes.theme_helper import th
                bg = th("primary")
            except Exception:
                bg = "#e63946"
        else:
            bg = color

        self.setStyleSheet(f"""
            background-color: {bg}; color: #ffffff;
            border-radius: {size // 2}px;
            font-weight: 700; font-size: {size // 3}px;
        """)
        self.setText(initials.upper()[:2])
