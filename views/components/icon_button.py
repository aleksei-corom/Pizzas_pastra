
from PySide6.QtWidgets import QPushButton

class IconButton(QPushButton):
    def __init__(self, icon_str, tooltip="", size=36, parent=None):
        super().__init__(icon_str, parent)
        self.setFixedSize(size, size)
        from PySide6.QtCore import Qt
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(tooltip)
        self.setProperty("class", "icon-btn")
