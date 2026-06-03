"""Helpers de layout: form rows, page headers, stats grids."""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QPushButton

from views.components.card_widget import CardWidget
from views.components.status_badge import StatusBadge


def create_form_row(label_text: str, widget, required=False, hint=""):
    """Retorna QVBoxLayout con label + widget + hint opcional."""
    row = QVBoxLayout()
    row.setSpacing(6)
    text = f"{label_text} *" if required else label_text
    lbl = QLabel(text)
    lbl.setProperty("class", "section")
    row.addWidget(lbl)
    row.addWidget(widget)
    if hint:
        h = QLabel(hint)
        h.setProperty("class", "caption")
        row.addWidget(h)
    return row


def create_page_header(title: str, subtitle="", actions=None):
    """Retorna QHBoxLayout con título + subtítulo a la izquierda, botones a la derecha."""
    header = QHBoxLayout()
    left = QVBoxLayout()
    left.setSpacing(4)
    t = QLabel(title)
    t.setProperty("class", "title")
    left.addWidget(t)
    if subtitle:
        s = QLabel(subtitle)
        s.setProperty("class", "subtitle")
        left.addWidget(s)
    header.addLayout(left)
    header.addStretch()
    if actions:
        for btn in actions:
            header.addWidget(btn)
    return header


def create_stats_grid(stats: list) -> QHBoxLayout:
    """Crea grid horizontal de tarjetas de métricas.

    stats = [{'label': 'Total', 'value': '1,248', 'badge': 'Activo', 'status': 'success'}, ...]
    """
    row = QHBoxLayout()
    row.setSpacing(16)
    for s in stats:
        card = CardWidget(title=s['value'], subtitle=s['label'], padding=20)
        if s.get('badge'):
            card.add_widget(StatusBadge(s['badge'], s.get('status', 'info')))
        row.addWidget(card)
    return row
