"""
Validadores para entrada de dados e configurações
"""

from typing import Optional, Tuple
from config import (
    LOTTERIES,
    MIN_JOGOS,
    MAX_JOGOS,
    GenerationConfig,
)
from utils.logger import logger


def validar_entrada_quantidade(qtd_str: str) -> Tuple[bool, Optional[str], Optional[int]]:
    """
    Valida entrada de quantidade de jogos.

    Args:
        qtd_str: String do input

    Returns:
        (válido, mensagem_erro, valor_inteiro)
    """
    try:
        qtd = int(qtd_str.strip())
    except ValueError:
        msg = "Quantidade deve ser um número inteiro"
        logger.error(msg)
        return False, msg, None

    if not MIN_JOGOS <= qtd <= MAX_JOGOS:
        msg = f"Quantidade deve estar entre {MIN_JOGOS} e {MAX_JOGOS}"
        logger.error(msg)
        return False, msg, None

    return True, None, qtd


def validar_tipo_jogo(tipo: str) -> Tuple[bool, Optional[str]]:
    """
    Valida tipo de jogo.

    Args:
        tipo: Nome da loteria

    Returns:
        (válido, mensagem_erro)
    """
    if tipo not in LOTTERIES:
        msg = f"Tipo de jogo inválido: {tipo}. Opções: {', '.join(LOTTERIES.keys())}"
        logger.error(msg)
        return False, msg
    return True, None


def validar_parametros_geracao(config: GenerationConfig) -> Tuple[bool, Optional[str]]:
    """
    Valida todos os parâmetros de geração.

    Args:
        config: GenerationConfig

    Returns:
        (válido, mensagem_erro)
    """
    return config.validate()


def validar_dezenas_selecionadas(
    dezenas: list, tipo: str
) -> Tuple[bool, Optional[str]]:
    """
    Valida dezenas selecionadas no modo manual.

    Args:
        dezenas: Lista de dezenas
        tipo: Tipo de loteria

    Returns:
        (válido, mensagem_erro)
    """
    if tipo not in LOTTERIES:
        return False, f"Tipo de jogo inválido: {tipo}"

    cfg = LOTTERIES[tipo]
    k = cfg.k_jogo

    if len(dezenas) < k:
        msg = f"Selecione ao menos {k} dezenas"
        logger.error(msg)
        return False, msg

    if len(dezenas) > cfg.max:
        msg = f"Máximo {cfg.max} dezenas permitidas"
        logger.error(msg)
        return False, msg

    for dez in dezenas:
        if not isinstance(dez, int) or not (cfg.min <= dez <= cfg.max):
            msg = f"Dezena {dez} inválida. Intervalo: [{cfg.min}, {cfg.max}]"
            logger.error(msg)
            return False, msg

    return True, None


def validar_intervalo_inteiro(
    valor: int, min_val: int, max_val: int, nome: str
) -> Tuple[bool, Optional[str]]:
    """
    Valida se inteiro está dentro de intervalo.

    Args:
        valor: Valor a validar
        min_val: Mínimo permitido
        max_val: Máximo permitido
        nome: Nome do parâmetro (para mensagem)

    Returns:
        (válido, mensagem_erro)
    """
    if not isinstance(valor, int):
        return False, f"{nome} deve ser um número inteiro"

    if not (min_val <= valor <= max_val):
        msg = f"{nome} deve estar entre {min_val} e {max_val}"
        logger.error(msg)
        return False, msg

    return True, None
