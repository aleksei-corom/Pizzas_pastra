"""Vista Asistente Inteligente de Ventas.

Motor de inteligencia local que analiza patrones de ventas,
inventario y comportamiento para generar insights accionables.

No depende de APIs externas — toda la inteligencia es local.

Módulo diferenciador: ningún otro POS open-source latino tiene esto.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame,
)
from PySide6.QtCore import Qt, QTimer

from database.asistente_service import AsistenteService
from views.layouts import create_page_header
from views.components.insight_card import InsightCard


class AsistenteView(QWidget):
    """Vista del asistente inteligente con insights y métricas.

    Se actualiza automáticamente cada 5 minutos o manualmente.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._svc = AsistenteService()
        self._build_ui()
        self.cargar_datos()

        # Auto-refresh cada 5 minutos
        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self.cargar_datos)
        self._auto_timer.start(300000)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(16)

        # Header con botón de refresh
        btn_refresh = QPushButton("🔄  Analizar Ahora")
        btn_refresh.setProperty("class", "secondary")
        btn_refresh.clicked.connect(self.cargar_datos)

        self._header = create_page_header(
            "\U0001f9e0  Asistente Inteligente",
            "Insights basados en tus datos de ventas — se actualiza automáticamente",
            actions=[btn_refresh]
        )
        layout.addLayout(self._header)

        # Scroll area para insights
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setObjectName("product-scroll-area")

        self._container = QWidget()
        self._container_layout = QVBoxLayout(self._container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(12)

        scroll.setWidget(self._container)
        layout.addWidget(scroll, 1)

    def cargar_datos(self):
        """Ejecuta el motor de análisis y muestra los insights."""
        # Limpiar insights anteriores
        while self._container_layout.count():
            child = self._container_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        try:
            insights = self._svc.generar_insights()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Error generando insights: %s", e, exc_info=True)
            insights = []

        if not insights:
            empty = QLabel("\U0001f4ca  No hay datos suficientes para generar insights.\n\n"
                             "Registra algunas ventas y el asistente comenzará a analizar patrones.")
            empty.setProperty("class", "caption")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty.setWordWrap(True)
            self._container_layout.addWidget(empty)
            self._container_layout.addStretch()
            return

        # Agrupar por tipo para secciones
        secciones = {
            "alerta": {"titulo": "\u26a0\ufe0f  Alertas", "insights": []},
            "oportunidad": {"titulo": "\U0001f4a0  Oportunidades", "insights": []},
            "sugerencia": {"titulo": "\U0001f4a1  Sugerencias", "insights": []},
            "positivo": {"titulo": "\u2705  Buenas Noticias", "insights": []},
            "info": {"titulo": "\u2139\ufe0f  Información", "insights": []},
        }

        for insight in insights:
            key = insight.tipo if insight.tipo in secciones else "info"
            secciones[key]["insights"].append(insight)

        # Renderizar secciones con insights
        for tipo, seccion in secciones.items():
            if not seccion["insights"]:
                continue

            # Título de sección
            lbl = QLabel(seccion["titulo"])
            lbl.setProperty("class", "section")
            self._container_layout.addWidget(lbl)

            # Insight cards
            for insight in seccion["insights"]:
                card = InsightCard(insight)
                card.action_clicked.connect(self._on_action)
                self._container_layout.addWidget(card)

        self._container_layout.addStretch()

        # Actualizar subtítulo con conteo
        n_alertas = len(secciones["alerta"]["insights"])
        n_oportunidades = len(secciones["oportunidad"]["insights"])
        if n_alertas > 0:
            subtitle = f"{len(insights)} insights generados — {n_alertas} alerta(s) activa(s)"
        elif n_oportunidades > 0:
            subtitle = f"{len(insights)} insights generados — {n_oportunidades} oportunidad(es)"
        else:
            subtitle = f"{len(insights)} insights generados — todo en orden"

        # Limpiar header viejo y recrear
        while self._header.count():
            child = self._header.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                # No eliminar el stretch
                pass

        btn_refresh = QPushButton("\U0001f504  Analizar Ahora")
        btn_refresh.setProperty("class", "secondary")
        btn_refresh.clicked.connect(self.cargar_datos)

        new_header = create_page_header(
            "\U0001f9e0  Asistente Inteligente",
            subtitle,
            actions=[btn_refresh]
        )
        while new_header.count():
            item = new_header.takeAt(0)
            if item.widget():
                self._header.addWidget(item.widget())

    def _on_action(self, accion: str):
        """Navega a la sección correspondiente cuando el usuario hace clic en una acción."""
        # Emite una señal que el MainWindow puede captar
        if hasattr(self, 'navigation_requested'):
            self.navigation_requested.emit(accion)
