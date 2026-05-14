"""
Decoradores reutilizáveis para logging, retry e rate limiting
"""

import time
import functools
from typing import Callable, Any

from utils.logger import logger


def log_execution_time(func: Callable) -> Callable:
    """
    Decorator que loga tempo de execução de uma função.

    Args:
        func: Função a decorar

    Returns:
        Função decorada
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(f"{func.__name__} levou {elapsed:.3f}s")
        return result

    return wrapper


def retry(max_retries: int = 3, backoff: float = 2.0) -> Callable:
    """
    Decorator que tenta executar função com retry e backoff exponencial.

    Args:
        max_retries: Número máximo de tentativas
        backoff: Multiplicador exponencial para delay

    Returns:
        Função decorada
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt >= max_retries:
                        logger.error(f"{func.__name__} falhou após {max_retries} tentativas: {e}")
                        raise

                    delay = backoff ** (attempt - 1)
                    logger.warning(
                        f"{func.__name__} tentativa {attempt} falhou. "
                        f"Aguardando {delay:.1f}s..."
                    )
                    time.sleep(delay)

        return wrapper

    return decorator


def rate_limit(calls_per_second: float = 1) -> Callable:
    """
    Decorator que limita chamadas por segundo.

    Args:
        calls_per_second: Máximo de chamadas por segundo

    Returns:
        Função decorada
    """
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            wait = min_interval - elapsed
            if wait > 0:
                time.sleep(wait)
            result = func(*args, **kwargs)
            last_called[0] = time.time()
            return result

        return wrapper

    return decorator
