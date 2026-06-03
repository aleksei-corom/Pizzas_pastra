
from PySide6.QtWidgets import QLabel

class AvatarWidget(QLabel):
    def __init__(self, initials="", size=40, color=None, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        from PySide6.QtCore import Qt
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg = color or "#6366f1"
        self.setStyleSheet(f"""
            background-color: {bg}; color: #ffffff;
            border-radius: {size//2}px;
            font-weight: 700; font-size: {size//3}px;
        """)
        self.setText(initials.upper()[:2])
