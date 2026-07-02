#!/usr/bin/env python3
"""
main.py — Dividend Bot B3

Uso:
  python main.py                          → Scan completo watchlist
  python main.py --ticker ITUB4          → Detalhe de um ativo
  python main.py --backtest              → Backtest com métricas profissionais
  python main.py --monitor               → Loop contínuo
  python main.py --relatorio             → Scan + salva HTML
  python main.py --carteira              → Exibe sua carteira
  python main.py --carteira-add PETR4 38.20 100          → Registra compra
  python main.py --carteira-div PETR4 0.85               → Registra dividendo
  python main.py --demo                  → Modo offline (dados simulados)
"""

import argparse, time, sys, os, logging, warnings
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
logging.getLogger("peewee").setLevel(logging.CRITICAL)
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(__file__))

from config.settings          import WATCHLIST_ACOES, SCORE_MIN_ALERTA
from data.market_data         import get_preco_atual, get_dados_tecnicos_completos
from data.fundamentals        import get_fundamentos
from data.demo_data           import get_demo_fundamentos, get_demo_tecnico, DEMO_BACKTEST, DEMO_ACOES
from analysis.dividend_analysis import analisar_ativo
from backtest.backtester      import rodar_backtest, backtest_lote
from portfolio.carteira       import Carteira
from reports.html_report      import salvar_relatorio
from alerts.console_alert     import (
    print_cabecalho, print_tabela_acoes, print_detalhe_ativo,
    print_backtest, print_alerta_buy, print_alerta_sell, print_top5,
    Fore, Style, LINE,
)

DEMO_MODE = False


# ─────────────────────────────────────────────────────────────────────────────
#  Analisar ativo
# ─────────────────────────────────────────────────────────────────────────────

def analisar(ticker: str, detalhe: bool = False, preco_compra: float = 0) -> dict:
    ticker_sa    = ticker if ticker.endswith(".SA") else ticker + ".SA"
    ticker_limpo = ticker.upper().replace(".SA", "")
    print(f"  {Fore.CYAN}Buscando {ticker_limpo}...{Style.RESET_ALL}", end="\r")

    if DEMO_MODE:
        fund = get_demo_fundamentos(ticker_sa)
        tec  = get_demo_tecnico(ticker_sa)
    else:
        fund = get_fundamentos(ticker_sa)
        tec  = get_dados_tecnicos_completos(ticker_sa)
        if not fund.get("preco"):
            fund["preco"] = get_preco_atual(ticker_sa)
        for campo in ("eps_growth", "beta", "momentum_12m", "momentum_3m"):
            if tec.get(campo) is not None and fund.get(campo) is None:
                fund[campo] = tec[campo]

    fund["ticker"] = ticker_limpo
    if fund.get("delisted"):
        return None

    resultado = analisar_ativo(fund, tec, preco_compra=preco_compra)
    if detalhe:
        print_detalhe_ativo(resultado)
    return resultado


# ─────────────────────────────────────────────────────────────────────────────
#  Scan da watchlist
# ─────────────────────────────────────────────────────────────────────────────

def scan_watchlist(watchlist: list = None, detalhe: bool = False) -> list:
    if watchlist is None:
        watchlist = ([t + ".SA" for t in DEMO_ACOES.keys()]
                     if DEMO_MODE else WATCHLIST_ACOES)

    print_cabecalho()
    print(f"\n  Escaneando {len(watchlist)} ativos...\n")

    resultados, compras, vendas = [], [], []

    for ticker in watchlist:
        try:
            r = analisar(ticker, detalhe=detalhe)
            if r is None: continue
            resultados.append(r)
            if r["sinal"] == "BUY"  and r["score"] >= SCORE_MIN_ALERTA: compras.append(r)
            elif r["sinal"] == "SELL": vendas.append(r)
        except Exception as e:
            print(f"  {Fore.RED}Erro em {ticker}: {e}{Style.RESET_ALL}")
        time.sleep(0.5)

    if resultados:
        print_tabela_acoes(resultados)
        print_top5(resultados)

    if compras:
        print(f"\n  {Fore.GREEN + Style.BRIGHT}{'─'*20} SINAIS DE COMPRA {'─'*20}{Style.RESET_ALL}")
        for r in sorted(compras, key=lambda x: -x["score"]):
            f = r["fundamentos"]
            print_alerta_buy(r["ticker"], r["score"], f.get("dy") or 0,
                             f"ROE={f.get('roe') or 0:.1f}%  P/L={f.get('pl') or 0:.1f}")

    if vendas:
        print(f"\n  {Fore.RED + Style.BRIGHT}{'─'*20} SINAIS DE VENDA {'─'*22}{Style.RESET_ALL}")
        for r in vendas:
            motivos = " | ".join(r["alertas"]) if r["alertas"] else "Fundamentos deteriorados"
            print_alerta_sell(r["ticker"], motivos)

    print(f"\n  {Fore.CYAN}Scan finalizado. {len(resultados)} ativos analisados.{Style.RESET_ALL}\n")
    return resultados


# ─────────────────────────────────────────────────────────────────────────────
#  Backtest
# ─────────────────────────────────────────────────────────────────────────────

def cmd_backtest(watchlist: list = None, period: str = "5y"):
    if watchlist is None:
        watchlist = WATCHLIST_ACOES[:8] if not DEMO_MODE else list(DEMO_ACOES.keys())[:6]

    print_cabecalho()
    print(f"\n  Rodando backtest ({period}) em {len(watchlist)} ativos...\n")

    if DEMO_MODE:
        # Exibe resultados demo
        hdr = f"  {'TICKER':<10} {'RETORNO':>8} {'CAPITAL FINAL':>15} {'TRADES':>7} {'WIN%':>7}"
        print(Fore.WHITE + Style.BRIGHT + hdr)
        print(LINE)
        for ticker in watchlist:
            t = ticker.upper().replace(".SA", "")
            r = DEMO_BACKTEST.get(t)
            if not r:
                continue
            cor = Fore.GREEN if r["retorno_pct"] >= 0 else Fore.RED
            print(f"  {t:<10} {cor}{r['retorno_pct']:>+7.2f}%{Style.RESET_ALL}"
                  f"  R$ {r['capital_final']:>12,.2f}  {r['n_trades']:>6}  {r['win_rate_pct']:>6.1f}%")
        print(LINE + "\n")
        return

    # Backtest real
    tickers_sa = [t if t.endswith(".SA") else t + ".SA" for t in watchlist]
    resultado  = backtest_lote(tickers_sa, capital_por_ativo=10_000, period=period)

    if "erro" in resultado:
        print(f"  {Fore.RED}Erro: {resultado['erro']}{Style.RESET_ALL}")
        return

    # Tabela individual
    hdr = (f"  {'TICKER':<10} {'PERÍODO':<12} {'RETORNO':>8} {'CAGR':>7} "
           f"{'B&H':>8} {'ALPHA':>8} {'SHARPE':>7} {'DRAWDOWN':>9} {'WIN%':>6} {'TRADES':>7}")
    print(Fore.WHITE + Style.BRIGHT + hdr)
    print(LINE)

    for r in sorted(resultado["resultados"], key=lambda x: -x["retorno_pct"]):
        rc = Fore.GREEN if r["retorno_pct"] >= 0 else Fore.RED
        ac = Fore.GREEN if r["alpha_pct"]   >= 0 else Fore.RED
        print(
            f"  {r['ticker'].replace('.SA',''):<10}"
            f"  {r['anos']:.1f}a{'':<8}"
            f"  {rc}{r['retorno_pct']:>+7.1f}%{Style.RESET_ALL}"
            f"  {r['cagr_pct']:>+6.1f}%"
            f"  {r['bh_retorno_pct']:>+7.1f}%"
            f"  {ac}{r['alpha_pct']:>+7.1f}%{Style.RESET_ALL}"
            f"  {r['sharpe']:>6.2f}"
            f"  {r['max_drawdown']:>8.1f}%"
            f"  {r['win_rate_pct']:>5.0f}%"
            f"  {r['n_trades']:>6}"
        )

    print(LINE)
    ac_total = Fore.GREEN if resultado["alpha_medio"] >= 0 else Fore.RED
    print(f"\n  Consolidado: retorno médio {resultado['retorno_medio']:+.1f}%"
          f"  B&H médio {resultado['bh_medio']:+.1f}%"
          f"  {ac_total}alpha {resultado['alpha_medio']:+.1f}%{Style.RESET_ALL}"
          f"  Sharpe {resultado['sharpe_medio']:.2f}"
          f"  {resultado['pct_venceu_bh']:.0f}% dos ativos venceu Buy & Hold\n")


# ─────────────────────────────────────────────────────────────────────────────
#  Carteira
# ─────────────────────────────────────────────────────────────────────────────

def cmd_carteira_exibir():
    c   = Carteira()
    pos = c.posicoes()

    if not pos:
        print(f"\n  {Fore.YELLOW}Carteira vazia. Use --carteira-add para registrar posições.{Style.RESET_ALL}\n")
        print(f"  Exemplo: python main.py --carteira-add PETR4 38.20 100\n")
        return

    # Busca preços atuais
    print(f"\n  {Fore.CYAN}Buscando preços atuais...{Style.RESET_ALL}")
    precos = {}
    for p in pos:
        try:
            precos[p["ticker"]] = get_preco_atual(p["ticker"] + ".SA")
        except Exception:
            precos[p["ticker"]] = p["pm"]

    resumo = c.resumo(precos)

    print_cabecalho()
    print(f"\n  {'─'*24} MINHA CARTEIRA {'─'*24}\n")

    hdr = (f"  {'TICKER':<8} {'QTD':>5} {'PM':>8} {'ATUAL':>8} "
           f"{'INVESTIDO':>12} {'ATUAL':>10} {'RENT.':>7} {'DIV':>8} {'TOTAL':>7}")
    print(Fore.WHITE + Style.BRIGHT + hdr)
    print(LINE)

    for p in resumo["posicoes"]:
        rc = Fore.GREEN if p["rent_pct"] >= 0 else Fore.RED
        rt = Fore.GREEN if p["rent_total"] >= 0 else Fore.RED
        print(
            f"  {p['ticker']:<8} {p['qtd']:>5}"
            f"  R${p['pm']:>7.2f}  R${p['preco_atual']:>7.2f}"
            f"  R${p['investido']:>10.2f}  R${p['atual']:>8.2f}"
            f"  {rc}{p['rent_pct']:>+6.1f}%{Style.RESET_ALL}"
            f"  R${p['dividendos']:>6.2f}"
            f"  {rt}{p['rent_total']:>+5.1f}%{Style.RESET_ALL}"
        )

    print(LINE)
    rc = Fore.GREEN if resumo["rentabilidade_pct"] >= 0 else Fore.RED
    print(f"\n  Total investido : R$ {resumo['total_investido']:>12,.2f}")
    print(f"  Valor atual     : R$ {resumo['total_atual']:>12,.2f}")
    print(f"  Lucro de capital: R$ {resumo['lucro_capital']:>+12,.2f}  "
          f"({rc}{resumo['rentabilidade_pct']:+.1f}%{Style.RESET_ALL})")
    print(f"  {Fore.CYAN}Dividendos rec. : R$ {resumo['total_dividendos']:>12,.2f}")
    print(f"  Retorno total   : {Fore.GREEN if resumo['rent_total_pct'] >= 0 else Fore.RED}"
          f"{resumo['rent_total_pct']:+.1f}%{Style.RESET_ALL}\n")

    # Alertas de concentração
    for alerta in c.alertas_risco():
        print(f"  {Fore.YELLOW}{alerta}{Style.RESET_ALL}")
    print()


def cmd_carteira_add(ticker: str, preco: float, qtd: int, data: str = None):
    c = Carteira()
    c.adicionar(ticker, preco, qtd, data)
    print(f"\n  {Fore.GREEN}✔ {ticker.upper()} adicionado: {qtd} ações a R$ {preco:.2f}{Style.RESET_ALL}\n")


def cmd_carteira_div(ticker: str, valor: float, data: str = None):
    c = Carteira()
    try:
        c.registrar_dividendo(ticker, valor, data)
        qtd = sum(l["qtd"] for l in c._dados["posicoes"][ticker.upper()]["lotes"])
        print(f"\n  {Fore.GREEN}✔ Dividendo registrado: {ticker.upper()} "
              f"R$ {valor:.4f}/ação × {qtd} = R$ {valor*qtd:.2f}{Style.RESET_ALL}\n")
    except ValueError as e:
        print(f"\n  {Fore.RED}Erro: {e}{Style.RESET_ALL}\n")


# ─────────────────────────────────────────────────────────────────────────────
#  Relatório HTML
# ─────────────────────────────────────────────────────────────────────────────

def cmd_relatorio(watchlist: list = None, com_backtest: bool = False):
    resultados = scan_watchlist(watchlist)
    if not resultados:
        return

    # Carteira (se existir)
    c = Carteira()
    precos = {r["ticker"]: r["fundamentos"].get("preco") for r in resultados}
    resumo_c = c.resumo(precos) if c.posicoes() else None

    # Backtest (opcional, demora)
    bt_resultado = None
    if com_backtest and not DEMO_MODE:
        print(f"\n  {Fore.CYAN}Rodando backtest para o relatório...{Style.RESET_ALL}")
        wl = [r["ticker"] + ".SA" for r in resultados]
        bt_resultado = backtest_lote(wl[:6], capital_por_ativo=10_000)

    caminho = salvar_relatorio(resultados, resumo_c, bt_resultado)
    print(f"\n  {Fore.GREEN + Style.BRIGHT}✔ Relatório salvo:{Style.RESET_ALL} {caminho}\n")


# ─────────────────────────────────────────────────────────────────────────────
#  Monitor contínuo
# ─────────────────────────────────────────────────────────────────────────────

def monitor_loop(intervalo_min: int = 30):
    print(f"\n  {Fore.CYAN}Monitor iniciado — intervalo: {intervalo_min} min{Style.RESET_ALL}")
    try:
        while True:
            scan_watchlist()
            print(f"\n  ⏳ Próximo scan em {intervalo_min} minutos...\n")
            time.sleep(intervalo_min * 60)
    except KeyboardInterrupt:
        print(f"\n  {Fore.YELLOW}Monitor encerrado.{Style.RESET_ALL}\n")


# ─────────────────────────────────────────────────────────────────────────────
#  CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(prog="dividend-bot",
        description="📊 Dividend Bot B3 — Análise, Carteira e Backtest")
    p.add_argument("--ticker",        type=str,         help="Detalhe de um ativo (ex: ITUB4)")
    p.add_argument("--preco-compra",  type=float, default=0)
    p.add_argument("--backtest",      action="store_true")
    p.add_argument("--backtest-period",type=str, default="5y", help="Período (ex: 2y, 5y)")
    p.add_argument("--monitor",       action="store_true")
    p.add_argument("--intervalo",     type=int,  default=30)
    p.add_argument("--detalhe",       action="store_true")
    p.add_argument("--demo",          action="store_true")
    p.add_argument("--lista",         type=str,  nargs="+")
    p.add_argument("--relatorio",     action="store_true", help="Gera relatório HTML")
    p.add_argument("--relatorio-bt",  action="store_true", help="Inclui backtest no HTML")
    p.add_argument("--carteira",      action="store_true", help="Exibe carteira")
    p.add_argument("--carteira-add",  type=str,  nargs="+",
                   metavar=("TICKER PRECO QTD"), help="Registra compra: PETR4 38.20 100")
    p.add_argument("--carteira-div",  type=str,  nargs="+",
                   metavar=("TICKER VALOR"),     help="Registra dividendo: PETR4 0.85")

    args = p.parse_args()

    global DEMO_MODE
    DEMO_MODE = args.demo
    if DEMO_MODE:
        print(f"\n  {Fore.YELLOW}[MODO DEMO] Usando dados simulados.{Style.RESET_ALL}")

    watchlist = ([t if t.endswith(".SA") else t + ".SA" for t in args.lista]
                 if args.lista else None)

    if args.ticker:
        print_cabecalho()
        analisar(args.ticker, detalhe=True, preco_compra=args.preco_compra)

    elif args.backtest:
        cmd_backtest(watchlist, period=args.backtest_period)

    elif args.monitor:
        monitor_loop(args.intervalo)

    elif args.carteira:
        cmd_carteira_exibir()

    elif args.carteira_add:
        a = args.carteira_add
        if len(a) < 3:
            print("Uso: --carteira-add TICKER PRECO QTD [DATA]")
        else:
            cmd_carteira_add(a[0], float(a[1]), int(a[2]), a[3] if len(a) > 3 else None)

    elif args.carteira_div:
        a = args.carteira_div
        if len(a) < 2:
            print("Uso: --carteira-div TICKER VALOR [DATA]")
        else:
            cmd_carteira_div(a[0], float(a[1]), a[2] if len(a) > 2 else None)

    elif args.relatorio or args.relatorio_bt:
        cmd_relatorio(watchlist, com_backtest=args.relatorio_bt)

    else:
        scan_watchlist(watchlist, detalhe=args.detalhe)


if __name__ == "__main__":
    main()
