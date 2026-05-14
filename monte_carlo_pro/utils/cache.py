"""
Sistema de cache thread-safe com limite de tamanho
"""

from collections import OrderedDict
from threading import RLock
from typing import Any, List, Optional


class LimitedCache:
    """
    Cache com limite de tamanho FIFO (First In First Out).
    Thread-safe com RLock.
    """

    def __init__(self, max_size: int = 5):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.lock = RLock()

    def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache"""
        with self.lock:
            if key in self.cache:
                # Mover para o final (mais recente)
                self.cache.move_to_end(key)
                return self.cache[key]
            return None

    def set(self, key: str, value: Any):
        """Armazena valor no cache"""
        with self.lock:
            if key in self.cache:
                self.cache.move_to_end(key)
            self.cache[key] = value

            # Remove mais antigo se exceder limite
            if len(self.cache) > self.max_size:
                oldest = next(iter(self.cache))
                del self.cache[oldest]

    def clear(self, key: str = None):
        """Limpa cache específico ou tudo"""
        with self.lock:
            if key and key in self.cache:
                del self.cache[key]
            elif key is None:
                self.cache.clear()

    def __len__(self) -> int:
        with self.lock:
            return len(self.cache)


class TrevosCache:
    """
    Cache especializado para dados de trevos da +Milionária.
    """

    def __init__(self):
        self.data: dict = {}
        self.lock = RLock()

    def get(self, tipo: str) -> Optional[List[List[int]]]:
        """Obtém trevos para um tipo de loteria"""
        with self.lock:
            return self.data.get(tipo)

    def set(self, tipo: str, trevos: List[List[int]]):
        """Armazena trevos"""
        with self.lock:
            self.data[tipo] = trevos

    def clear(self, tipo: str = None):
        """Limpa trevos específicos ou tudo"""
        with self.lock:
            if tipo and tipo in self.data:
                del self.data[tipo]
            elif tipo is None:
                self.data.clear()


# Instâncias globais
history_cache = LimitedCache(max_size=5)
trevos_cache = TrevosCache()
