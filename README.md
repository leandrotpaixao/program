# 🎲 Monte Carlo PRO — Análise Histórica Avançada de Loterias

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Software profissional para análise estatística avançada de loterias brasileiras com geração de jogos otimizada e simulação Monte Carlo.

## ✨ Funcionalidades Principais

### 📊 Análise Histórica Completa
- **Frequência**: Números mais e menos frequentes
- **Atraso**: Quantos sorteios faltam para cada número
- **Score Composto**: Combinação inteligente de frequência + recência
- **Co-ocorrência**: Pares de números que aparecem juntos
- **Estatísticas**: Soma, paridade, consecutivos, décadas
- **Ciclos**: Repetição entre sorteios consecutivos
- **Casas de Dezenas**: Análise de distribuição por décadas

### 🎯 Geração Inteligente de Jogos
- **Modo Manual**: Selecione dezenas manualmente
- **Modo Automático**: Geração automática com filtros
- **Filtros Avançados**:
  - Paridade (pares vs ímpares)
  - Soma dentro de intervalo histórico (Q1-Q3)
  - Máximo de consecutivos
  - Tendência recente
  - Co-ocorrência de pares
  - Distribuição de casas de dezenas

### 🎲 Simulação Monte Carlo
- Avalia desempenho de jogos vs histórico
- Calcula probabilidade de acerto
- Valor esperado (EV) de cada jogo
- Ranking automático
- Modo Conservador e Agressivo

### 🔄 Carregamento de Dados Flexível
- **CSV**: Arquivo local com histórico
- **XLSX**: Planilha Excel com suporte a múltiplos formatos
- **API CEF**: Download automático da Caixa Econômica Federal

## 🚀 Instalação

### 1. Clone o repositório
```bash
git clone https://github.com/leandrotpaixao/program.git
cd program
```

### 2. Crie ambiente virtual (recomendado)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Instale dependências
```bash
pip install -r requirements.txt
```

## 📖 Como Usar

### Executar Interface Gráfica
```bash
python -m monte_carlo_pro.main
```

### Uso Programático
```python
from monte_carlo_pro.config import GenerationConfig
from monte_carlo_pro.loader import carregar_historico
from monte_carlo_pro.analyzer import AnalisadorHistorico
from monte_carlo_pro.generator import gerar_jogos
from monte_carlo_pro.simulator import monte_carlo

# 1. Carregar histórico
historico = carregar_historico("Lotofácil")

# 2. Analisar
analisador = AnalisadorHistorico("Lotofácil")
print(f"Sorteios: {analisador.n}")
print(f"Top 5 quentes: {analisador.quentes[:5]}")

# 3. Gerar jogos
config = GenerationConfig(
    tipo="Lotofácil",
    qtd=10,
    usar_paridade=True,
    pct_quentes=60,
)
jogos, erro = gerar_jogos(config)

# 4. Simular com Monte Carlo
ranking = monte_carlo(jogos, "Lotofácil", "Conservador", analisador)
for i, jogo_info in enumerate(ranking, 1):
    print(f"{i}. {jogo_info['jogo']} - Score: {jogo_info['score']:.3f}")
```

## 📁 Estrutura do Projeto

```
monte_carlo_pro/
├── config.py              # Configuração centralizada
├── loader.py              # Carregamento de dados
├── analyzer.py            # Análise estatística
├── generator.py           # Geração de jogos
├── simulator.py           # Simulação Monte Carlo
├── validator.py           # Validação de entrada
├── main.py                # Interface Tkinter
├── utils/
│   ├── logger.py          # Sistema de logging
│   ├── cache.py           # Cache thread-safe
│   └── decorators.py      # Decoradores úteis
└── __init__.py
```

## 🔧 Configuração

### Ajustar Pesos de Score
Em `config.py`:
```python
SCORE_WEIGHTS = {
    "frequencia": 0.35,
    "soma": 0.25,
    "paridade": 0.15,
    "coocorrencia": 0.15,
    "consecutivos": 0.10,
}
```

### Ajustar Thresholds
```python
DESVIO_SOMA_THRESHOLD = 0.25
DESVIO_PARIDADE_THRESHOLD = 0.2
DESVIO_CONSEC_THRESHOLD = 0.2
```

## 📊 Loterias Suportadas

| Loteria | Min | Max | K | API |
|---------|-----|-----|---|-----|
| Lotofácil | 1 | 25 | 15 | ✅ |
| Mega-Sena | 1 | 60 | 6 | ✅ |
| Lotomania | 0 | 99 | 20/50 | ✅ |
| +Milionária | 1 | 50 | 6 | ✅ |

## 🧪 Testes

```bash
# Rodar testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=monte_carlo_pro --cov-report=html
```

## 📝 Logs

Logs são salvos em `logs/montecarlo.log` com rotação automática (5MB).

## 🔐 Segurança

- ✅ Cache thread-safe com RLock
- ✅ Rate limiting automático para API
- ✅ Retry com backoff exponencial
- ✅ Validação robusta de entrada
- ✅ Logging estruturado

## 🚧 Roadmap

- [ ] Suporte a mais loterias internacionais
- [ ] Machine Learning para predição
- [ ] Dashboard web com Django
- [ ] Notificações de sorteios
- [ ] Exportação de resultados (PDF, Excel)
- [ ] Histórico de análises

## 📄 Licença

MIT License - veja [LICENSE](LICENSE) para detalhes

## 👤 Autor

**Leandro Paixão**
- GitHub: [@leandrotpaixao](https://github.com/leandrotpaixao)

## 🤝 Contribuições

Contribuições são bem-vindas! Sinta-se livre para abrir issues e pull requests.

---

⭐ Se gostou do projeto, deixe uma estrela!
