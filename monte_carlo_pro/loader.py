"""
Carregamento robusto de histórico de loterias (CSV, XLSX, API)
"""

import csv
import json
import os
from typing import List, Optional, Tuple
import urllib.request
import urllib.error

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

from config import LOTTERIES, API_TIMEOUT, API_RATE_LIMIT, API_RETRIES, API_BACKOFF
from utils.logger import logger
from utils.cache import history_cache, trevos_cache
from utils.decorators import rate_limit, retry


def carregar_historico(tipo: str) -> List[List[int]]:
    """
    Carrega histórico com prioridade: XLSX > CSV > Cache.

    Args:
        tipo: Tipo de loteria (ex: "Lotofácil")

    Returns:
        Lista de sorteios (cada sorteio é uma lista de inteiros)
    """
    # 1. Verificar cache
    cached = history_cache.get(tipo)
    if cached:
        logger.debug(f"Usando cache para {tipo}")
        return cached

    # 2. Tentar CSV na pasta /dados
    caminho_csv = os.path.join("dados", LOTTERIES[tipo].arquivo)
    if os.path.exists(caminho_csv):
        historico = _ler_csv(caminho_csv, tipo)
        if historico:
            history_cache.set(tipo, historico)
            logger.info(f"Carregados {len(historico)} sorteios de {caminho_csv}")
            return historico

    logger.warning(f"Nenhum histórico encontrado para {tipo}")
    return []


def _ler_csv(caminho: str, tipo: str) -> List[List[int]]:
    """
    Lê histórico de arquivo CSV.

    Format esperado:
        Concurso;Data;D1;D2;...;Dn
        1;01/01/2024;01;02;03;...

    Args:
        caminho: Caminho do arquivo CSV
        tipo: Tipo de loteria

    Returns:
        Lista de sorteios
    """
    historico = []
    cfg = LOTTERIES[tipo]
    k = cfg.k

    try:
        with open(caminho, newline="", encoding="utf-8") as f:
            leitor = csv.reader(f, delimiter=";")
            next(leitor, None)  # Pular header

            for linha in leitor:
                try:
                    # Pegar números a partir da coluna 2 (índice 2)
                    nums = [
                        int(x)
                        for x in linha[2:]
                        if x.strip().lstrip("-").isdigit()
                    ]
                    if len(nums) == k:
                        historico.append(sorted(nums))
                except (ValueError, IndexError):
                    continue

        logger.info(f"CSV: Lidos {len(historico)} sorteios de {caminho}")
        return historico

    except Exception as e:
        logger.error(f"Erro ao ler CSV {caminho}: {e}")
        return []


def _ler_xlsx(caminho: str, tipo: str) -> List[List[int]]:
    """
    Lê histórico de arquivo XLSX.

    Formatos suportados:
        "asloterias": header na linha 7, dados a partir de linha 8
        "milionaria": header na linha 1, dados a partir de linha 2

    Args:
        caminho: Caminho do arquivo XLSX
        tipo: Tipo de loteria

    Returns:
        Lista de sorteios
    """
    if not HAS_OPENPYXL:
        raise ImportError("openpyxl não instalado. Execute: pip install openpyxl")

    cfg = LOTTERIES[tipo]
    k = cfg.k
    fmt = cfg.xlsx_fmt
    k_trevo = cfg.k_trevo

    min_row = 8 if fmt == "asloterias" else 2

    historico = []
    trevos = []

    try:
        wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
        ws = wb.active

        for row in ws.iter_rows(min_row=min_row, values_only=True):
            try:
                dezenas = [
                    int(row[c])
                    for c in range(2, 2 + k)
                    if row[c] is not None
                ]
                if len(dezenas) == k:
                    historico.append(sorted(dezenas))

                    # Trevos (se houver)
                    if k_trevo:
                        tv = [
                            int(row[2 + k + t])
                            for t in range(k_trevo)
                            if (2 + k + t) < len(row) and row[2 + k + t] is not None
                        ]
                        trevos.append(tv if len(tv) == k_trevo else [])

            except (TypeError, ValueError, IndexError):
                continue

        wb.close()

        if k_trevo and trevos:
            trevos_cache.set(tipo, trevos)

        logger.info(f"XLSX: Lidos {len(historico)} sorteios de {caminho}")
        return historico

    except Exception as e:
        logger.error(f"Erro ao ler XLSX {caminho}: {e}")
        return []


@retry(max_retries=API_RETRIES, backoff=API_BACKOFF)
@rate_limit(calls_per_second=API_RATE_LIMIT)
def _obter_ultimo_concurso(api: str) -> Optional[int]:
    """
    Obtém número do último concurso da API Caixa.

    Args:
        api: Nome da API (ex: "lotofacil")

    Returns:
        Número do último concurso ou None
    """
    url = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{api}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as r:
            dados = json.loads(r.read().decode())
            return int(dados.get("numero", 0))
    except urllib.error.URLError as e:
        logger.error(f"Erro de conexão na API: {e}")
        raise
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Erro ao decodificar resposta da API: {e}")
        raise


@retry(max_retries=API_RETRIES, backoff=API_BACKOFF)
@rate_limit(calls_per_second=API_RATE_LIMIT)
def _obter_concurso(api: str, concurso_id: int) -> Optional[dict]:
    """
    Obtém dados de um concurso específico.

    Args:
        api: Nome da API
        concurso_id: ID do concurso

    Returns:
        Dict com dados do concurso
    """
    url = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{api}/{concurso_id}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as r:
            return json.loads(r.read().decode())
    except urllib.error.URLError as e:
        logger.error(f"Erro ao obter concurso {concurso_id}: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar concurso {concurso_id}: {e}")
        raise


def baixar_historico_cef(
    tipo: str, progress_cb=None
) -> Tuple[bool, str]:
    """
    Baixa histórico completo da API pública da Caixa.

    Args:
        tipo: Tipo de loteria
        progress_cb: Callback para progresso (atual, total)

    Returns:
        (sucesso, mensagem)
    """
    cfg = LOTTERIES[tipo]
    api = cfg.api
    k = cfg.k

    os.makedirs("dados", exist_ok=True)

    try:
        logger.info(f"Obtendo último concurso para {tipo}...")
        n_ultimo = _obter_ultimo_concurso(api)
        if not n_ultimo:
            return False, "Não foi possível obter o último concurso."

        logger.info(f"Baixando {n_ultimo} concursos...")
        resultados = []

        for c in range(1, n_ultimo + 1):
            try:
                dados = _obter_concurso(api, c)
                dezenas = sorted(int(x) for x in dados.get("listaDezenas", []))
                data = dados.get("dataApuracao", "")
                resultados.append([c, data] + dezenas)

                if progress_cb:
                    progress_cb(c, n_ultimo)

            except Exception:
                continue

        # Salvar em CSV
        caminho = os.path.join("dados", cfg.arquivo)
        with open(caminho, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(["Concurso", "Data"] + [f"D{i+1}" for i in range(k)])
            w.writerows(resultados)

        # Invalidar cache
        history_cache.clear(tipo)

        logger.info(f"Download concluído: {len(resultados)} sorteios salvos")
        return True, f"{len(resultados)} sorteios baixados com sucesso"

    except Exception as e:
        logger.error(f"Erro ao baixar histórico: {e}")
        return False, str(e)
