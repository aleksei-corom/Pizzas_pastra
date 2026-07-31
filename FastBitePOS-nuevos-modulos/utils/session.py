'''Gestor de sesión del usuario actual — CON NUEVOS MÓDULOS.

Reemplaza completamente a utils/session.py.

Cambios vs original:
- Se agregaron 'clientes', 'costos', 'asistente' a ROLE_ACCESS["admin"]
- Se agregó 'clientes' a ROLE_ACCESS["cajero"]
'''

from database.models import Usuario


# Módulos accesibles por rol
ROLE_ACCESS = {
    "admin": [
        "dashboard", "pos", "menu", "ordenes", "domicilios", "cocina",
        "reportes", "contabilidad", "ajustes", "usuarios",
        "clientes", "costos", "asistente",  # ← NUEVOS MÓDULOS
    ],
    "cajero": [
        "pos", "ordenes", "domicilios", "cocina",
        "clientes",  # ← CRM básico para cajeros
    ],
}


class Session:
    """Singleton thread-safe que mantiene la sesión del usuario logueado y sus preferencias.

    Las preferencias se cargan desde la DB al iniciar sesión y se persisten
    automáticamente al cambiarlas. Esto permite que cada usuario tenga su
    propia configuración (ej: impresora predeterminada).
    """

    _instance = None
    _lock = __import__("threading").Lock()

    def __init__(self):
        self._current_user: Usuario | None = None
        self._preferences: dict[str, str] = {}

    @classmethod
    def get(cls) -> "Session":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    def login(self, user: Usuario):
        """Establece el usuario de la sesión y carga sus preferencias."""
        self._current_user = user
        self._load_preferences()

    def logout(self):
        """Cierra la sesión actual y limpia preferencias."""
        self._current_user = None
        self._preferences.clear()

    # ─── Preferencias por usuario ───

    def _load_preferences(self):
        """Carga todas las preferencias del usuario desde la DB."""
        if not self._current_user:
            return
        try:
            from database.config_service import ConfigService
            cfg_svc = ConfigService()
            prefs = cfg_svc.get_all_user_preferences(self._current_user.id)
            self._preferences = prefs
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error cargando preferencias: {e}")
            self._preferences = {}

    def _save_preference(self, key: str, value: str):
        """Persiste una preferencia a la DB."""
        if not self._current_user:
            return
        try:
            from database.config_service import ConfigService
            cfg_svc = ConfigService()
            cfg_svc.set_user_preference(self._current_user.id, key, value)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error guardando preferencia '{key}': {e}")

    def get_preference(self, key: str, default: str | None = None) -> str | None:
        """Obtiene una preferencia del usuario actual.

        Args:
            key: Nombre de la preferencia.
            default: Valor por defecto si no existe.

        Returns:
            El valor de la preferencia o el default si no está configurada.
        """
        return self._preferences.get(key, default)

    def set_preference(self, key: str, value: str):
        """Establece una preferencia del usuario y la persiste en DB."""
        self._preferences[key] = value
        self._save_preference(key, value)

    # ─── Propiedades de usuario ───

    @property
    def user(self) -> Usuario | None:
        return self._current_user

    @property
    def is_logged_in(self) -> bool:
        return self._current_user is not None

    def is_admin(self) -> bool:
        return self._current_user is not None and self._current_user.rol == "admin"

    def has_access(self, module_name: str) -> bool:
        """Verifica si el usuario actual tiene acceso a un módulo."""
        if self._current_user is None:
            return False
        allowed = ROLE_ACCESS.get(self._current_user.rol, [])
        return module_name in allowed

    def get_allowed_modules(self) -> list[str]:
        """Retorna la lista de módulos accesibles para el usuario actual."""
        if self._current_user is None:
            return []
        return ROLE_ACCESS.get(self._current_user.rol, [])
