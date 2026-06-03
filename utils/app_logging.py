"""Configuración de logging y manejo de excepciones no capturadas."""

import logging
import sys
import os
from datetime import datetime

from config import APP_DATA_DIR


def setup_logging():
    """Configura logging a archivo + consola."""
    log_dir = os.path.join(APP_DATA_DIR, "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(
        log_dir, f"pizzas_pastra_{datetime.now().strftime('%Y%m%d')}.log"
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("pizzas_pastra")


def install_exception_hook(logger):
    """Instala hook global para excepciones no capturadas."""

    def _exception_handler(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logger.critical(
            "Excepción no capturada", exc_info=(exc_type, exc_value, exc_tb)
        )

    sys.excepthook = _exception_handler
