"""
Análise estatística avançada de histórico de sorteios
"""

import statistics
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple
import math

from config import (
    LOTTERIES,
    SCORE_WEIGHTS,
    PERCENTIL_CASAS,
    MIN_SORTEIOS_ANALISE,
    LOOKBACK_TENDENCIA,
    DESVIO_PARIDADE_THRESHOLD,
    DESVIO_CONSEC_THRESHOLD,
    DESVIO_SOMA_THRESHOLD,
)
from loader import carregar_historico
from utils.logger import logger
from utils.decorators import log_execution_time


class AnalisadorHistorico:
    """
    Realiza análise estatística profunda sobre o histórico de sorteios.

    Métricas calculadas:
      - frequencia: frequência relativa de cada número
      - atraso: sorteios desde a última aparição
      - score_numero: score composto (frequência + recência)
      - coocorrencia: pares que mais aparecem juntos
      - stats_soma: média, desvio, Q1, Q3 das somas
      - stats_pares: distribuição de números pares
      - stats_consec: distribuição de sequências consecutivas
      - stats_decadas: distribuição por faixas de dezenas
      - correlacao_pos: correlação posicional
      - ciclos: análise de repetição entre sorteios
      - casas: análise de casas de dezenas (décadas)
    """

    def __init__(self, tipo: str):
        self.tipo = tipo
        self.cfg = LOTTERIES[tipo]
        self.k = self.cfg.k  # Bolas sorteadas
        self.min_n = self.cfg.min
        self.max_n = self.cfg.max

        self.historico = carregar_historico(tipo)
        self.n = len(self.historico)

        # Atributos inicializados em _calcular()
        self.frequencia: Dict[int, float] = {}
        self.atraso: Dict[int, int] = {}
        self.score_numero: Dict[int, float] = {}
        self.quentes: List[int] = []
        self.frios: List[int] = []
        self.coocorrencia: Dict[Tuple[int, int], int] = {}
        self.coocorrencia_norm: Dict[Tuple[int, int], float] = {}
        self.stats_soma: Dict = {}
        self.stats_pares: Dict = {}
        self.stats_consec: Dict = {}
        self.stats_decadas: Dict = {}
        self.correlacao_pos: Dict = {}
        self.ciclo: Dict = {}
        self.casas: Dict = {}

        self._calcular()
        logger.debug(f"AnalisadorHistorico({tipo}) inicializado com {self.n} sorteios")

    @log_execution_time
    def _calcular(self):
        """Executa todos os cálculos estatísticos"""
        if not self.historico:
            self._inicializar_vazio()
            return

        todos = list(range(self.min_n, self.max_n + 1))

        self._calcular_frequencia(todos)
        self._calcular_atraso(todos)
        self._calcular_score_numero(todos)
        self._calcular_coocorrencia()
        self._calcular_stats_soma()
        self._calcular_stats_pares()
        self._calcular_stats_consecutivos()
        self._calcular_stats_decadas()
        self._calcular_correlacao_posicional()
        self._calcular_ciclos()
        self._calcular_casas()

    def _inicializar_vazio(self):
        """Inicializa atributos com valores padrão quando não há histórico"""
        todos = list(range(self.min_n, self.max_n + 1))
        self.frequencia = {n: 0 for n in todos}
        self.atraso = {n: 0 for n in todos}
        self.score_numero = {n: 0 for n in todos}
        self.coocorrencia = {}
        self.coocorrencia_norm = {}
        self.stats_soma = {}
        self.stats_pares = {}
        self.stats_consec = {}
        self.stats_decadas = {}
        self.correlacao_pos = {}
        self.ciclo = {}
        self.casas = {}
        self.quentes = todos[: self.k]
        self.frios = todos[-self.k :]

    def _calcular_frequencia(self, todos: List[int]):
        """Calcula frequência de cada número"""
        cnt = Counter()
        for sorteio in self.historico:
            cnt.update(sorteio)
        self.frequencia = {n: cnt.get(n, 0) / self.n for n in todos}

    def _calcular_atraso(self, todos: List[int]):
        """Calcula atraso (sorteios sem aparecer) de cada número"""
        self.atraso = {}
        for n in todos:
            for i, sorteio in enumerate(reversed(self.historico)):
                if n in sorteio:
                    self.atraso[n] = i
                    break
            else:
                self.atraso[n] = self.n

    def _calcular_score_numero(self, todos: List[int]):
        """Calcula score composto por número (frequência + recência)"""
        max_freq = max(self.frequencia.values()) or 1
        max_atr = max(self.atraso.values()) or 1

        self.score_numero = {}
        for n in todos:
            freq_norm = self.frequencia[n] / max_freq  # 0-1, alto = quente
            atr_norm = self.atraso[n] / max_atr  # 0-1, alto = muito atrasado

            # 60% frequência histórica + 40% penalidade por atraso
            self.score_numero[n] = round(0.60 * freq_norm + 0.40 * (1 - atr_norm), 5)

        # Classificar em quentes/frios
        scores_ord = sorted(self.score_numero.items(), key=lambda x: -x[1])
        corte = max(1, len(todos) // 3)
        self.quentes = [n for n, _ in scores_ord[:corte]]
        self.frios = [n for n, _ in scores_ord[-corte:]]

    def _calcular_coocorrencia(self):
        """Calcula pares de números que aparecem juntos"""
        self.coocorrencia = defaultdict(int)
        for sorteio in self.historico:
            ss = sorted(sorteio)
            for i in range(len(ss)):
                for j in range(i + 1, len(ss)):
                    self.coocorrencia[(ss[i], ss[j])] += 1

        max_c = max(self.coocorrencia.values()) if self.coocorrencia else 1
        self.coocorrencia_norm = {p: v / max_c for p, v in self.coocorrencia.items()}

    def _calcular_stats_soma(self):
        """Calcula estatísticas da soma dos sorteios"""
        somas = [sum(s) for s in self.historico]
        somas_ord = sorted(somas)

        self.stats_soma = {
            "media": statistics.mean(somas),
            "desvio": statistics.pstdev(somas),
            "min": min(somas),
            "max": max(somas),
            "q1": somas_ord[self.n // 4],
            "q3": somas_ord[3 * self.n // 4],
        }

    def _calcular_stats_pares(self):
        """Calcula estatísticas de paridade (números pares vs ímpares)"""
        pares_l = [sum(n % 2 == 0 for n in s) for s in self.historico]

        self.stats_pares = {
            "media": statistics.mean(pares_l),
            "desvio": statistics.pstdev(pares_l),
            "min": min(pares_l),
            "max": max(pares_l),
        }

    def _calcular_stats_consecutivos(self):
        """Calcula estatísticas de sequências consecutivas"""

        def max_sequencia(sorteio):
            ss = sorted(sorteio)
            m = c = 1
            for i in range(1, len(ss)):
                c = c + 1 if ss[i] == ss[i - 1] + 1 else 1
                m = max(m, c)
            return m

        consec_l = [max_sequencia(s) for s in self.historico]

        self.stats_consec = {
            "media": statistics.mean(consec_l),
            "desvio": statistics.pstdev(consec_l),
            "min": min(consec_l),
            "max": max(consec_l),
        }

    def _calcular_stats_decadas(self):
        """Calcula distribuição por décadas (faixas de 10)"""
        decade_size = 10
        n_decades = (self.max_n // decade_size) + 1

        self.stats_decadas = {}
        for d in range(n_decades):
            lo = (
                d * decade_size + (0 if self.min_n == 0 else 1)
                if d == 0
                else d * decade_size + 1
            )
            hi = lo + decade_size - 1

            vals = [sum(lo <= n <= hi for n in s) for s in self.historico]

            self.stats_decadas[d] = {
                "range": (lo, hi),
                "media": round(statistics.mean(vals), 2),
                "desvio": round(statistics.pstdev(vals), 2),
            }

    def _calcular_correlacao_posicional(self):
        """Calcula valor mais comum para cada posição"""
        self.correlacao_pos = {}
        for pos in range(self.k):
            vals_pos = [sorted(s)[pos] for s in self.historico if len(s) > pos]
            if vals_pos:
                self.correlacao_pos[pos] = {
                    "media": round(statistics.mean(vals_pos), 1),
                    "desvio": round(statistics.pstdev(vals_pos), 1),
                    "moda": Counter(vals_pos).most_common(1)[0][0],
                }

    def _calcular_ciclos(self):
        """Analisa quantos números se repetem entre sorteios consecutivos"""
        repeticoes = []
        for i in range(1, len(self.historico)):
            prev = set(self.historico[i - 1])
            curr = set(self.historico[i])
            repeticoes.append(len(prev & curr))

        self.ciclo = {
            "media_repeticao": (
                round(statistics.mean(repeticoes), 2) if repeticoes else 0
            ),
            "desvio": round(statistics.pstdev(repeticoes), 2) if repeticoes else 0,
        }

    def _calcular_casas(self):
        """Analisa distribuição de casas de dezenas (décadas 00-09, 10-19, etc)"""
        n_decadas = (self.max_n // 10) + 1
        ausencias_dec = Counter()
        n_casas_fora_list = []

        for sorteio in self.historico:
            presentes = set(n // 10 for n in sorteio)
            ausentes = set(range(n_decadas)) - presentes
            ausencias_dec.update(ausentes)
            n_casas_fora_list.append(len(ausentes))

        self.casas = {
            "ausencia_por_decada": {
                d: {
                    "nome": f"{d*10:02d}-{d*10+9:02d}",
                    "total": ausencias_dec.get(d, 0),
                    "pct": (
                        round(ausencias_dec.get(d, 0) / self.n * 100, 1)
                        if self.n
                        else 0
                    ),
                }
                for d in range(n_decadas)
            },
            "n_fora_dist": dict(Counter(n_casas_fora_list)),
            "media_fora": (
                round(statistics.mean(n_casas_fora_list), 2)
                if n_casas_fora_list
                else 0
            ),
            "moda_fora": (
                Counter(n_casas_fora_list).most_common(1)[0][0]
                if n_casas_fora_list
                else 0
            ),
            "max_fora_tipico": (
                sorted(n_casas_fora_list)[int(len(n_casas_fora_list) * PERCENTIL_CASAS / 100)]
                if n_casas_fora_list
                else 2
            ),
        }

    # ==================== Métodos Públicos ====================

    def score_jogo(self, jogo: List[int]) -> float:
        """
        Calcula score de um jogo específico baseado no histórico.

        Avalia:
          - Frequência dos números
          - Soma dentro do intervalo Q1-Q3
          - Paridade próxima à média histórica
          - Co-ocorrência de pares
          - Consecutivos próximos à média
          - Padrão de casas de dezenas

        Args:
            jogo: Lista de números do jogo

        Returns:
            Score entre 0 e 1
        """
        if not self.historico:
            return 0.5

        parcelas = []

        # a) Frequência
        freq_scores = [self.score_numero.get(n, 0) for n in jogo]
        parcelas.append(
            ("freq", statistics.mean(freq_scores), SCORE_WEIGHTS.get("frequencia", 0.35))
        )

        # b) Soma
        if self.stats_soma:
            soma = sum(jogo)
            q1, q3 = self.stats_soma["q1"], self.stats_soma["q3"]
            if q1 <= soma <= q3:
                s_soma = 1.0
            else:
                dist = abs(soma - self.stats_soma["media"]) / (
                    self.stats_soma["desvio"] + 1
                )
                s_soma = max(0.0, 1.0 - dist * DESVIO_SOMA_THRESHOLD)
            parcelas.append(("soma", s_soma, SCORE_WEIGHTS.get("soma", 0.25)))

        # c) Paridade
        if self.stats_pares:
            pares = sum(n % 2 == 0 for n in jogo)
            dist = abs(pares - self.stats_pares["media"]) / (
                self.stats_pares["desvio"] + 1
            )
            parcelas.append(
                (
                    "par",
                    max(0.0, 1.0 - dist * DESVIO_PARIDADE_THRESHOLD),
                    SCORE_WEIGHTS.get("paridade", 0.15),
                )
            )

        # d) Co-ocorrência
        if self.coocorrencia_norm:
            ss = sorted(jogo)
            vals = [
                self.coocorrencia_norm.get((ss[i], ss[j]), 0)
                for i in range(len(ss))
                for j in range(i + 1, len(ss))
            ]
            parcelas.append(
                (
                    "cooc",
                    statistics.mean(vals) if vals else 0,
                    SCORE_WEIGHTS.get("coocorrencia", 0.15),
                )
            )

        # e) Consecutivos
        if self.stats_consec:
            ss = sorted(jogo)
            m = c = 1
            for i in range(1, len(ss)):
                c = c + 1 if ss[i] == ss[i - 1] + 1 else 1
                m = max(m, c)
            dist = abs(m - self.stats_consec["media"]) / (self.stats_consec["desvio"] + 1)
            parcelas.append(
                (
                    "consec",
                    max(0.0, 1.0 - dist * DESVIO_CONSEC_THRESHOLD),
                    SCORE_WEIGHTS.get("consecutivos", 0.10),
                )
            )

        # f) Casas de dezenas
        if self.casas:
            n_decadas = (self.max_n // 10) + 1
            presentes = set(n // 10 for n in jogo)
            casas_fora = n_decadas - len(presentes)
            media_fora = self.casas["media_fora"]
            moda_fora = self.casas["moda_fora"]
            dist = abs(casas_fora - media_fora) / (0.5 + abs(moda_fora - media_fora + 0.1))
            parcelas.append(
                (
                    "casas",
                    max(0.0, 1.0 - dist * 0.15),
                    SCORE_WEIGHTS.get("casas", 0.10),
                )
            )

        total_peso = sum(p for _, _, p in parcelas)
        return sum(v * p for _, v, p in parcelas) / total_peso if total_peso else 0.5

    def numeros_quentes(self, percentual: int = 33) -> List[int]:
        """Retorna os N% números com maior score"""
        s = sorted(self.score_numero.items(), key=lambda x: -x[1])
        n = max(1, len(s) * percentual // 100)
        return [num for num, _ in s[:n]]

    def top_pares(self, n: int = 20) -> List[Tuple[Tuple[int, int], int]]:
        """Retorna os top N pares mais frequentes"""
        return sorted(self.coocorrencia.items(), key=lambda x: -x[1])[:n]

    def resumo(self) -> Optional[Dict]:
        """Retorna resumo da análise"""
        if not self.historico:
            return None

        return {
            "n": self.n,
            "soma_q1": self.stats_soma.get("q1", 0),
            "soma_q3": self.stats_soma.get("q3", 0),
            "soma_media": round(self.stats_soma.get("media", 0), 1),
            "pares_media": round(self.stats_pares.get("media", 0), 1),
            "consec_media": round(self.stats_consec.get("media", 0), 1),
            "rep_media": self.ciclo.get("media_repeticao", 0),
            "top5_quentes": sorted(self.quentes[:5]),
            "top5_frios": sorted(self.frios[:5]),
        }
