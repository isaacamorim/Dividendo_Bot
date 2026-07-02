"""
alerts/console_alert.py — Saída colorida no terminal (colorama).

Exporta os wrappers usados pelo main.py:
  print_cabecalho, print_tabela_acoes, print_detalhe_ativo, print_backtest,
  print_alerta_buy, print_alerta_sell, print_top5, Fore, Style, LINE
"""

from datetime import datetime

from colorama import Fore, Style, init as _colorama_init

_colorama_init()

LINE = "  " + "─" * 100


# ─────────────────────────────────────────────────────────────────────────────
#  Formatação
# ─────────────────────────────────────────────────────────────────────────────

def _moeda(v, largura=8):
    if v is None:
        return f"{'N/D':>{largura}}"
    return f"R${v:>{largura - 2}.2f}"


def _pct(v, largura=6, sinal=False):
    if v is None:
        return f"{'N/D':>{largura}}"
    s = "+" if sinal else ""
    return f"{v:>{s}{largura - 1}.1f}%"


def _cor_sinal(sinal):
    return {"BUY": Fore.GREEN, "SELL": Fore.RED, "HOLD": Fore.YELLOW}.get(sinal, Fore.WHITE)


def _cor_score(score):
    if score >= 8: return Fore.GREEN
    if score >= 6: return Fore.YELLOW
    return Fore.RED


# ─────────────────────────────────────────────────────────────────────────────
#  Cabeçalho
# ─────────────────────────────────────────────────────────────────────────────

def print_cabecalho():
    agora = datetime.now().strftime("%d/%m/%Y %H:%M")
    print()
    print(f"  {Fore.CYAN + Style.BRIGHT}{'═' * 100}{Style.RESET_ALL}")
    print(f"  {Fore.CYAN + Style.BRIGHT}  DIVIDEND BOT B3 — Scanner Fundamentalista  ·  {agora}{Style.RESET_ALL}")
    print(f"  {Fore.CYAN + Style.BRIGHT}{'═' * 100}{Style.RESET_ALL}")


# ─────────────────────────────────────────────────────────────────────────────
#  Tabela do scan
# ─────────────────────────────────────────────────────────────────────────────

def print_tabela_acoes(resultados: list):
    hdr = (f"  {'TICKER':<8} {'NOME':<22} {'PREÇO':>9} {'MA200':>9} {'P.JUSTO':>9} "
           f"{'UPSIDE':>7} {'DY':>6} {'DIV/ANO':>8} {'ROE':>6} {'P/L':>6} {'SCR':>5}  {'SINAL':<5}")
    print()
    print(Fore.WHITE + Style.BRIGHT + hdr + Style.RESET_ALL)
    print(LINE)

    for r in sorted(resultados, key=lambda x: -x["score"]):
        f    = r.get("fundamentos", {})
        tec  = r.get("tecnico", {})
        val  = r.get("valuation", {})
        preco  = f.get("preco")
        ma200  = tec.get("ma_longa")
        upside = val.get("upside")

        ma_cor = Fore.GREEN if (preco is not None and ma200 is not None and preco >= ma200) else Fore.RED
        up_cor = (Fore.WHITE if upside is None
                  else Fore.GREEN if upside >= 10
                  else Fore.YELLOW if upside >= 0 else Fore.RED)
        s_cor  = _cor_sinal(r["sinal"])
        pl     = f.get("pl")
        pl_txt = f"{pl:>6.1f}" if pl is not None else f"{'N/D':>6}"
        up_txt = _pct(upside, 7, sinal=True) if upside is not None else f"{'N/D':>7}"

        print(
            f"  {Fore.WHITE + Style.BRIGHT}{r['ticker']:<8}{Style.RESET_ALL} "
            f"{(f.get('nome') or '')[:22]:<22} "
            f"{_moeda(preco, 9)} "
            f"{ma_cor}{_moeda(ma200, 9)}{Style.RESET_ALL} "
            f"{_moeda(val.get('preco_justo'), 9)} "
            f"{up_cor}{up_txt}{Style.RESET_ALL} "
            f"{_pct(f.get('dy'), 6)} "
            f"{_moeda(val.get('div_estimado'), 8)} "
            f"{_pct(f.get('roe'), 6)} "
            f"{pl_txt} "
            f"{_cor_score(r['score'])}{r['score']:>5.1f}{Style.RESET_ALL}  "
            f"{s_cor + Style.BRIGHT}{r['sinal']:<5}{Style.RESET_ALL}"
        )
    print(LINE)


# ─────────────────────────────────────────────────────────────────────────────
#  Top 5
# ─────────────────────────────────────────────────────────────────────────────

def print_top5(resultados: list):
    top = sorted(resultados, key=lambda x: (0 if x["sinal"] == "BUY" else 1, -x["score"]))[:5]
    print(f"\n  {Fore.CYAN + Style.BRIGHT}TOP 5 OPORTUNIDADES{Style.RESET_ALL}")
    for i, r in enumerate(top, 1):
        f   = r.get("fundamentos", {})
        val = r.get("valuation", {})
        s_cor = _cor_sinal(r["sinal"])
        upside = val.get("upside")
        up_txt = f"{upside:+.0f}%" if upside is not None else "N/D"
        print(f"   {i}. {Style.BRIGHT}{r['ticker']:<8}{Style.RESET_ALL}"
              f" score {_cor_score(r['score'])}{r['score']:.1f}{Style.RESET_ALL}"
              f" · DY {f.get('dy') or 0:.1f}%"
              f" · upside {up_txt}"
              f" · {s_cor}{r['sinal']}{Style.RESET_ALL}"
              f"  ({r.get('setor_perfil', '')})")


# ─────────────────────────────────────────────────────────────────────────────
#  Detalhe de um ativo
# ─────────────────────────────────────────────────────────────────────────────

def print_detalhe_ativo(r: dict):
    f    = r.get("fundamentos", {})
    tec  = r.get("tecnico", {})
    val  = r.get("valuation", {})
    niv  = r.get("niveis_tecnicos", {})
    s_cor = _cor_sinal(r["sinal"])

    print()
    print(f"  {Style.BRIGHT}{r['ticker']} — {f.get('nome') or 'N/D'}{Style.RESET_ALL}"
          f"  ·  {r.get('setor_perfil', '')}  ·  estratégia {r.get('estrategia', '')}")
    print(LINE)

    print(f"  Preço atual : {_moeda(f.get('preco'))}      "
          f"MA50: {_moeda(tec.get('ma_curta'))}      MA200: {_moeda(tec.get('ma_longa'))}      "
          f"Tendência: {'ALTA' if tec.get('tendencia_alta') else 'BAIXA'}")

    pj  = val.get("preco_justo")
    up  = val.get("upside")
    up_txt = f"{up:+.1f}%" if up is not None else "N/D"
    print(f"  Preço justo : {_moeda(pj)}      Upside: {up_txt}      ", end="")
    metodos = val.get("metodos") or {}
    if metodos:
        met_txt = " · ".join(f"{k}={v:.2f}" for k, v in metodos.items())
        print(f"[{val.get('qualidade', '')}: {met_txt}]")
    else:
        print("[sem métodos válidos]")

    print(f"  Dividendos  : DY {_pct(f.get('dy'))}   "
          f"est. {_moeda(val.get('div_estimado'))}/ano   "
          f"{_moeda(val.get('div_mensal'))}/mês   payout {_pct(f.get('payout'))}")

    dv = f.get("divida_ebitda")
    print(f"  Fundamentos : ROE {_pct(f.get('roe'))}   P/L {f.get('pl') if f.get('pl') is not None else 'N/D'}   "
          f"LPA {f.get('lpa') if f.get('lpa') is not None else 'N/D'}   PVP {f.get('pvp') if f.get('pvp') is not None else 'N/D'}   "
          f"Dív/EBITDA {dv if dv is not None else 'N/A'}")

    print(f"  Técnico     : momentum 12m {_pct(tec.get('momentum_12m'), sinal=True)}   "
          f"3m {_pct(tec.get('momentum_3m'), sinal=True)}   beta {tec.get('beta') if tec.get('beta') is not None else 'N/D'}   "
          f"suporte {_moeda(tec.get('suporte'))}   resistência {_moeda(tec.get('resistencia'))}")

    if niv:
        print(f"  Gestão risco: stop sugerido {_moeda(niv.get('stop_sugerido'))}   "
              f"alvo {_moeda(niv.get('alvo_sugerido'))}")

    print(f"  Score       : {_cor_score(r['score'])}{Style.BRIGHT}{r['score']:.1f}{Style.RESET_ALL}"
          f"      Sinal: {s_cor + Style.BRIGHT}{r['sinal']}{Style.RESET_ALL}")

    if r.get("alertas"):
        for a in r["alertas"]:
            print(f"  {Fore.YELLOW}! {a}{Style.RESET_ALL}")
    print(LINE)


# ─────────────────────────────────────────────────────────────────────────────
#  Backtest (resultado individual)
# ─────────────────────────────────────────────────────────────────────────────

def print_backtest(r: dict):
    if "erro" in r:
        print(f"  {Fore.RED}{r['ticker']}: {r['erro']}{Style.RESET_ALL}")
        return
    rc = Fore.GREEN if r["retorno_pct"] >= 0 else Fore.RED
    print()
    print(f"  {Style.BRIGHT}BACKTEST {r['ticker']}{Style.RESET_ALL}  ({r['periodo']}, {r['anos']} anos)")
    print(LINE)
    print(f"  Estratégia : {rc}{r['retorno_pct']:+.1f}%{Style.RESET_ALL}"
          f"  (CAGR {r['cagr_pct']:+.1f}%)   capital final {_moeda(r['capital_final'], 12)}")
    print(f"  Buy & Hold : {r['bh_retorno_pct']:+.1f}%  (CAGR {r['bh_cagr_pct']:+.1f}%)")
    print(f"  Alpha      : {r['alpha_pct']:+.1f}%   Sharpe {r['sharpe']:.2f}   "
          f"MaxDD {r['max_drawdown']:.1f}%   Win {r['win_rate_pct']:.0f}%   trades {r['n_trades']}")
    print(LINE)


# ─────────────────────────────────────────────────────────────────────────────
#  Alertas BUY / SELL
# ─────────────────────────────────────────────────────────────────────────────

def print_alerta_buy(ticker: str, score: float, dy: float, extra: str = ""):
    print(f"  {Fore.GREEN + Style.BRIGHT}BUY  {ticker:<8}{Style.RESET_ALL}"
          f" score {score:.1f} · DY {dy:.1f}%  {extra}")


def print_alerta_sell(ticker: str, motivos: str = ""):
    print(f"  {Fore.RED + Style.BRIGHT}SELL {ticker:<8}{Style.RESET_ALL} {motivos}")
