"""
Gerador de jogos com filtros estatísticos avançados
"""

import random
import statistics
from typing import List, Optional, Tuple

from config import LOTTERIES, GenerationConfig, LOOKBACK_TENDENCIA, MAX_TENTATIVAS_GERACAO
from analyzer import AnalisadorHistorico
from utils.logger import logger


def gerar_jogos(
    config: GenerationConfig,
) -> Tuple[Optional[List[List[int]]], Optional[str]]:
    """
    Gera jogos aplicando filtros estatísticos.

    Args:
        config: GenerationConfig com parâmetros da geração

    Returns:
        (lista_de_jogos, mensagem_erro) ou (None, erro)
    """
    # Validar configuração
    válido, erro = config.validate()
    if not válido:
        logger.error(f"Erro na configuração: {erro}")
        return None, erro

    cfg = LOTTERIES[config.tipo]
    k = cfg.k_jogo
    min_n, max_n = cfg.min, cfg.max

    # Carregar analisador
    analisador = AnalisadorHistorico(config.tipo)

    # Definir base de números
    if config.modo_geracao == "Manual":
        base = config.dezenas_selecionadas
        if len(base) < k:
            erro = f"Selecione ao menos {k} dezenas no modo Manual."
            logger.error(erro)
            return None, erro
    else:
        base = list(range(min_n, max_n + 1))

    # Separar números quentes
    quentes = [n for n in analisador.quentes if n in base]
    outros = [n for n in base if n not in quentes]

    jogos = []
    tentativas = 0
    limite_tentativas = config.qtd * MAX_TENTATIVAS_GERACAO

    logger.info(
        f"Gerando {config.qtd} jogos para {config.tipo} "
        f"(modo={config.modo_geracao}, risco={config.modo_risco})"
    )

    while len(jogos) < config.qtd and tentativas < limite_tentativas:
        tentativas += 1

        # Gerar jogo
        if (
            analisador.historico
            and config.modo_geracao == "Automático"
            and quentes
        ):
            # Mix de quentes + outros
            n_q = min(
                len(quentes),
                max(0, int(k * config.pct_quentes / 100)),
            )
            n_o = k - n_q

            if n_o > len(outros):
                jogo = sorted(random.sample(base, k))
            else:
                jogo = sorted(
                    random.sample(quentes, n_q) + random.sample(outros, n_o)
                )
        else:
            jogo = sorted(random.sample(base, k))

        # Validar e adicionar
        if _validar_jogo(jogo, config, analisador) and jogo not in jogos:
            jogos.append(jogo)

    if not jogos:
        erro = "Nenhum jogo passou nos filtros. Relaxe os critérios."
        logger.warning(erro)
        return None, erro

    logger.info(f"Gerados {len(jogos)} jogos em {tentativas} tentativas")
    return jogos, None


def _validar_jogo(
    jogo: List[int],
    config: GenerationConfig,
    analisador: AnalisadorHistorico,
) -> bool:
    """
    Valida um jogo aplicando todos os filtros.

    Args:
        jogo: Lista de números do jogo
        config: Configuração com filtros
        analisador: Analisador com dados históricos

    Returns:
        True se jogo passa em todos os filtros
    """
    cfg = LOTTERIES[config.tipo]

    # 1. Paridade fixa
    if config.usar_paridade:
        pares = sum(n % 2 == 0 for n in jogo)
        if pares != config.pares_desejados:
            return False

    # 2. Soma no intervalo Q1-Q3
    if config.usar_soma and analisador.stats_soma:
        soma = sum(jogo)
        q1 = analisador.stats_soma["q1"]
        q3 = analisador.stats_soma["q3"]
        if not (q1 <= soma <= q3):
            return False

    # 3. Consecutivos máximos
    if config.usar_consecutivos:
        max_seq = _calcular_max_sequencia(jogo)
        if max_seq > config.max_consecutivos:
            return False

    # 4. Tendência recente de paridade
    if config.usar_tendencia and len(analisador.historico) >= 20:
        rec = analisador.historico[-LOOKBACK_TENDENCIA:]
        par_r = [sum(n % 2 == 0 for n in s) for s in rec]
        mp = statistics.mean(par_r)
        dp = statistics.pstdev(par_r)
        p = sum(n % 2 == 0 for n in jogo)
        if not (mp - 1.5 * dp <= p <= mp + 1.5 * dp):
            return False

    # 5. Casas de dezenas ausentes
    if config.usar_casas:
        n_decadas = (cfg.max // 10) + 1
        decadas_presentes = set(n // 10 for n in jogo)
        casas_fora = n_decadas - len(decadas_presentes)
        if casas_fora > config.max_casas_fora:
            return False

    # 6. Co-ocorrência (opcional)
    if config.usar_coocorrencia and analisador.coocorrencia_norm:
        ss = sorted(jogo)
        vals = [
            analisador.coocorrencia_norm.get((ss[i], ss[j]), 0)
            for i in range(len(ss))
            for j in range(i + 1, len(ss))
        ]
        if vals:
            media_cooc = statistics.mean(vals)
            if media_cooc < 0.3:  # Threshold mínimo
                return False

    return True


def _calcular_max_sequencia(jogo: List[int]) -> int:
    """
    Calcula a máxima sequência de números consecutivos.

    Args:
        jogo: Lista de números

    Returns:
        Comprimento da maior sequência consecutiva
    """
    ss = sorted(jogo)
    max_seq = 1
    seq_atual = 1

    for i in range(1, len(ss)):
        if ss[i] == ss[i - 1] + 1:
            seq_atual += 1
            max_seq = max(max_seq, seq_atual)
        else:
            seq_atual = 1

    return max_seq
