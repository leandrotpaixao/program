"""
Configuração centralizada de todas as loterias e parâmetros do sistema
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional


class LotteryType(Enum):
    """Tipos de loteria suportados"""
    LOTOFACIL = "Lotofácil"
    MEGASENA = "Mega-Sena"
    LOTOMANIA = "Lotomania"
    MAISMILIONARIA = "+Milionária"


@dataclass
class LotteryConfig:
    """Configuração de uma loteria específica"""
    name: str
    max: int
    min: int
    k: int  # Bolas sorteadas
    premio: float
    arquivo: str
    api: str
    xlsx_fmt: str
    k_trevo: int = 0
    max_trevo: int = 0
    k_jogo: int = None  # Bolas a marcar (diferente de k para Lotomania)

    def __post_init__(self):
        if self.k_jogo is None:
            self.k_jogo = self.k


# Definições de loterias
LOTTERIES: Dict[str, LotteryConfig] = {
    "Lotofácil": LotteryConfig(
        name="Lotofácil",
        max=25, min=1, k=15,
        premio=1500,
        arquivo="lotofacil.csv",
        api="lotofacil",
        xlsx_fmt="asloterias",
        k_trevo=0,
    ),
    "Mega-Sena": LotteryConfig(
        name="Mega-Sena",
        max=60, min=1, k=6,
        premio=1000,
        arquivo="megasena.csv",
        api="megasena",
        xlsx_fmt="asloterias",
        k_trevo=0,
    ),
    "Lotomania": LotteryConfig(
        name="Lotomania",
        max=99, min=0, k=20,
        premio=1000,
        arquivo="lotomania.csv",
        api="lotomania",
        xlsx_fmt="asloterias",
        k_trevo=0,
        k_jogo=50,  # Jogador marca 50 números
    ),
    "+Milionária": LotteryConfig(
        name="+Milionária",
        max=50, min=1, k=6,
        premio=2000,
        arquivo="milionaria.csv",
        api="maismilionaria",
        xlsx_fmt="milionaria",
        k_trevo=2, max_trevo=6,
    ),
}

# Custos de cada jogo (em reais)
COSTOS: Dict[str, float] = {
    "Lotofácil": 3.00,
    "Mega-Sena": 5.00,
    "Lotomania": 3.00,
    "+Milionária": 6.00,
}

# Pesos para cálculo de score de jogo
SCORE_WEIGHTS: Dict[str, float] = {
    "frequencia": 0.35,      # Frequência histórica do número
    "soma": 0.25,            # Soma dentro do intervalo Q1-Q3
    "paridade": 0.15,        # Distribuição par/ímpar
    "coocorrencia": 0.15,    # Pares que aparecem juntos
    "consecutivos": 0.10,    # Sequências consecutivas
}

# Thresholds para análise
DESVIO_SOMA_THRESHOLD = 0.25
DESVIO_PARIDADE_THRESHOLD = 0.2
DESVIO_CONSEC_THRESHOLD = 0.2
PERCENTIL_CASAS = 97  # Usar percentil 97 para máximo de casas

# Configurações de análise
MIN_SORTEIOS_ANALISE = 10  # Mínimo de sorteios para análise significativa
LOOKBACK_TENDENCIA = 30    # Últimos N sorteios para tendência

# Cache
MAX_CACHED_HISTORIES = 5   # Máximo de históricos em cache
CACHE_TTL_SECONDS = 3600   # TTL do cache em segundos

# API Caixa
API_TIMEOUT = 10
API_RATE_LIMIT = 2  # Requisições por segundo
API_RETRIES = 3
API_BACKOFF = 2.0  # Multiplicador exponencial

# Geração de jogos
MAX_TENTATIVAS_GERACAO = 300  # Tentativas por jogo
MIN_JOGOS = 1
MAX_JOGOS = 1000

# Monte Carlo
SIMULACOES_MONTE_CARLO = 5000  # Se sem histórico
MODE_CONSERVADOR_WEIGHT = ("media", 10, -2)  # (nome, coef_media, coef_desvio)
MODE_AGRESSIVO_WEIGHT = ("media", 7, 1.5)     # (nome, coef_media, coef_max)

# Histórico Score Mix
HIST_SCORE_WEIGHT = 0.50
MC_SCORE_WEIGHT = 0.50


@dataclass
class GenerationConfig:
    """Configuração para geração de jogos"""
    tipo: str
    qtd: int
    modo_geracao: str = "Automático"  # "Manual" ou "Automático"
    modo_risco: str = "Conservador"   # "Conservador" ou "Agressivo"
    
    # Paridade
    usar_paridade: bool = True
    pares_desejados: int = 7
    impares_desejados: int = 8
    
    # Filtros
    usar_tendencia: bool = True
    usar_soma: bool = True
    usar_consecutivos: bool = True
    usar_coocorrencia: bool = False
    max_consecutivos: int = 3
    pct_quentes: int = 60
    
    # Casas de dezenas
    usar_casas: bool = False
    max_casas_fora: int = 2
    
    # Dezenas selecionadas (modo manual)
    dezenas_selecionadas: list = field(default_factory=list)
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Valida configuração. Retorna (válido, mensagem_erro)"""
        
        # Validar tipo de jogo
        if self.tipo not in LOTTERIES:
            return False, f"Tipo de jogo inválido: {self.tipo}"
        
        # Validar quantidade
        if not MIN_JOGOS <= self.qtd <= MAX_JOGOS:
            return False, f"Quantidade deve estar entre {MIN_JOGOS} e {MAX_JOGOS}"
        
        # Validar modo de geração
        if self.modo_geracao not in ["Manual", "Automático"]:
            return False, f"Modo de geração inválido: {self.modo_geracao}"
        
        # Validar modo de risco
        if self.modo_risco not in ["Conservador", "Agressivo"]:
            return False, f"Modo de risco inválido: {self.modo_risco}"
        
        cfg = LOTTERIES[self.tipo]
        k = cfg.k_jogo
        
        # Validar paridade
        if self.usar_paridade:
            total = self.pares_desejados + self.impares_desejados
            if total != k:
                return False, f"Pares ({self.pares_desejados}) + Ímpares ({self.impares_desejados}) devem somar {k}"
            if not (0 <= self.pares_desejados <= k):
                return False, f"Pares deve estar entre 0 e {k}"
        
        # Validar consecutivos
        if self.usar_consecutivos:
            if not (1 <= self.max_consecutivos <= k):
                return False, f"Máximo de consecutivos deve estar entre 1 e {k}"
        
        # Validar percentual de quentes
        if not (0 <= self.pct_quentes <= 100):
            return False, f"% Quentes deve estar entre 0 e 100"
        
        # Validar casas de dezenas
        if self.usar_casas:
            n_decadas = (cfg.max // 10) + 1
            if not (0 <= self.max_casas_fora < n_decadas):
                return False, f"Máximo de casas fora deve estar entre 0 e {n_decadas-1}"
        
        # Validar modo manual
        if self.modo_geracao == "Manual":
            if len(self.dezenas_selecionadas) < k:
                return False, f"Modo manual requer ao menos {k} dezenas selecionadas"
            if len(self.dezenas_selecionadas) > cfg.max:
                return False, f"Máximo {cfg.max} dezenas permitidas"
            for dez in self.dezenas_selecionadas:
                if not (cfg.min <= dez <= cfg.max):
                    return False, f"Dezena {dez} fora do intervalo [{cfg.min}, {cfg.max}]"
        
        return True, None
