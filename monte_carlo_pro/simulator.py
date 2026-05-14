"""
Simulador Monte Carlo para classificação de jogos
"""

import random
import statistics
from typing import Dict, List, Optional

from config import (
    LOTTERIES,
    MODE_AGRESSIVO_WEIGHT,
    MODE_CONSERVADOR_WEIGHT,
    HIST_SCORE_WEIGHT,
    MC_SCORE_WEIGHT,
    CUSTOS,
    SIMULACOES_MONTE_CARLO,
)
from analyzer import AnalisadorHistorico
from utils.logger import logger


def monte_carlo(
    jogos: List[List[int]],
    tipo: str,
    modo_risco: str,
    analisador: AnalisadorHistorico,
) -> List[Dict]:
    """
    Classifica jogos usando simulação Monte Carlo + análise histórica.

    Args:
        jogos: Lista de jogos a classificar
        tipo: Tipo de loteria
        modo_risco: "Conservador" ou "Agressivo"
        analisador: AnalisadorHistorico com dados

    Returns:
        Lista de dicts com ranking dos 10 melhores jogos
    """
    cfg = LOTTERIES[tipo]
    k = cfg.k
    min_n, max_n = cfg.min, cfg.max

    logger.info(f"Simulando {len(jogos)} jogos com modo {modo_risco}")

    # Gerar sorteios simulados
    if analisador.historico:
        sorteios = [set(s) for s in analisador.historico]
    else:
        # Se sem histórico, gerar simulações aleatórias
        sorteios = [
            set(random.sample(range(min_n, max_n + 1), k))
            for _ in range(SIMULACOES_MONTE_CARLO)
        ]
        logger.warning(
            f"Sem histórico, usando {SIMULACOES_MONTE_CARLO} simulações aleatórias"
        )

    ranking = []
    custo = CUSTOS[tipo]
    premio = cfg.premio

    for jogo in jogos:
        js = set(jogo)

        # Calcular acertos em cada sorteio
        acertos = [len(js & s) for s in sorteios]
        media_acertos = statistics.mean(acertos)
        desvio_acertos = statistics.pstdev(acertos) if len(acertos) > 1 else 0
        max_acertos = max(acertos)

        # Probabilidade de acertar acima da média
        prob_acerto = sum(a >= round(media_acertos) for a in acertos) / len(acertos)

        # Valor esperado
        ev = prob_acerto * premio - custo

        # Score Monte Carlo
        if modo_risco == "Conservador":
            # Prioriza média e penaliza desvio
            _, coef_media, coef_desvio = MODE_CONSERVADOR_WEIGHT
            mc_score = media_acertos * coef_media - desvio_acertos * abs(coef_desvio)
        else:
            # Agressivo: prioriza máximo
            _, coef_media, coef_max = MODE_AGRESSIVO_WEIGHT
            mc_score = media_acertos * coef_media + max_acertos * coef_max

        # Score histórico (0-1 escalado para 0-10)
        hist_score = analisador.score_jogo(jogo)

        # Score final (mix)
        score_final = HIST_SCORE_WEIGHT * hist_score * 10 + MC_SCORE_WEIGHT * mc_score

        ranking.append(
            {
                "jogo": jogo,
                "media": round(media_acertos, 3),
                "desvio": round(desvio_acertos, 3),
                "max": max_acertos,
                "prob": round(prob_acerto, 4),
                "hist_score": round(hist_score, 4),
                "mc_score": round(mc_score, 3),
                "score": round(score_final, 3),
                "ev": round(ev, 2),
                "ev_pct": round((ev / custo * 100) if custo else 0, 1),
            }
        )

    # Ordenar por score (depois por EV como critério de desempate)
    ranking.sort(key=lambda x: (-x["score"], -x["ev"]))

    logger.info(f"Top jogo: {ranking[0]['jogo']} com score {ranking[0]['score']}")

    return ranking[:10]
