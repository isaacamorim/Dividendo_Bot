"""
reports/html_report.py

Gera relatório HTML completo com scan, valuation e carteira.
Salva em reports/relatorio_YYYYMMDD_HHMM.html
"""

import os
from datetime import datetime

REPORTS_DIR = os.path.join(os.path.dirname(__file__))


def _cor_sinal(sinal: str) -> str:
    return {"BUY": "#22c55e", "SELL": "#ef4444", "HOLD": "#f59e0b"}.get(sinal, "#94a3b8")


def _cor_upside(upside) -> str:
    if upside is None: return "#94a3b8"
    if upside >= 15:   return "#22c55e"
    if upside >= 0:    return "#86efac"
    if upside >= -20:  return "#fbbf24"
    return "#ef4444"


def _cor_score(score: float) -> str:
    if score >= 8: return "#22c55e"
    if score >= 6: return "#f59e0b"
    return "#ef4444"


def _fmt(v, fmt=".2f", pre="R$", suf=""):
    if v is None: return "N/D"
    return f"{pre}{v:{fmt}}{suf}"


def gerar_html(resultados: list, resumo_carteira: dict = None,
               backtest_lote: dict = None) -> str:
    """Gera HTML completo. Retorna string HTML."""

    agora    = datetime.now().strftime("%d/%m/%Y %H:%M")
    n_buy    = sum(1 for r in resultados if r["sinal"] == "BUY")
    n_sell   = sum(1 for r in resultados if r["sinal"] == "SELL")
    n_hold   = sum(1 for r in resultados if r["sinal"] == "HOLD")
    top5     = sorted(resultados, key=lambda x: (
        0 if x["sinal"] == "BUY" else 1, -x["score"],
        -(x.get("valuation", {}).get("upside") or 0)
    ))[:5]

    # ── Linhas da tabela ────────────────────────────────────────────────────
    linhas_tabela = ""
    for r in sorted(resultados, key=lambda x: -x["score"]):
        f      = r.get("fundamentos", {})
        val    = r.get("valuation", {})
        tec    = r.get("tecnico", {})
        preco  = f.get("preco")
        ma200  = tec.get("ma_longa")
        pjusto = val.get("preco_justo")
        upside = val.get("upside")
        div_a  = val.get("div_estimado")
        div_m  = val.get("div_mensal")
        payout = f.get("payout") or 0

        ma_cor = "#22c55e" if (preco or 0) >= (ma200 or 0) and ma200 else "#ef4444"

        payout_tag = ""
        if payout > 0:
            if payout <= 70:   payout_tag = f'<span class="badge green">{payout:.0f}%</span>'
            elif payout <= 90: payout_tag = f'<span class="badge yellow">{payout:.0f}%</span>'
            else:              payout_tag = f'<span class="badge red">{payout:.0f}%</span>'

        linhas_tabela += f"""
        <tr>
          <td><strong>{r['ticker']}</strong></td>
          <td class="small">{(f.get('nome') or r['ticker'])[:22]}</td>
          <td class="small">{r.get('setor_perfil','')}</td>
          <td>{'R$'+f'{preco:.2f}' if preco else 'N/D'}</td>
          <td style="color:{ma_cor}">{'R$'+f'{ma200:.2f}' if ma200 else 'N/D'}</td>
          <td>{'R$'+f'{pjusto:.2f}' if pjusto else 'N/D'}</td>
          <td style="color:{_cor_upside(upside)};font-weight:600">
            {f'{upside:+.0f}%' if upside is not None else 'N/D'}
          </td>
          <td>{f.get('dy') or 0:.1f}%</td>
          <td>{'R$'+f'{div_a:.2f}' if div_a else 'N/D'}</td>
          <td>{'R$'+f'{div_m:.2f}' if div_m else 'N/D'}</td>
          <td>{f.get('roe') or 0:.1f}%</td>
          <td>{f.get('pl') or 0:.1f}</td>
          <td>{payout_tag}</td>
          <td style="color:{_cor_score(r['score'])};font-weight:700">{r['score']}</td>
          <td><span class="badge" style="background:{_cor_sinal(r['sinal'])}20;color:{_cor_sinal(r['sinal'])};border:1px solid {_cor_sinal(r['sinal'])}">{r['sinal']}</span></td>
          <td class="small">{r.get('estrategia','')[:3]}</td>
        </tr>"""

    # ── TOP 5 ───────────────────────────────────────────────────────────────
    cards_top5 = ""
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
    for i, r in enumerate(top5):
        val    = r.get("valuation", {})
        f      = r.get("fundamentos", {})
        upside = val.get("upside")
        div    = val.get("div_estimado")
        s_cor  = _cor_sinal(r["sinal"])
        cards_top5 += f"""
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <span style="font-size:1.3em">{medals[i]}</span>
            <span class="badge" style="background:{s_cor}20;color:{s_cor};border:1px solid {s_cor}">{r['sinal']}</span>
          </div>
          <div style="font-size:1.4em;font-weight:700;color:#f1f5f9">{r['ticker']}</div>
          <div style="color:#94a3b8;font-size:.85em;margin:2px 0">{r.get('setor_perfil','')}</div>
          <div style="margin-top:10px;display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:.88em">
            <span style="color:#94a3b8">Score</span>
            <span style="color:{_cor_score(r['score'])};font-weight:700">{r['score']}</span>
            <span style="color:#94a3b8">DY</span>
            <span style="color:#22c55e">{f.get('dy') or 0:.1f}%</span>
            <span style="color:#94a3b8">Upside</span>
            <span style="color:{_cor_upside(upside)}">{f'{upside:+.0f}%' if upside is not None else 'N/D'}</span>
            <span style="color:#94a3b8">Div/ano</span>
            <span style="color:#38bdf8">{'R$'+f'{div:.2f}' if div else 'N/D'}</span>
          </div>
        </div>"""

    # ── Seção carteira (opcional) ────────────────────────────────────────────
    secao_carteira = ""
    if resumo_carteira and resumo_carteira.get("posicoes"):
        rc        = resumo_carteira
        rent_cor  = "#22c55e" if rc["rentabilidade_pct"] >= 0 else "#ef4444"
        linhas_c  = ""
        for p in rc["posicoes"]:
            r_cor = "#22c55e" if p["rent_pct"] >= 0 else "#ef4444"
            linhas_c += f"""
            <tr>
              <td><strong>{p['ticker']}</strong></td>
              <td>{p['qtd']}</td>
              <td>R${p['pm']:.2f}</td>
              <td>R${p['preco_atual']:.2f}</td>
              <td>R${p['investido']:.2f}</td>
              <td>R${p['atual']:.2f}</td>
              <td style="color:{r_cor};font-weight:600">{p['rent_pct']:+.1f}%</td>
              <td style="color:#38bdf8">R${p['dividendos']:.2f}</td>
              <td style="color:{r_cor};font-weight:600">{p['rent_total']:+.1f}%</td>
            </tr>"""

        secao_carteira = f"""
        <section>
          <h2>💼 Minha Carteira</h2>
          <div class="kpi-grid" style="margin-bottom:20px">
            <div class="kpi"><span class="kpi-label">Total investido</span>
              <span class="kpi-val">R${rc['total_investido']:,.2f}</span></div>
            <div class="kpi"><span class="kpi-label">Valor atual</span>
              <span class="kpi-val">R${rc['total_atual']:,.2f}</span></div>
            <div class="kpi"><span class="kpi-label">Rentabilidade</span>
              <span class="kpi-val" style="color:{rent_cor}">{rc['rentabilidade_pct']:+.1f}%</span></div>
            <div class="kpi"><span class="kpi-label">Dividendos recebidos</span>
              <span class="kpi-val" style="color:#22c55e">R${rc['total_dividendos']:,.2f}</span></div>
            <div class="kpi"><span class="kpi-label">Retorno total</span>
              <span class="kpi-val" style="color:{rent_cor}">{rc['rent_total_pct']:+.1f}%</span></div>
          </div>
          <table>
            <thead><tr>
              <th>Ticker</th><th>Qtd</th><th>PM</th><th>Atual</th>
              <th>Investido</th><th>Valor atual</th><th>Rent. cap.</th>
              <th>Dividendos</th><th>Ret. total</th>
            </tr></thead>
            <tbody>{linhas_c}</tbody>
          </table>
        </section>"""

    # ── Seção backtest (opcional) ────────────────────────────────────────────
    secao_backtest = ""
    if backtest_lote and "resultados" in backtest_lote:
        bl = backtest_lote
        alpha_cor = "#22c55e" if bl.get("alpha_medio", 0) >= 0 else "#ef4444"
        linhas_bt = ""
        for r in sorted(bl["resultados"], key=lambda x: -x["retorno_pct"]):
            rc = "#22c55e" if r["retorno_pct"] >= 0 else "#ef4444"
            ac = "#22c55e" if r["alpha_pct"]   >= 0 else "#ef4444"
            linhas_bt += f"""
            <tr>
              <td><strong>{r['ticker'].replace('.SA','')}</strong></td>
              <td>{r['anos']}a</td>
              <td style="color:{rc};font-weight:600">{r['retorno_pct']:+.1f}%</td>
              <td>{r['cagr_pct']:+.1f}%</td>
              <td>{r['bh_retorno_pct']:+.1f}%</td>
              <td style="color:{ac};font-weight:600">{r['alpha_pct']:+.1f}%</td>
              <td>{r['sharpe']:.2f}</td>
              <td>{r['max_drawdown']:.1f}%</td>
              <td>{r['win_rate_pct']:.0f}%</td>
              <td>{r['n_trades']}</td>
            </tr>"""

        secao_backtest = f"""
        <section>
          <h2>📈 Backtest — Estratégia vs Buy & Hold</h2>
          <div class="kpi-grid" style="margin-bottom:20px">
            <div class="kpi"><span class="kpi-label">Ativos testados</span>
              <span class="kpi-val">{bl['n_ativos']}</span></div>
            <div class="kpi"><span class="kpi-label">Retorno médio</span>
              <span class="kpi-val">{bl['retorno_medio']:+.1f}%</span></div>
            <div class="kpi"><span class="kpi-label">B&H médio</span>
              <span class="kpi-val">{bl['bh_medio']:+.1f}%</span></div>
            <div class="kpi"><span class="kpi-label">Alpha médio</span>
              <span class="kpi-val" style="color:{alpha_cor}">{bl['alpha_medio']:+.1f}%</span></div>
            <div class="kpi"><span class="kpi-label">Sharpe médio</span>
              <span class="kpi-val">{bl['sharpe_medio']:.2f}</span></div>
            <div class="kpi"><span class="kpi-label">% venceu B&H</span>
              <span class="kpi-val">{bl['pct_venceu_bh']:.0f}%</span></div>
          </div>
          <table>
            <thead><tr>
              <th>Ticker</th><th>Período</th><th>Retorno</th><th>CAGR</th>
              <th>B&H</th><th>Alpha</th><th>Sharpe</th><th>Max DD</th>
              <th>Win%</th><th>Trades</th>
            </tr></thead>
            <tbody>{linhas_bt}</tbody>
          </table>
          <p style="color:#64748b;font-size:.82em;margin-top:12px">
            ⚠️ Resultados históricos não garantem retornos futuros.
            Alpha = retorno da estratégia − Buy &amp; Hold no mesmo período.
          </p>
        </section>"""

    # ── HTML final ───────────────────────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dividend Bot B3 — {agora}</title>
<style>
  :root{{--bg:#0f172a;--surface:#1e293b;--border:#334155;--text:#e2e8f0;--muted:#94a3b8}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:'Segoe UI',system-ui,sans-serif;font-size:14px;padding:24px}}
  h1{{font-size:1.6em;font-weight:700;color:#f1f5f9;margin-bottom:4px}}
  h2{{font-size:1.15em;font-weight:600;color:#cbd5e1;margin:28px 0 14px;border-bottom:1px solid var(--border);padding-bottom:6px}}
  .subtitle{{color:var(--muted);margin-bottom:28px;font-size:.9em}}
  .kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}}
  .kpi{{background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:14px 16px}}
  .kpi-label{{display:block;font-size:.78em;color:var(--muted);margin-bottom:4px;text-transform:uppercase;letter-spacing:.04em}}
  .kpi-val{{display:block;font-size:1.35em;font-weight:700;color:#f1f5f9}}
  .top5-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;margin-bottom:32px}}
  .card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:16px}}
  section{{margin-bottom:36px}}
  .table-wrap{{overflow-x:auto}}
  table{{width:100%;border-collapse:collapse;font-size:.86em}}
  th{{background:#1e293b;color:var(--muted);font-weight:600;text-align:left;padding:8px 10px;position:sticky;top:0;text-transform:uppercase;font-size:.78em;letter-spacing:.04em;border-bottom:1px solid var(--border)}}
  td{{padding:7px 10px;border-bottom:1px solid #1e293b;vertical-align:middle}}
  tr:hover td{{background:#1e293b88}}
  .badge{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:.8em;font-weight:600}}
  .badge.green{{background:#22c55e20;color:#22c55e;border:1px solid #22c55e}}
  .badge.yellow{{background:#f59e0b20;color:#f59e0b;border:1px solid #f59e0b}}
  .badge.red{{background:#ef444420;color:#ef4444;border:1px solid #ef4444}}
  .small{{font-size:.84em;color:var(--muted)}}
  .summary-badges{{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}}
</style>
</head>
<body>

<h1>📊 Dividend Bot B3</h1>
<div class="subtitle">Gerado em {agora} · {len(resultados)} ativos analisados</div>

<div class="kpi-grid" style="margin-bottom:28px">
  <div class="kpi"><span class="kpi-label">🟢 BUY</span><span class="kpi-val" style="color:#22c55e">{n_buy}</span></div>
  <div class="kpi"><span class="kpi-label">🔴 SELL</span><span class="kpi-val" style="color:#ef4444">{n_sell}</span></div>
  <div class="kpi"><span class="kpi-label">🟡 HOLD</span><span class="kpi-val" style="color:#f59e0b">{n_hold}</span></div>
  <div class="kpi"><span class="kpi-label">Score médio</span><span class="kpi-val">{sum(r['score'] for r in resultados)/len(resultados):.1f}</span></div>
</div>

<section>
  <h2>🏆 Top 5 Oportunidades</h2>
  <div class="top5-grid">{cards_top5}</div>
</section>

{secao_carteira}

<section>
  <h2>📋 Scan Completo</h2>
  <div class="table-wrap">
  <table>
    <thead><tr>
      <th>Ticker</th><th>Nome</th><th>Setor</th><th>Preço</th><th>MA200</th>
      <th>P. Justo</th><th>Upside</th><th>DY</th><th>Div/ano</th><th>Div/mês</th>
      <th>ROE</th><th>P/L</th><th>Payout</th><th>Score</th><th>Sinal</th><th>Tipo</th>
    </tr></thead>
    <tbody>{linhas_tabela}</tbody>
  </table>
  </div>
  <p style="color:#64748b;font-size:.8em;margin-top:10px">
    MA200: verde = preço acima · vermelho = abaixo · Payout: verde ≤70% · amarelo ≤90% · vermelho >90%
  </p>
</section>

{secao_backtest}

<footer style="margin-top:40px;color:#475569;font-size:.8em;border-top:1px solid var(--border);padding-top:16px">
  Dividend Bot B3 · Apenas fins informativos · Não constitui recomendação de investimento
</footer>

</body></html>"""

    return html


def salvar_relatorio(resultados: list, resumo_carteira: dict = None,
                     backtest_lote: dict = None) -> str:
    """Gera e salva o relatório HTML. Retorna o caminho do arquivo."""
    html     = gerar_html(resultados, resumo_carteira, backtest_lote)
    nome     = f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    caminho  = os.path.join(REPORTS_DIR, nome)
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(html)
    return caminho
