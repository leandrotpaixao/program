"""
Sistema de logging profissional com rotação de arquivos
"""

import logging
from logging.handlers import RotatingFileHandler
import os


def setup_logger(name: str = "montecarlo", log_file: str = "montecarlo.log") -> logging.Logger:
    """
    Configura logger com handlers para arquivo e console.

    Args:
        name: Nome do logger
        log_file: Caminho do arquivo de log

    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Criar diretório se não existir
    os.makedirs("logs", exist_ok=True)
    log_path = os.path.join("logs", log_file)

    # Handler para arquivo com rotação (5MB, 3 backups)
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
    )
    file_handler.setLevel(logging.DEBUG)

    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Formato
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Logger global
logger = setup_logger()
