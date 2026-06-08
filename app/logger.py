import logging
import sys

def setup_logger(name: str = "aurora_api") -> logging.Logger:
    """
    Configure et retourne un logger standardisé.
    Les logs apparaissent dans le terminal avec timestamp + niveau + message.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Éviter les doublons si la fonction est appelée plusieurs fois
    if logger.handlers:
        return logger

    # Format : 2026-06-08 14:32:01 | INFO | Message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Affichage dans le terminal
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

# Instance globale réutilisable partout
logger = setup_logger()
