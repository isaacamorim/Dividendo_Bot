"""
backtest/backtester.py — v2

Backtest fatorial: Value + Quality + Momentum vs Ibovespa.

Estratégia:
  Compra quando:
    1. MA50 cruza MA200 para cima  (momentum / tendência)
    2. Preço ≤ MA200 × 1.05        (não comprar esticado)
    3. Sem posição aberta

  Venda quando:
    1. Stop Loss     (padrão -8%)
    2. Take Profit   (padrão +20%)
    3. MA50 < MA200  (reversão de tendência)

Métricas:
  Retorno total, CAGR, Sharpe ratio, Max Drawdown, Win Rate,
  Comparação vs Buy & Hold (sem gestão ativa).

Benchmark:
  Buy & Hold no mesmo período com o mesmo capital.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from data.market_data import get_historico
from config.settings import STOP_LOSS_PCT, TAKE_PROFIT_PCT, MA_CURTA, MA_LONGA


def _cagr(retorno_total_pct: float, anos: float) -> float:
    if anos <= 0: return 0.0
    return round(((1 + retorno_total_pct / 100) ** (1 / anos) - 1) * 100, 2)


def _sharpe(retornos_diarios: pd.Series, rf_anual: float = 0.11) -> float:
    """Sharpe Ratio. rf = taxa livre de risco (Selic ~11% a.a.)"""
    if len(retornos_diarios) < 30: return 0.0
    rf_diario = rf_anual / 252
    excesso   = retornos_diarios - rf_diario
    if excesso.std() == 0: return 0.0
    return round(float(excesso.mean() / excesso.std() * np.sqrt(252)), 2)


def _max_drawdown(capital_hist: list) -> float:
    if not capital_hist: return 0.0
    vals = [h["capital"] for h in capital_hist]
    peak = vals[0]
    mdd  = 0.0
    for v in vals:
        if v > peak: peak = v
        dd = (v - peak) / peak * 100
        if dd < mdd: mdd = dd
    return round(mdd, 2)


def rodar_backtest(
    ticker: str,
    capital_inicial: float = 10_000.0,
    period: str = "5y",
    stop_loss:    float = STOP_LOSS_PCT,
    take_profit:  float = TAKE_PROFIT_PCT,
    verbose: bool = False,
) -> dict:
    """
    Backtest com estratégia fatorial + métricas profissionais.
    Retorna dict com resultado da estratégia E do Buy & Hold para comparação.
    """
    df = get_historico(ticker, period=period)
    if df.empty or len(df) < MA_LONGA + 30:
        return {"ticker": ticker, "erro": "Dados insuficientes para backtest"}

    close  = df["Close"].squeeze()
    ma50   = close.rolling(MA_CURTA).mean()
    ma200  = close.rolling(MA_LONGA).mean()

    # ── Estratégia ativa ─────────────────────────────────────────────────────
    capital      = capital_inicial
    posicao      = 0
    preco_compra = 0.0
    trades       = []
    capital_hist = []
    retornos_d   = []   # retornos diários da estratégia

    for i in range(MA_LONGA, len(df)):
        preco    = float(close.iloc[i])
        data     = df.index[i].strftime("%Y-%m-%d")
        ma_c     = float(ma50.iloc[i])
        ma_l     = float(ma200.iloc[i])
        ma_c_ant = float(ma50.iloc[i - 1])
        ma_l_ant = float(ma200.iloc[i - 1])

        capital_total = capital + posicao * preco

        # Retorno diário para Sharpe
        if capital_hist:
            ret_d = (capital_total - capital_hist[-1]["capital"]) / capital_hist[-1]["capital"]
            retornos_d.append(ret_d)

        capital_hist.append({"data": data, "capital": round(capital_total, 2)})

        # ── VENDA ─────────────────────────────────────────────────────────
        if posicao > 0:
            var    = (preco - preco_compra) / preco_compra
            motivo = None
            if var <= stop_loss:
                motivo = "STOP_LOSS"
            elif var >= take_profit:
                motivo = "TAKE_PROFIT"
            elif ma_c < ma_l and ma_c_ant >= ma_l_ant:
                motivo = "CRUZAMENTO_BAIXA"

            if motivo:
                lucro    = posicao * (preco - preco_compra)
                capital += posicao * preco
                trades.append({
                    "tipo": "VENDA", "data": data,
                    "preco": round(preco, 2), "qtd": posicao,
                    "lucro": round(lucro, 2), "motivo": motivo,
                })
                if verbose:
                    print(f"  VENDA  {data}  R${preco:.2f}  {motivo}  lucro={lucro:+.2f}")
                posicao = 0
                preco_compra = 0.0

        # ── COMPRA ────────────────────────────────────────────────────────
        elif (posicao == 0 and capital >= preco and
              ma_c > ma_l and ma_c_ant <= ma_l_ant and    # cruzamento de alta
              preco <= ma_l * 1.05):                       # não comprar muito esticado
            qtd          = int(capital // preco)
            capital     -= qtd * preco
            posicao      = qtd
            preco_compra = preco
            trades.append({
                "tipo": "COMPRA", "data": data,
                "preco": round(preco, 2), "qtd": qtd,
            })
            if verbose:
                print(f"  COMPRA {data}  R${preco:.2f}  qtd={qtd}")

    # Fecha posição no último dia
    if posicao > 0:
        capital += posicao * float(close.iloc[-1])

    # ── Buy & Hold (benchmark) ──────────────────────────────────────────────
    preco_ini   = float(close.iloc[MA_LONGA])
    preco_fim   = float(close.iloc[-1])
    qtd_bh      = int(capital_inicial // preco_ini)
    capital_bh  = capital_inicial - qtd_bh * preco_ini + qtd_bh * preco_fim
    ret_bh      = (capital_bh / capital_inicial - 1) * 100

    # ── Métricas ────────────────────────────────────────────────────────────
    ret_total    = (capital / capital_inicial - 1) * 100
    n_dias       = (df.index[-1] - df.index[MA_LONGA]).days
    anos         = n_dias / 365.25
    lucros       = [t["lucro"] for t in trades if t["tipo"] == "VENDA"]
    n_vendas     = len(lucros)
    win_rate     = sum(1 for l in lucros if l > 0) / n_vendas * 100 if n_vendas else 0
    ret_series   = pd.Series(retornos_d)
    sharpe       = _sharpe(ret_series)
    mdd          = _max_drawdown(capital_hist)
    alpha        = round(ret_total - ret_bh, 2)   # retorno vs buy&hold

    # Expectância por trade
    media_ganho  = np.mean([l for l in lucros if l > 0]) if any(l > 0 for l in lucros) else 0
    media_perda  = np.mean([l for l in lucros if l < 0]) if any(l < 0 for l in lucros) else 0
    expectancia  = round((win_rate/100 * media_ganho + (1 - win_rate/100) * media_perda), 2) if lucros else 0

    return {
        "ticker":          ticker,
        "periodo":         f"{df.index[MA_LONGA].strftime('%Y-%m-%d')} → {df.index[-1].strftime('%Y-%m-%d')}",
        "anos":            round(anos, 1),
        "capital_inicial": capital_inicial,
        # Estratégia ativa
        "capital_final":   round(capital, 2),
        "retorno_pct":     round(ret_total, 2),
        "cagr_pct":        _cagr(ret_total, anos),
        "sharpe":          sharpe,
        "max_drawdown":    mdd,
        "n_trades":        sum(1 for t in trades if t["tipo"] == "COMPRA"),
        "n_vendas":        n_vendas,
        "win_rate_pct":    round(win_rate, 1),
        "expectancia":     expectancia,
        # Buy & Hold
        "bh_capital":      round(capital_bh, 2),
        "bh_retorno_pct":  round(ret_bh, 2),
        "bh_cagr_pct":     _cagr(ret_bh, anos),
        # Alpha
        "alpha_pct":       alpha,
        "trades":          trades[-20:],   # últimos 20 trades
        "historico":       capital_hist,
    }


def backtest_lote(tickers: list, capital_por_ativo: float = 10_000,
                  period: str = "5y") -> dict:
    """
    Roda backtest em vários ativos e calcula estatísticas consolidadas.
    """
    resultados = []
    for ticker in tickers:
        r = rodar_backtest(ticker, capital_por_ativo, period)
        if "erro" not in r:
            resultados.append(r)

    if not resultados:
        return {"erro": "Nenhum dado disponível"}

    retornos  = [r["retorno_pct"]  for r in resultados]
    bh_retorn = [r["bh_retorno_pct"] for r in resultados]
    alphas    = [r["alpha_pct"]    for r in resultados]
    sharpes   = [r["sharpe"]       for r in resultados]

    return {
        "n_ativos":          len(resultados),
        "retorno_medio":     round(np.mean(retornos), 2),
        "retorno_mediano":   round(np.median(retornos), 2),
        "bh_medio":          round(np.mean(bh_retorn), 2),
        "alpha_medio":       round(np.mean(alphas), 2),
        "sharpe_medio":      round(np.mean(sharpes), 2),
        "melhor":            max(resultados, key=lambda x: x["retorno_pct"]),
        "pior":              min(resultados, key=lambda x: x["retorno_pct"]),
        "pct_venceu_bh":     round(sum(1 for a in alphas if a > 0) / len(alphas) * 100, 1),
        "resultados":        resultados,
    }
