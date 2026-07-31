"""Motor de inteligencia local para el Asistente de Ventas.

Analiza patrones de ventas, inventario y comportamiento de clientes
para generar insights accionables SIN depender de APIs externas.

Toda la inteligencia es local basada en datos históricos de la DB.
"""

from datetime import datetime, timedelta
from typing import Optional

from database.db_manager import DatabaseManager
from database.models import Insight


class AsistenteService:
    """Genera insights y sugerencias basados en datos locales.

    Tipos de insight:
    - oportunidad: Producto vendiendo más de lo normal (promocionar)
    - alerta: Producto con baja rotación o posible desabasto
    - positivo: Buen desempeño general
    - sugerencia: Recomendación basada en patrones
    """

    def __init__(self, db: Optional[DatabaseManager] = None):
        self._db = db or DatabaseManager()

    # ─── MOTOR PRINCIPAL ─────────────────────────────────────────────

    def generar_insights(self) -> list[Insight]:
        """Genera todos los insights disponibles basados en datos actuales.

        Ejecuta múltiples análisis y retorna una lista priorizada de insights.
        """
        insights = []

        try:
            insights.extend(self._analizar_ventas_hoy())
        except Exception:
            pass

        try:
            insights.extend(self._analizar_productos_estrella())
        except Exception:
            pass

        try:
            insights.extend(self._analizar_productos_estancados())
        except Exception:
            pass

        try:
            insights.extend(self._analizar_horas_pico())
        except Exception:
            pass

        try:
            insights.extend(self._analizar_tendencia_semanal())
        except Exception:
            pass

        try:
            insights.extend(self._analizar_ticket_promedio())
        except Exception:
            pass

        try:
            insights.extend(self._analizar_tipos_pedido())
        except Exception:
            pass

        try:
            insights.extend(self._analizar_clientes_frecuentes())
        except Exception:
            pass

        # Ordenar por prioridad: alertas primero, luego oportunidades
        prioridad = {"alerta": 0, "oportunidad": 1, "sugerencia": 2, "positivo": 3}
        insights.sort(key=lambda x: prioridad.get(x.tipo, 4))

        return insights

    # ─── ANÁLISIS DE VENTAS DEL DÍA ──────────────────────────────────

    def _analizar_ventas_hoy(self) -> list[Insight]:
        """Compara ventas de hoy vs ayer y genera insight."""
        hoy = datetime.now().strftime("%Y-%m-%d")
        ayer = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        hoy_row = self._db.conn.execute(
            "SELECT COUNT(*) as ordenes, COALESCE(SUM(total),0) as total "
            "FROM ordenes WHERE fecha_creacion LIKE ? AND estado != 'cancelled'",
            (f"{hoy}%",)
        ).fetchone()

        ayer_row = self._db.conn.execute(
            "SELECT COUNT(*) as ordenes, COALESCE(SUM(total),0) as total "
            "FROM ordenes WHERE fecha_creacion LIKE ? AND estado != 'cancelled'",
            (f"{ayer}%",)
        ).fetchone()

        if hoy_row["total"] == 0 and ayer_row["total"] == 0:
            return [Insight(
                tipo="sugerencia",
                titulo="Sin ventas registradas",
                descripcion="No hay ventas hoy ni ayer. Verifica que el sistema esté operativo y que los productos estén disponibles.",
                accion="Ir a Punto de Venta"
            )]

        insights = []

        if ayer_row["total"] > 0:
            cambio = ((hoy_row["total"] - ayer_row["total"]) / ayer_row["total"]) * 100

            if cambio >= 20:
                insights.append(Insight(
                    tipo="positivo",
                    titulo="Ventas en alza hoy",
                    descripcion=f"Las ventas subieron un {cambio:.0f}% respecto a ayer. "
                                f"Hoy: ${hoy_row['total']:.2f} vs Ayer: ${ayer_row['total']:.2f}",
                    metrica_valor=f"+{cambio:.0f}%",
                    metrica_label="vs ayer",
                    timestamp=datetime.now().isoformat()
                ))
            elif cambio <= -20:
                insights.append(Insight(
                    tipo="alerta",
                    titulo="Caída en ventas hoy",
                    descripcion=f"Las ventas cayeron un {abs(cambio):.0f}% respecto a ayer. "
                                f"Considera activar una promoción para atraer clientes.",
                    metrica_valor=f"{cambio:.0f}%",
                    metrica_label="vs ayer",
                    accion="Crear promoción",
                    timestamp=datetime.now().isoformat()
                ))

        # Insight de órdenes
        if hoy_row["ordenes"] > 0:
            ticket = hoy_row["total"] / hoy_row["ordenes"]
            insights.append(Insight(
                tipo="info" if len(insights) > 0 else "positivo",
                titulo=f"{hoy_row['ordenes']} órdenes procesadas",
                descripcion=f"Ticket promedio de ${ticket:.2f} con un total de ${hoy_row['total']:.2f}.",
                metrica_valor=f"${hoy_row['total']:.0f}",
                metrica_label="Ventas hoy",
                timestamp=datetime.now().isoformat()
            ))

        return insights

    # ─── PRODUCTOS ESTRELLA ──────────────────────────────────────────

    def _analizar_productos_estrella(self) -> list[Insight]:
        """Identifica los productos más vendidos del día."""
        hoy = datetime.now().strftime("%Y-%m-%d")

        rows = self._db.conn.execute(
            "SELECT oi.producto_nombre, SUM(oi.cantidad) as total_qty, "
            "SUM(oi.cantidad * oi.precio_unitario) as ingresos "
            "FROM orden_items oi "
            "JOIN ordenes o ON oi.orden_id = o.id "
            "WHERE o.fecha_creacion LIKE ? AND o.estado != 'cancelled' "
            "GROUP BY oi.producto_nombre ORDER BY ingresos DESC LIMIT 3",
            (f"{hoy}%",)
        ).fetchall()

        if not rows:
            return []

        top = rows[0]
        insights = [Insight(
            tipo="oportunidad",
            titulo=f"Estrella del día: {top['producto_nombre']}",
            descripcion=f"Es el producto con mayor ingreso (${top['ingresos']:.2f}) "
                        f"con {int(top['total_qty'])} unidades vendidas. "
                        f"Considéralo para destacar en promociones.",
            metrica_valor=f"${top['ingresos']:.0f}",
            metrica_label="Ingreso top",
            accion="Ver menú",
            timestamp=datetime.now().isoformat()
        )]

        # Si hay un segundo producto que genera más del 50% del top, mencionar
        if len(rows) >= 2:
            segundo = rows[1]
            ratio = segundo["ingresos"] / top["ingresos"] if top["ingresos"] > 0 else 0
            if ratio > 0.7:
                insights.append(Insight(
                    tipo="oportunidad",
                    titulo=f"{segundo['producto_nombre']} sigue de cerca",
                    descripcion=f"Con ${segundo['ingresos']:.2f} está al {ratio*100:.0f}% del top. "
                                f"Podrías crear un combo con ambos productos.",
                    accion="Crear combo",
                    timestamp=datetime.now().isoformat()
                ))

        return insights

    # ─── PRODUCTOS ESTANCADOS ────────────────────────────────────────

    def _analizar_productos_estancados(self) -> list[Insight]:
        """Detecta productos disponibles que nadie ha comprado en los últimos 7 días."""
        desde = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M")

        rows = self._db.conn.execute(
            "SELECT p.nombre, p.precio, c.nombre as categoria "
            "FROM productos p "
            "JOIN categorias c ON p.categoria_id = c.id "
            "WHERE p.disponible = 1 AND c.activa = 1 "
            "AND p.id NOT IN ("
            "  SELECT DISTINCT producto_id FROM orden_items oi "
            "  JOIN ordenes o ON oi.orden_id = o.id "
            "  WHERE o.fecha_creacion >= ? AND o.estado != 'cancelled'"
            ") "
            "ORDER BY c.nombre, p.nombre",
            (desde,)
        ).fetchall()

        if not rows:
            return []

        nombres = [r["nombre"] for r in rows[:5]]
        lista_texto = ", ".join(nombres)
        if len(rows) > 5:
            lista_texto += f" y {len(rows)-5} más"

        return [Insight(
            tipo="alerta",
            titulo=f"{len(rows)} producto(s) sin ventas en 7 días",
            descripcion=f"{lista_texto}. Considera crear promociones o verificar su disponibilidad real.",
            metrica_valor=str(len(rows)),
            metrica_label="Productos estancados",
            accion="Ver productos",
            timestamp=datetime.now().isoformat()
        )]

    # ─── HORAS PICO ──────────────────────────────────────────────────

    def _analizar_horas_pico(self) -> list[Insight]:
        """Identifica las horas con más ventas para optimizar personal."""
        hoy = datetime.now().strftime("%Y-%m-%d")

        rows = self._db.conn.execute(
            "SELECT CAST(STRFTIME('%H', fecha_creacion) AS INTEGER) as hora, "
            "COUNT(*) as ordenes, COALESCE(SUM(total), 0) as ventas "
            "FROM ordenes WHERE fecha_creacion LIKE ? AND estado != 'cancelled' "
            "GROUP BY hora ORDER BY ventas DESC LIMIT 3",
            (f"{hoy}%",)
        ).fetchall()

        if not rows:
            return []

        hora_pico = rows[0]
        hora_str = f"{int(hora_pico['hora']):02d}:00"

        horas_lista = ", ".join(f"{int(r['hora']):02d}:00" for r in rows)

        return [Insight(
            tipo="sugerencia",
            titulo=f"Hora pico: {hora_str}",
            descripcion=f"Las horas con más ventas hoy: {horas_lista}. "
                        f"Asegúrate de tener personal suficiente en estos horarios.",
            metrica_valor=f"${hora_pico['ventas']:.0f}",
            metrica_label=f"Ventas en {hora_str}",
            timestamp=datetime.now().isoformat()
        )]

    # ─── TENDENCIA SEMANAL ───────────────────────────────────────────

    def _analizar_tendencia_semanal(self) -> list[Insight]:
        """Analiza la tendencia de ventas de los últimos 7 días."""
        rows = self._db.conn.execute(
            "SELECT DATE(fecha_creacion) as fecha, "
            "COALESCE(SUM(total), 0) as ventas, COUNT(*) as ordenes "
            "FROM ordenes WHERE estado != 'cancelled' "
            "AND fecha_creacion >= DATE('now', '-7 days') "
            "GROUP BY DATE(fecha_creacion) ORDER BY fecha",
        ).fetchall()

        if len(rows) < 2:
            return []

        ventas = [r["ventas"] for r in rows]
        # Tendencia simple: comparar promedio últimos 3 días vs primeros 3 días
        if len(ventas) >= 6:
            prom_primero = sum(ventas[:3]) / 3
            prom_ultimo = sum(ventas[-3:]) / 3

            if prom_primero > 0:
                cambio = ((prom_ultimo - prom_primero) / prom_primero) * 100

                if cambio > 15:
                    return [Insight(
                        tipo="positivo",
                        titulo="Tendencia ascendente esta semana",
                        descripcion=f"Las ventas promediaron ${prom_ultimo:.0f}/día en los últimos 3 días, "
                                    f"un {cambio:.0f}% más que los primeros 3 días (${prom_primero:.0f}/día).",
                        metrica_valor=f"+{cambio:.0f}%",
                        metrica_label="Tendencia semanal",
                        timestamp=datetime.now().isoformat()
                    )]
                elif cambio < -15:
                    return [Insight(
                        tipo="alerta",
                        titulo="Tendencia descendente esta semana",
                        descripcion=f"Las ventas cayeron un {abs(cambio):.0f}% en los últimos 3 días vs los primeros. "
                                    f"Revisa si hay factores externos (clima, competencia, eventos).",
                        metrica_valor=f"{cambio:.0f}%",
                        metrica_label="Tendencia semanal",
                        timestamp=datetime.now().isoformat()
                    )]

        return []

    # ─── TICKET PROMEDIO ─────────────────────────────────────────────

    def _analizar_ticket_promedio(self) -> list[Insight]:
        """Analiza el ticket promedio y sugiere upselling."""
        hoy = datetime.now().strftime("%Y-%m-%d")

        row = self._db.conn.execute(
            "SELECT COUNT(*) as n, COALESCE(SUM(total),0) as total, "
            "COALESCE(AVG(total),0) as promedio "
            "FROM ordenes WHERE fecha_creacion LIKE ? AND estado != 'cancelled'",
            (f"{hoy}%",)
        ).fetchone()

        if row["n"] == 0:
            return []

        # Comparar vs semana pasada
        row_semana = self._db.conn.execute(
            "SELECT COALESCE(AVG(total),0) as promedio "
            "FROM ordenes WHERE estado != 'cancelled' "
            "AND fecha_creacion >= DATE('now', '-14 days') "
            "AND fecha_creacion < DATE('now', '-7 days')"
        ).fetchone()

        insights = []
        promedio_hoy = row["promedio"]

        if row_semana["promedio"] > 0:
            cambio = ((promedio_hoy - row_semana["promedio"]) / row_semana["promedio"]) * 100

            if cambio < -10:
                insights.append(Insight(
                    tipo="sugerencia",
                    titulo="Ticket promedio por debajo de la semana pasada",
                    descripcion=f"Hoy: ${promedio_hoy:.2f} vs Promedio semanal: ${row_semana['promedio']:.2f}. "
                                f"Motiva a los cajeros a sugerir bebidas o postres (upselling).",
                    metrica_valor=f"${promedio_hoy:.2f}",
                    metrica_label="Ticket promedio",
                    accion="Ver combo",
                    timestamp=datetime.now().isoformat()
                ))
        else:
            insights.append(Insight(
                tipo="info",
                titulo=f"Ticket promedio: ${promedio_hoy:.2f}",
                descripcion=f"Con {int(row['n'])} órdenes, el ticket promedio de hoy es ${promedio_hoy:.2f}.",
                metrica_valor=f"${promedio_hoy:.2f}",
                metrica_label="Ticket promedio",
                timestamp=datetime.now().isoformat()
            ))

        return insights

    # ─── TIPOS DE PEDIDO ─────────────────────────────────────────────

    def _analizar_tipos_pedido(self) -> list[Insight]:
        """Analiza la distribución de tipos de pedido (local, takeout, delivery)."""
        hoy = datetime.now().strftime("%Y-%m-%d")

        rows = self._db.conn.execute(
            "SELECT tipo, COUNT(*) as n, COALESCE(SUM(total),0) as total "
            "FROM ordenes WHERE fecha_creacion LIKE ? AND estado != 'cancelled' "
            "GROUP BY tipo ORDER BY total DESC",
            (f"{hoy}%",)
        ).fetchall()

        if not rows:
            return []

        total_general = sum(r["total"] for r in rows)
        if total_general == 0:
            return []

        tipo_nombres = {
            "local": "Comer aquí",
            "takeout": "Para llevar",
            "delivery": "Delivery"
        }

        resultados = []
        for r in rows:
            pct = (r["total"] / total_general) * 100
            nombre = tipo_nombres.get(r["tipo"], r["tipo"])
            resultados.append(f"{nombre}: {pct:.0f}% (${r['total']:.0f})")

        texto = " | ".join(resultados)

        # Si delivery > 50%, sugerir optimización
        delivery_pct = 0
        for r in rows:
            if r["tipo"] == "delivery":
                delivery_pct = (r["total"] / total_general) * 100

        insight = Insight(
            tipo="info",
            titulo="Distribución de ventas por tipo",
            descripcion=texto,
            metrica_valor=f"{len(rows)} tipos",
            metrica_label="Activos hoy",
            timestamp=datetime.now().isoformat()
        )

        if delivery_pct > 50:
            insight.tipo = "sugerencia"
            insight.accion = "Ver domicilios"
            insight.descripcion += ("\n\nEl delivery representa más del 50% de tus ventas. "
                                   "Asegúrate de tener suficientes repartidores disponibles.")

        return [insight]

    # ─── ANÁLISIS DE CLIENTES ────────────────────────────────────────

    def _analizar_clientes_frecuentes(self) -> list[Insight]:
        """Analiza datos del CRM si hay clientes registrados."""
        # Verificar si hay clientes
        total = self._db.conn.execute(
            "SELECT COUNT(*) as cnt FROM clientes"
        ).fetchone()["cnt"]

        if total == 0:
            return []

        insights = []

        # Clientes con cumpleaños próximo (próximos 7 días)
        hoy = datetime.now()
        desde = hoy.strftime("%m-%d")
        en_7 = (hoy + timedelta(days=7)).strftime("%m-%d")

        rows_cumple = self._db.conn.execute(
            "SELECT nombre, telefono, puntos FROM clientes "
            "WHERE fecha_cumpleanos IS NOT NULL AND fecha_cumpleanos != '' "
            "AND SUBSTR(fecha_cumpleanos, 6) >= ? AND SUBSTR(fecha_cumpleanos, 6) <= ? "
            "ORDER BY SUBSTR(fecha_cumpleanos, 6)",
            (desde, en_7)
        ).fetchall()

        if rows_cumple:
            nombres = ", ".join(r["nombre"] for r in rows_cumple[:3])
            if len(rows_cumple) > 3:
                nombres += f" (+{len(rows_cumple)-3} más)"
            insights.append(Insight(
                tipo="oportunidad",
                titulo=f"{len(rows_cumple)} cumpleaños esta semana",
                descripcion=f"{nombres}. Aprovecha para enviar un mensaje de felicitación "
                            f"y ofrecer un descuento especial (+500 puntos de regalo).",
                metrica_valor=str(len(rows_cumple)),
                metrica_label="Cumpleaños",
                accion="Ver clientes",
                timestamp=datetime.now().isoformat()
            ))

        # Clientes con muchos puntos sin canjear
        row_puntos = self._db.conn.execute(
            "SELECT COUNT(*) as cnt FROM clientes WHERE puntos >= 500"
        ).fetchone()

        if row_puntos["cnt"] > 0:
            insights.append(Insight(
                tipo="sugerencia",
                titulo=f"{row_puntos['cnt']} cliente(s) con puntos acumulados",
                descripcion=f"Estos clientes tienen 500+ puntos que pueden canjear. "
                            f"Recuérdales que tienen premios disponibles.",
                metrica_valor=str(row_puntos["cnt"]),
                metrica_label="Con puntos",
                accion="Ver premios",
                timestamp=datetime.now().isoformat()
            ))

        return insights

    # ─── MÉTRICAS RÁPIDAS PARA DASHBOARD ─────────────────────────────

    def get_resumen_rapido(self) -> dict:
        """Retorna un resumen de 1 línea para mostrar en el sidebar o header."""
        hoy = datetime.now().strftime("%Y-%m-%d")

        row = self._db.conn.execute(
            "SELECT COUNT(*) as ordenes, COALESCE(SUM(total),0) as total "
            "FROM ordenes WHERE fecha_creacion LIKE ? AND estado != 'cancelled'",
            (f"{hoy}%",)
        ).fetchone()

        pendientes = self._db.conn.execute(
            "SELECT COUNT(*) as cnt FROM ordenes WHERE estado = 'pending'"
        ).fetchone()["cnt"]

        return {
            "ventas_hoy": row["total"],
            "ordenes_hoy": row["ordenes"],
            "pendientes": pendientes,
        }