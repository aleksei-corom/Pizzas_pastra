"""Kitchen Display System (KDS) — Pantalla de Cocina.

Muestra órdenes en tiempo real agrupadas por estado, con temporizadores
codificados por color, notificaciones sonoras y controles de cambio de estado.
Optimizada para uso en cocina con tarjetas grandes y legibles.
"""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QApplication,
)
from PySide6.QtCore import Qt, QTimer, Signal

from database.orden_service import OrdenService
from database.repartidor_service import RepartidorService
import config as app_config


# ─── Constantes de tiempo ───
TIEMPO_NORMAL = 5      # minutos antes de pasar a amarillo
TIEMPO_ALERTA = 12     # minutos antes de pasar a rojo
REFRESH_INTERVAL_MS = 5000  # 5 segundos


class KDSOrderCard(QFrame):
    """Tarjeta de orden individual para el KDS."""

    status_changed = Signal(int, str)  # orden_id, nuevo_estado

    def __init__(self, orden, items_count=0, parent=None):
        super().__init__(parent)
        self.orden = orden
        self.items_count = items_count
        self.setObjectName("kds-card")
        self.setProperty("class", "kds-card")
        self.setMinimumHeight(180)
        self._build_ui()
        self._update_timer_display()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # ── Fila superior: número + tipo + tiempo ──
        header = QHBoxLayout()
        header.setSpacing(8)

        # Número de orden (grande)
        self._lbl_numero = QLabel(f"#{self.orden.numero.split('-')[-1]}")
        self._lbl_numero.setProperty("class", "kds-order-number")
        font = self._lbl_numero.font()
        font.setPointSize(22)
        font.setBold(True)
        self._lbl_numero.setFont(font)
        header.addWidget(self._lbl_numero)

        # Tipo de orden
        tipo_icon = app_config.ORDER_TYPES.get(self.orden.tipo, "🍽️").split()[0]
        tipo_lbl = QLabel(tipo_icon)
        tipo_lbl.setProperty("class", "kds-type-icon")
        tipo_lbl.setToolTip(app_config.ORDER_TYPES.get(self.orden.tipo, self.orden.tipo))
        header.addWidget(tipo_lbl)

        header.addStretch()

        # Temporizador
        self._lbl_tiempo = QLabel("--:--")
        self._lbl_tiempo.setProperty("class", "kds-timer")
        header.addWidget(self._lbl_tiempo)

        # Delivery info
        if self.orden.tipo == "delivery" and self.orden.cliente_nombre:
            delivery_tag = QLabel(f"🛵 {self.orden.cliente_nombre}")
            delivery_tag.setProperty("class", "kds-delivery-tag")
            header.addWidget(delivery_tag)

        layout.addLayout(header)

        # ── Items ──
        items_widget = QWidget()
        items_widget.setProperty("class", "kds-items")
        items_layout = QVBoxLayout(items_widget)
        items_layout.setContentsMargins(0, 4, 0, 4)
        items_layout.setSpacing(2)

        items = self.orden.items if hasattr(self.orden, 'items') and self.orden.items else []
        if not items:
            # Placeholder — cargaremos items por separado
            placeholder = QLabel(f"{self.items_count} item(s)")
            placeholder.setProperty("class", "kds-item-text")
            items_layout.addWidget(placeholder)
        else:
            for item in items:
                item_text = f"×{item.cantidad}  {item.producto_nombre}"
                item_lbl = QLabel(item_text)
                item_lbl.setProperty("class", "kds-item-text")
                items_layout.addWidget(item_lbl)

        # Si hay notas, mostrarlas
        if self.orden.notas:
            notas_lbl = QLabel(f"📝 {self.orden.notas}")
            notas_lbl.setProperty("class", "kds-note")
            items_layout.addWidget(notas_lbl)

        items_layout.addStretch()
        layout.addWidget(items_widget, 1)

        # ── Botones de acción (según estado actual) ──
        btns = QHBoxLayout()
        btns.setSpacing(8)

        if self.orden.estado == "pending":
            btn_aceptar = QPushButton("👨‍🍳 Aceptar")
            btn_aceptar.setProperty("class", "kds-btn-primary")
            btn_aceptar.setFixedHeight(42)
            btn_aceptar.clicked.connect(lambda: self.status_changed.emit(self.orden.id, "preparing"))
            btns.addWidget(btn_aceptar, 1)

        elif self.orden.estado == "preparing":
            btn_listo = QPushButton("✅ Listo")
            btn_listo.setProperty("class", "kds-btn-success")
            btn_listo.setFixedHeight(42)
            btn_listo.clicked.connect(lambda: self.status_changed.emit(self.orden.id, "ready"))
            btns.addWidget(btn_listo, 1)

            btn_volver = QPushButton("⏪ Pendiente")
            btn_volver.setProperty("class", "kds-btn-secondary")
            btn_volver.setFixedHeight(42)
            btn_volver.clicked.connect(lambda: self.status_changed.emit(self.orden.id, "pending"))
            btns.addWidget(btn_volver)

        elif self.orden.estado == "ready":
            btn_entregado = QPushButton("📦 Entregado")
            btn_entregado.setProperty("class", "kds-btn-success")
            btn_entregado.setFixedHeight(42)
            btn_entregado.clicked.connect(lambda: self.status_changed.emit(self.orden.id, "delivered"))
            btns.addWidget(btn_entregado, 1)

            btn_volver_prep = QPushButton("⏪ Preparación")
            btn_volver_prep.setProperty("class", "kds-btn-secondary")
            btn_volver_prep.setFixedHeight(42)
            btn_volver_prep.clicked.connect(lambda: self.status_changed.emit(self.orden.id, "preparing"))
            btns.addWidget(btn_volver_prep)

        # Delivery — botón de asignar repartidor
        if self.orden.tipo == "delivery" and self.orden.estado == "ready" and not self.orden.repartidor_id:
            from database.repartidor_service import RepartidorService
            rep_svc = RepartidorService()
            disponibles = rep_svc.get_repartidores_disponibles()
            if disponibles:
                btn_asignar = QPushButton(f"🛵 Asignar ({len(disponibles)} disp.)")
                btn_asignar.setProperty("class", "kds-btn-warning")
                btn_asignar.setFixedHeight(42)
                btn_asignar.clicked.connect(self._asignar_repartidor)
                btns.addWidget(btn_asignar)

        layout.addLayout(btns)

    def _asignar_repartidor(self):
        """Asigna el primer repartidor disponible."""
        rep_svc = RepartidorService()
        disponibles = rep_svc.get_repartidores_disponibles()
        if disponibles:
            rep = disponibles[0]
            rep_svc.asignar_repartidor(self.orden.id, rep.id)
            self.status_changed.emit(self.orden.id, "en_delivery")

    def _update_timer_display(self):
        """Actualiza el temporizador y el color de la tarjeta."""
        try:
            created = datetime.fromisoformat(self.orden.fecha_creacion)
        except (ValueError, TypeError):
            created = datetime.now()

        elapsed = datetime.now() - created
        total_min = elapsed.total_seconds() / 60

        # Formatear tiempo
        mins = int(total_min)
        secs = int(elapsed.total_seconds() % 60)
        self._lbl_tiempo.setText(f"{mins:02d}:{secs:02d}")

        # Color según urgencia (propiedades separadas para Qt stylesheet)
        if total_min > TIEMPO_ALERTA:
            urgency = "critical"
        elif total_min > TIEMPO_NORMAL:
            urgency = "warning"
        else:
            urgency = "normal"

        self._lbl_tiempo.setProperty("urgency", urgency)
        self.setProperty("urgency", urgency)

        # Forzar re-aplicación de estilos
        self._lbl_tiempo.style().unpolish(self._lbl_tiempo)
        self._lbl_tiempo.style().polish(self._lbl_tiempo)
        self.style().unpolish(self)
        self.style().polish(self)

    def refresh_timer(self):
        """Llamado periódicamente para actualizar el reloj."""
        self._update_timer_display()


class KDSColumn(QFrame):
    """Columna de estado del KDS (Pendientes / Preparando / Listos)."""

    status_changed = Signal(int, str)

    def __init__(self, title, icon, status_key, empty_text="Sin órdenes", parent=None):
        super().__init__(parent)
        self.status_key = status_key
        self._cards = []
        self.setObjectName("kds-column")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Encabezado de columna ──
        header = QFrame()
        header.setObjectName("kds-column-header")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 12, 16, 12)

        self._title_lbl = QLabel(f"{icon}  {title}")
        self._title_lbl.setProperty("class", "kds-column-title")
        h_layout.addWidget(self._title_lbl)

        self._count_badge = QLabel("0")
        self._count_badge.setProperty("class", "kds-count-badge")
        h_layout.addWidget(self._count_badge)

        layout.addWidget(header)

        # ── Scroll de tarjetas ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setObjectName("kds-scroll")

        self._scroll_content = QWidget()
        self._scroll_layout = QVBoxLayout(self._scroll_content)
        self._scroll_layout.setContentsMargins(12, 12, 12, 12)
        self._scroll_layout.setSpacing(10)
        self._scroll_layout.addStretch()

        scroll.setWidget(self._scroll_content)
        layout.addWidget(scroll, 1)

    def set_ordenes(self, ordenes_list):
        """Reemplaza todas las tarjetas de la columna."""
        # Limpiar tarjetas existentes
        for card in self._cards:
            self._scroll_layout.removeWidget(card)
            card.deleteLater()
        self._cards = []

        if not ordenes_list:
            empty = QLabel(f"💭  {self.status_key}")
            empty.setProperty("class", "kds-empty")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._scroll_layout.insertWidget(0, empty)
            self._count_badge.setText("0")
            return

        # Remover widget "empty" si existe (buscarlo en todos los ítems del layout)
        for i in range(self._scroll_layout.count()):
            item = self._scroll_layout.itemAt(i)
            if item and item.widget() and item.widget().property("class") == "kds-empty":
                w = self._scroll_layout.takeAt(i).widget()
                w.deleteLater()
                break

        for orden_data in ordenes_list:
            if isinstance(orden_data, dict):
                orden = orden_data.get("orden", orden_data)
                items_count = orden_data.get("items_count", 0)
            else:
                orden = orden_data
                items_count = 0

            # Cargar items si no están
            if not hasattr(orden, 'items') or not orden.items:
                from database.orden_service import OrdenService
                o_svc = OrdenService()
                orden.items = o_svc.get_orden_items(orden.id)
                if not items_count and orden.items:
                    items_count = len(orden.items)

            card = KDSOrderCard(orden, items_count)
            card.status_changed.connect(self.status_changed.emit)
            self._cards.append(card)
            # Insertar antes del stretch
            self._scroll_layout.insertWidget(self._scroll_layout.count() - 1, card)

        self._count_badge.setText(str(len(ordenes_list)))

    def refresh_timers(self):
        """Actualiza los temporizadores de todas las tarjetas."""
        for card in self._cards:
            card.refresh_timer()


class KitchenDisplayView(QWidget):
    """Pantalla principal del Kitchen Display System (KDS)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.orden_svc = OrdenService()
        self.rep_svc = RepartidorService()
        self._prev_pending_count = 0

        self._build_ui()
        self._setup_refresh_timer()
        self.cargar_datos()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── Header ──
        header = QHBoxLayout()
        header.setSpacing(16)

        title_lbl = QLabel("👨‍🍳  Pantalla de Cocina")
        title_lbl.setProperty("class", "title")
        header.addWidget(title_lbl)

        header.addStretch()

        # Stats rápidos
        self._stat_pendientes, self._stat_val_pendientes = self._make_stat_label("⏳ Pendientes", "0", "#fbbf24")
        header.addWidget(self._stat_pendientes)
        self._stat_preparando, self._stat_val_preparando = self._make_stat_label("👨‍🍳 Preparando", "0", "#6366f1")
        header.addWidget(self._stat_preparando)
        self._stat_listos, self._stat_val_listos = self._make_stat_label("✅ Listos", "0", "#34d399")
        header.addWidget(self._stat_listos)
        self._stat_delivery, self._stat_val_delivery = self._make_stat_label("🛵 En Camino", "0", "#fb923c")
        header.addWidget(self._stat_delivery)

        # Reloj actual
        self._clock_lbl = QLabel()
        self._clock_lbl.setProperty("class", "kds-clock")
        header.addWidget(self._clock_lbl)
        self._update_clock()

        # Botón refresh manual
        btn_refresh = QPushButton("🔄")
        btn_refresh.setFixedSize(42, 42)
        btn_refresh.setToolTip("Actualizar manualmente")
        btn_refresh.setProperty("class", "secondary")
        btn_refresh.clicked.connect(self.cargar_datos)
        header.addWidget(btn_refresh)

        # Botón fullscreen
        btn_fullscreen = QPushButton("⛶")
        btn_fullscreen.setFixedSize(42, 42)
        btn_fullscreen.setToolTip("Pantalla completa")
        btn_fullscreen.setProperty("class", "secondary")
        btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        header.addWidget(btn_fullscreen)

        layout.addLayout(header)

        # ── Cuatro columnas de órdenes ──
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(16)

        self._col_pending = KDSColumn("Pendientes", "⏳", "pending",
                                       "No hay órdenes pendientes")
        self._col_pending.status_changed.connect(self._on_status_change)
        columns_layout.addWidget(self._col_pending, 1)

        self._col_preparing = KDSColumn("En Preparación", "👨‍🍳", "preparing",
                                         "Nada en preparación")
        self._col_preparing.status_changed.connect(self._on_status_change)
        columns_layout.addWidget(self._col_preparing, 1)

        self._col_ready = KDSColumn("Listos", "✅", "ready",
                                     "No hay órdenes listas")
        self._col_ready.status_changed.connect(self._on_status_change)
        columns_layout.addWidget(self._col_ready, 1)

        # Columna de delivery activo (en_delivery) — antes las órdenes desaparecían aquí
        self._col_delivery = KDSColumn("En Camino", "🛵", "en_delivery",
                                        "Sin pedidos en camino")
        self._col_delivery.status_changed.connect(self._on_status_change)
        columns_layout.addWidget(self._col_delivery, 1)

        layout.addLayout(columns_layout, 1)

        # ── Botón de sonido de prueba ──
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()

        test_btn = QPushButton("🔔  Probar Sonido")
        test_btn.setProperty("class", "ghost")
        test_btn.setFixedHeight(32)
        test_btn.clicked.connect(self._notify_new_orders)
        bottom_bar.addWidget(test_btn)

        layout.addLayout(bottom_bar)

    def _make_stat_label(self, title, value, color):
        """Crea una etiqueta de estadística rápida."""
        w = QFrame()
        w.setProperty("class", "card-light")
        l = QHBoxLayout(w)
        l.setContentsMargins(12, 6, 12, 6)
        l.setSpacing(6)
        lbl = QLabel(title)
        lbl.setProperty("class", "caption")
        l.addWidget(lbl)
        val = QLabel(value)
        val.setObjectName(f"kds-stat-val-{title.split()[0]}")
        val.setProperty("class", "bold")
        val.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 800;")
        l.addWidget(val)
        return w, val

    def _update_stats(self, pending_count, preparing_count, ready_count, delivery_count=0):
        """Actualiza los contadores de estadísticas."""
        self._stat_val_pendientes.setText(str(pending_count))
        self._stat_val_preparando.setText(str(preparing_count))
        self._stat_val_listos.setText(str(ready_count))
        self._stat_val_delivery.setText(str(delivery_count))

    def _update_clock(self):
        now = datetime.now()
        self._clock_lbl.setText(now.strftime("🕐 %H:%M"))

    def _setup_refresh_timer(self):
        self._refresh_timer = QTimer(self)
        self._refresh_timer.timeout.connect(self._auto_refresh)
        self._refresh_timer.start(REFRESH_INTERVAL_MS)

        # Reloj se actualiza cada segundo
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)

        # Temporizadores de tarjetas se actualizan cada 30s (ahorra CPU)
        self._timer_updater = QTimer(self)
        self._timer_updater.timeout.connect(self._refresh_timers)
        self._timer_updater.start(30_000)

    def _auto_refresh(self):
        """Auto-refresh que detecta nuevas órdenes y notifica."""
        old_pending = self._prev_pending_count
        self.cargar_datos()
        new_pending = self._prev_pending_count

        # Si hay nuevas órdenes pendientes, notificar
        if new_pending > old_pending:
            self._notify_new_orders()

    def _refresh_timers(self):
        """Actualiza los temporizadores visibles."""
        self._col_pending.refresh_timers()
        self._col_preparing.refresh_timers()
        self._col_ready.refresh_timers()
        self._col_delivery.refresh_timers()

    def _notify_new_orders(self):
        """Notificación sonora + visual."""
        # Sonido del sistema
        QApplication.beep()
        QApplication.beep()

        # Flash visual en el header (cambiar temporalmente el fondo)
        # Se podría hacer con una animación, pero por ahora un parpadeo simple

    def cargar_datos(self):
        """Carga todas las órdenes activas de cocina."""
        hoy = datetime.now().strftime("%Y-%m-%d")

        # Cargar órdenes activas (pending, preparing, ready, en_delivery)
        estados_activos = ["pending", "preparing", "ready", "en_delivery"]
        todas = []

        for estado in estados_activos:
            rows = self.orden_svc.get_ordenes_con_items_count(
                fecha=hoy, estado=estado, limit=50
            )
            todas.extend(rows)

        # Separar por estado
        pending = [r for r in todas if r["orden"].estado == "pending"]
        preparing = [r for r in todas if r["orden"].estado == "preparing"]
        ready = [r for r in todas if r["orden"].estado == "ready"]
        en_delivery = [r for r in todas if r["orden"].estado == "en_delivery"]

        # Actualizar columnas
        self._col_pending.set_ordenes(pending)
        self._col_preparing.set_ordenes(preparing)
        self._col_ready.set_ordenes(ready)
        self._col_delivery.set_ordenes(en_delivery)

        # Guardar conteo anterior para detección de nuevas órdenes
        self._prev_pending_count = len(pending)

        # Actualizar estadísticas
        self._update_stats(len(pending), len(preparing), len(ready), len(en_delivery))

    def _on_status_change(self, orden_id, nuevo_estado):
        """Maneja cambio de estado desde una tarjeta."""
        self.orden_svc.actualizar_estado_orden(orden_id, nuevo_estado)
        self.cargar_datos()

        # Si la orden está lista, notificar
        if nuevo_estado == "ready":
            QApplication.beep()

    def _toggle_fullscreen(self):
        """Alterna pantalla completa."""
        window = self.window()
        if window.isFullScreen():
            window.showNormal()
        else:
            window.showFullScreen()
