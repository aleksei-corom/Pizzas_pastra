
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel

class CardWidget(QFrame):
    def __init__(self, parent=None, title="", subtitle="", padding=20):
        super().__init__(parent)
        self.setProperty("class", "card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(padding, padding, padding, padding)
        self._layout.setSpacing(12)
        if title:
            t = QLabel(title); t.setProperty("class", "title"); self._layout.addWidget(t)
        if subtitle:
            s = QLabel(subtitle); s.setProperty("class", "subtitle"); self._layout.addWidget(s)
        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(10)
        self._layout.addLayout(self.content_layout)
        self._layout.addStretch()

    def add_widget(self, w): self.content_layout.addWidget(w)
    def add_layout(self, l): self.content_layout.addLayout(l)
    def add_widget_header(self, h_widget):
        """Agrega un widget header antes del content_layout."""
        self._layout.insertWidget(self._layout.count() - 2, h_widget)
