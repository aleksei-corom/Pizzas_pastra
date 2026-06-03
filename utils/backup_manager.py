"""Gestor de copias de seguridad automáticas de la base de datos."""

import os
import shutil
import logging
import glob
from datetime import datetime

from config import DB_PATH, APP_DATA_DIR

logger = logging.getLogger("pizzas_pastra.backup")


def run_daily_backup():
    """Crea un backup de la DB si no se ha hecho uno hoy. Mantiene los últimos 7."""
    if not os.path.exists(DB_PATH):
        logger.info("No hay base de datos para respaldar todavía.")
        return

    backup_dir = os.path.join(APP_DATA_DIR, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    today_str = datetime.now().strftime("%Y%m%d")
    backup_file = os.path.join(backup_dir, f"db_backup_{today_str}.db")

    if os.path.exists(backup_file):
        logger.debug("Ya existe un backup de la DB para el día de hoy.")
        return

    try:
        shutil.copy2(DB_PATH, backup_file)
        logger.info(f"Backup creado exitosamente: {backup_file}")
        _cleanup_old_backups(backup_dir, keep_last=7)
    except Exception as e:
        logger.error(f"Error al crear backup de la DB: {e}", exc_info=True)


def _cleanup_old_backups(backup_dir: str, keep_last: int = 7):
    """Elimina los backups antiguos, manteniendo solo los últimos 'keep_last'."""
    try:
        backups = glob.glob(os.path.join(backup_dir, "db_backup_*.db"))
        # Ordenar por fecha de modificación (los más nuevos al final)
        backups.sort(key=os.path.getmtime)

        if len(backups) > keep_last:
            to_delete = backups[:-keep_last]
            for file_path in to_delete:
                os.remove(file_path)
                logger.debug(f"Backup antiguo eliminado: {file_path}")
    except Exception as e:
        logger.error(f"Error al limpiar backups antiguos: {e}")
