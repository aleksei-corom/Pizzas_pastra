"""Helper centralizado para acceder a los colores del tema activo.

Permite que los componentes usen tokens del tema sin necesidad de
recibir colores como parámetro ni hardcodear valores.

Uso:
    from views.themes.theme_helper import th
    color = th("primary")
    bg = th("bg_card")
"""

from views.themes.themes import (
    THEME_SAAS, THEME_CLINICA, THEME_FINTECH, THEME_RETAIL,
    THEME_EDUCATIVO, THEME_INDUSTRIAL, THEME_PIZZERIA
)
from views.themes.build_stylesheet import build_stylesheet

AVAILABLE_THEMES = {
    "saas": THEME_SAAS,
    "clinica": THEME_CLINICA,
    "fintech": THEME_FINTECH,
    "retail": THEME_RETAIL,
    "educativo": THEME_EDUCATIVO,
    "industrial": THEME_INDUSTRIAL,
    "pizzeria": THEME_PIZZERIA,
}

# El tema activo
_ACTIVE_THEME = THEME_PIZZERIA
# Cache del stylesheet compilado
_COMPILED_STYLESHEET = build_stylesheet(_ACTIVE_THEME)

def set_active_theme(theme_name: str):
    """Cambia el tema activo y recompila el stylesheet."""
    global _ACTIVE_THEME, _COMPILED_STYLESHEET
    _ACTIVE_THEME = AVAILABLE_THEMES.get(theme_name, THEME_PIZZERIA)
    _COMPILED_STYLESHEET = build_stylesheet(_ACTIVE_THEME)

def apply_theme_to_app(app):
    """Aplica el stylesheet globalmente a la aplicación."""
    app.setStyleSheet(_COMPILED_STYLESHEET)

def th(key: str, default: str = "") -> str:
    """Retorna el valor de un token del tema activo.

    Args:
        key: Nombre del token (ej: 'primary', 'bg_card', 'fg_muted').
        default: Valor por defecto si el token no existe.

    Returns:
        Valor del token como string.
    """
    return _ACTIVE_THEME.get(key, default)


def get_active_theme() -> dict:
    """Retorna una copia del diccionario del tema activo."""
    return dict(_ACTIVE_THEME)


def get_stylesheet() -> str:
    """Retorna el stylesheet compilado del tema activo."""
    return _COMPILED_STYLESHEET


def get_chart_colors() -> list:
    """Retorna una paleta de colores para gráficos derivada del tema.

    Usa colores del tema activo + complementarios para una paleta armónica.
    """
    return [
        th("primary", "#e63946"),
        th("accent", "#f77f00"),
        th("success", "#06d6a0"),
        "#118ab2",
        th("warning", "#ffd166"),
        th("danger", "#ef476f"),
        "#8338ec",
        "#ff6b6b",
        "#4ecdc4",
        "#45b7d1",
    ]


def get_chart_bg() -> str:
    """Retorna el color de fondo para gráficos (bg_card del tema)."""
    return th("bg_card", "#1e293b")
