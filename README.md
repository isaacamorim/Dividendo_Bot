# 📊 Dividend Bot B3

Scanner fundamentalista de ações da B3 com score multi-fator ajustado por setor,
valuation por 3 métodos, sinais BUY/HOLD/SELL, backtest e carteira persistente.

> Python puro. Sem banco de dados, sem servidor — roda direto no terminal.
> Dados via Yahoo Finance (`yfinance`).

---

## Estado atual

Projeto **reconstruído após perda parcial do core** (o OneDrive havia salvo só
4 arquivos). A Fase 0 remontou os 7 módulos que faltavam e validou tudo contra
um relatório de gabarito. Hoje o `python main.py` roda de ponta a ponta com
dados reais da B3.

Histórico técnico honesto:
- **Dívida estrutural de utilities** não gera mais SELL falso — concessões
  reguladas operam alavancadas 3–5x EBITDA por design (teto de dívida agora é
  por setor).
- **DY calculado pela série real de proventos** (últimos 12 meses ÷ preço),
  não pelo campo do Yahoo, que subreportava alguns ativos (VIVT3 saltou de
  2,2% → 7,0% após a correção).

---

## Instalação

```bash
git clone https://github.com/isaacamorim/Dividendo_Bot.git
cd Dividendo_Bot
pip install yfinance pandas numpy requests beautifulsoup4 colorama tabulate
```

Sem configuração adicional.

---

## Uso

### Sem internet (recomendado para testar)
```bash
python main.py --demo                 # Scan completo com dados simulados
python main.py --demo --ticker PETR4  # Detalhe de um ativo
```

### Ao vivo (Yahoo Finance)
```bash
python main.py                        # Scan completo da watchlist
python main.py --ticker ITUB4         # Detalhe de um ativo
python main.py --detalhe              # Scan com detalhe por ativo
python main.py --lista PETR4 VALE3 WEGE3   # Lista customizada
python main.py --monitor --intervalo 60    # Loop contínuo (min)
```

### Backtest
```bash
python main.py --backtest                       # 5 anos (padrão)
python main.py --backtest --backtest-period 2y  # Período customizado
```

### Carteira
```bash
python main.py --carteira                       # Exibe posições e rentabilidade
python main.py --carteira-add PETR4 38.20 100   # Registra compra (ticker preço qtd)
python main.py --carteira-div PETR4 0.85        # Registra dividendo por ação
```

### Relatório HTML
```bash
python main.py --relatorio            # Scan + salva HTML em reports/
python main.py --relatorio-bt         # Inclui backtest (demora mais)
```

---

## Estrutura real do projeto

```
Dividendo_Bot/
├── main.py                        # CLI principal
│
├── config/
│   └── settings.py                # Watchlist, filtros, perfis por setor
│
├── data/
│   ├── fundamentals.py            # DY (série real), ROE, P/L, LPA, PVP via yfinance
│   ├── market_data.py             # Preços, MA50/200, momentum, beta, EPS growth
│   └── demo_data.py               # Dados simulados para uso offline
│
├── analysis/
│   ├── dividend_analysis.py       # Score multi-fator, sinais BUY/SELL/HOLD
│   └── valuation.py               # Preço justo (Graham + DDM + P/L setorial)
│
├── backtest/
│   └── backtester.py              # CAGR, Sharpe, Drawdown, Alpha vs Buy & Hold
│
├── portfolio/
│   └── carteira.py                # Persistência de carteira em JSON
│
├── alerts/
│   └── console_alert.py           # Alertas de compra/venda no terminal
│
└── reports/
    └── html_report.py             # Gerador de relatório HTML
```

`carteira.json` e `reports/*.html` são criados em runtime (ignorados pelo git).

---

## Exemplo de scan ao vivo

Saída real de `python main.py` (02/07/2026, watchlist padrão):

```
TICKER   PREÇO    P.JUSTO  UPSIDE     DY   ROE    P/L   SCR  SINAL
ITUB4    R$42.47  R$45.00   +6.0%   8.1%  21.8%  10.3   8.2  HOLD
VIVT3    R$34.61  R$35.02   +1.2%   7.0%   9.2%  17.6   7.8  HOLD
WEGE3    R$46.26  R$63.74  +37.8%   4.7%  32.5%  30.8   7.6  HOLD
PETR4    R$37.96  R$53.26  +40.3%   7.9%  25.6%   4.7   7.3  BUY
BBDC4    R$18.16  R$18.81   +3.6%   6.7%  13.4%   8.6   7.0  HOLD
CMIG4    R$10.97  R$20.27  +84.8%  11.7%  17.0%   6.4   6.9  BUY
TAEE11   R$40.89  R$34.54  -15.5%   8.0%  20.6%  40.5   6.6  HOLD
VALE3    R$78.24  R$60.88  -22.2%   7.0%   6.8%  22.9   6.2  HOLD
CPLE3    R$15.07  R$13.30  -11.7%   7.1%  10.8%  16.6   5.7  HOLD
ISAE4    R$28.89  R$37.63  +30.3%   6.4%  11.3%   8.1   5.2  HOLD
EGIE3    R$32.36  R$23.97  -25.9%   3.7%  20.2%  14.4   4.8  HOLD
BBAS3    R$20.00  R$19.98   -0.1%   2.7%   9.2%   9.0   4.4  HOLD

BUY: PETR4 (7.3 · DY 7.9%) · CMIG4 (6.9 · DY 11.7%)
```

---

## Como funciona

**Score 0–10 multi-fator**, com pesos diferentes por estratégia:
- **DIVIDENDO** (bancos, energia, telecom): peso maior em DY, ROE, dívida, payout.
- **GROWTH** (industrial/tech): peso maior em EPS growth, ROE, momentum.

**Perfis por setor** — cada setor tem benchmarks próprios de P/L, DY-alvo e
teto de dívida estrutural. Transmissoras (TAEE11, ISAE4, ENGI11) são detectadas
automaticamente e usam P/L mediano de 32 e dívida tolerada de 5,5x EBITDA.

**Preço justo** — média ponderada de três métodos independentes:
1. **Graham** `√(22.5 × LPA × VPA)` — desativado para bancos/FIIs e PVP > 5.
2. **DDM** `DPS / DY_alvo_setor` — desativado acima do cap de yield do setor.
3. **P/L justo** `LPA × P/L_mediano_setor` — desativado com LPA < 0.

Resultado descartado se ficar fora de 30%–250% do preço atual.

**Sinal BUY** exige: fundamentos aprovados + upside ≥ 10% + tendência de alta
(MA50 > MA200). **SELL** é reservado a deterioração real (prejuízo, payout
insustentável, yield trap, ou alavancagem acima do teto setorial *com lucro em
queda*) — nunca dívida alta estrutural sozinha.

---

## Em desenvolvimento

**Fase 1 — dados confiáveis** *(próxima)*
Cache em SQLite (TTL 4h para preços, 24h para fundamentos) e fonte alternativa
`brapi.dev` como primária, com fallback para yfinance. Sanity checks
centralizados. Objetivo: eliminar dependência de um único provedor gratuito.

**Fase 2 — persistência** — snapshots de cada scan e runs de backtest em SQLite;
backtest fundamental (segura por score, não por cruzamento de médias) além do
técnico atual.

**Fase 3 — alertas Telegram** — BUY forte, stop/take da carteira, proximidade
de data ex-dividendo.

**Fase 5 — dashboard web** — visualização do histórico de scans, evolução de
score e carteira ao longo do tempo, em vez do relatório HTML estático atual.

---

## Limitações conhecidas

- **Dados via Yahoo Finance**: gratuito, mas com atrasos e inconsistências de
  escala. O bot trata com sanity checks e fallbacks; a Fase 1 endereça a fonte.
- **Preço justo é estimativa**: Graham e DDM dependem de LPA/PVP reportados, que
  podem refletir resultados extraordinários. Ponto de partida, não verdade.
- **Value traps**: um ativo estatisticamente barato (P/L e P/VP baixos, DY alto)
  pontua bem mesmo quando o desconto reflete risco real de governança. O modelo
  não enxerga isso — use julgamento.
- **Backtest**: usa apenas MA50/200 calculadas no dia da decisão (sem look-ahead),
  mas resultado passado não garante futuro.

---

## Aviso legal

Este projeto é para fins **educacionais e informativos**. Não constitui
recomendação de investimento. Sempre faça sua própria análise antes de investir.
