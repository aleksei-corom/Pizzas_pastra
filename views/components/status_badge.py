
from PySide6.QtWidgets import QLabel

class StatusBadge(QLabel):
    """status: 'success' | 'warning' | 'danger' | 'info'"""
    def __init__(self, text, status="success", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", f"badge-{status}")
        self.setFixedHeight(28)
        from PySide6.QtCore import Qt
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
