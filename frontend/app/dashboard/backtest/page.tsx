"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { BacktestResult, ComparativoItem, ComparativoResponse } from "@/types";
import BacktestChart from "@/components/BacktestChart";

const API = process.env.NEXT_PUBLIC_API_URL || "";
const WATCHLIST = [
  // Bancos
  "BBAS3",
  "ITUB4",
  "BBDC4",

  // Energia
  "TAEE11",
  "ISAE4",
  "CMIG4",
  "CPLE3",
  "EGIE3",

  // Commodities
  "PETR4",
  "VALE3",

  // Telecom
  "VIVT3",

  // Industrial
  "WEGE3",

  // Tecnologia
  "TOTS3",

  // Saúde
  "RADL3",
  "RDOR3",

  // Consumo
  "ABEV3",
  "LREN3",

  // Seguros
  "CXSE3",

  // Papel e Celulose
  "SUZB3",

  // Shopping
  "MULT3",
];
const PERIODOS = ["1y", "2y", "5y"];

type Modo = "tecnico" | "fundamental";

const pct = (v: number | null | undefined) =>
  v == null ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(2)}%`;
const corVal = (v: number | null | undefined) =>
  (v ?? 0) >= 0 ? "text-emerald-400" : "text-red-400";
const ddmm = (d: string) => {
  const p = d.split("-");
  return `${p[2]}/${p[1]}`;
};

function veredito(it: ComparativoItem): string {
  if ((it.n_trades ?? 0) === 0) return "⏸ Sem operações";
  if ((it.retorno_pct ?? 0) < 0) return "❌ Prejuízo";
  if ((it.alpha_pct ?? 0) > 0) return "✅ Estratégia venceu B&H";
  return "📈 Lucro, mas B&H foi melhor";
}

export default function Backtest() {
  const router = useRouter();
  const [ticker, setTicker] = useState("PETR4");
  const [periodo, setPeriodo] = useState("5y");
  const [modo, setModo] = useState<Modo>("tecnico");
  const [dados, setDados] = useState<BacktestResult | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [comp, setComp] = useState<ComparativoResponse | null>(null);
  const [rodandoComp, setRodandoComp] = useState(false);

  async function rodarComparativo() {
    setRodandoComp(true);
    try {
      const resp = await fetch(`${API}/backtest/comparativo?periodo=5y`, {
        credentials: "include",
      });
      if (resp.status === 401) {
        router.push("/login");
        return;
      }
      setComp(await resp.json());
    } catch {
      // silencioso
    } finally {
      setRodandoComp(false);
    }
  }

  const carregar = useCallback(
    async (tk: string, per: string, md: Modo) => {
      setCarregando(true);
      const url =
        md === "fundamental"
          ? `${API}/backtest/fundamental/${tk}`
          : `${API}/backtest/${tk}?periodo=${per}`;
      try {
        const resp = await fetch(url, { credentials: "include" });
        if (resp.status === 401) {
          router.push("/login");
          return;
        }
        setDados(await resp.json());
      } catch {
        // silencioso
      } finally {
        setCarregando(false);
      }
    },
    [router],
  );

  useEffect(() => {
    carregar(ticker, periodo, modo);
  }, [ticker, periodo, modo, carregar]);

  const fund = modo === "fundamental";

  const kpis = dados
    ? fund
      ? [
          { label: "Retorno", value: pct(dados.retorno_pct), cor: corVal(dados.retorno_pct) },
          { label: "CAGR", value: pct(dados.cagr_pct), cor: "text-zinc-100" },
          { label: "Trades", value: `${dados.n_trades ?? 0}`, cor: "text-zinc-100" },
          { label: "Win Rate", value: dados.win_rate_pct == null ? "—" : `${dados.win_rate_pct}%`, cor: "text-zinc-100" },
          { label: "Max Drawdown", value: pct(dados.max_drawdown), cor: "text-red-400" },
        ]
      : [
          { label: "Retorno", value: pct(dados.retorno_pct), cor: corVal(dados.retorno_pct) },
          { label: "CAGR", value: pct(dados.cagr_pct), cor: "text-zinc-100" },
          { label: "Sharpe", value: dados.sharpe?.toFixed(2) ?? "—", cor: "text-zinc-100" },
          { label: "Max Drawdown", value: pct(dados.max_drawdown), cor: "text-red-400" },
          { label: "Alpha", value: pct(dados.alpha_pct), cor: corVal(dados.alpha_pct) },
          { label: "Win Rate", value: dados.win_rate_pct == null ? "—" : `${dados.win_rate_pct}%`, cor: "text-zinc-100" },
        ]
    : [];

  const selCls =
    "min-h-[44px] rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm outline-none focus:border-emerald-500 sm:min-h-0";

  return (
    <main className="mx-auto max-w-6xl px-4 py-6">
      <header className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-bold">📈 Backtest</h1>
        <Link
          href="/dashboard"
          className="rounded-lg bg-zinc-800 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-700"
        >
          ← Dashboard
        </Link>
      </header>

      {/* Toggle de modo */}
      <div className="mb-4 flex w-full rounded-lg border border-zinc-800 bg-zinc-900 p-1 sm:inline-flex sm:w-auto">
        {([["tecnico", "Técnico (MA50/MA200)"], ["fundamental", "Fundamental"]] as const).map(
          ([m, label]) => (
            <button
              key={m}
              onClick={() => setModo(m)}
              className={`min-h-[44px] flex-1 rounded-md px-3 py-1.5 text-sm sm:min-h-0 sm:flex-none ${
                modo === m ? "bg-emerald-600 text-white" : "text-zinc-400 hover:text-zinc-100"
              }`}
            >
              {label}
            </button>
          ),
        )}
      </div>

      <div className="mb-6 flex gap-3">
        <div>
          <label className="mb-1 block text-sm text-zinc-400">Ativo</label>
          <select className={selCls} value={ticker} onChange={(e) => setTicker(e.target.value)}>
            {WATCHLIST.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>
        {!fund && (
          <div>
            <label className="mb-1 block text-sm text-zinc-400">Período</label>
            <select className={selCls} value={periodo} onChange={(e) => setPeriodo(e.target.value)}>
              {PERIODOS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {carregando ? (
        <div className="animate-pulse text-zinc-500">Rodando backtest...</div>
      ) : dados && !dados.erro ? (
        <div className="space-y-6">
          {fund && dados.nota_dados && (
            <div className="rounded-xl border border-amber-800 bg-amber-950/40 px-4 py-3 text-sm text-amber-300">
              {dados.nota_dados}
            </div>
          )}

          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <span>{fund ? dados.periodo : dados.intervalo_datas ?? ""}</span>
            {!fund && (
              <span className="rounded bg-zinc-800 px-2 py-0.5">
                {dados.origem === "cache" ? "⚡ cache" : "🔄 ao vivo"}
              </span>
            )}
          </div>

          {/* KPIs */}
          <div
            className={`grid grid-cols-2 gap-3 sm:grid-cols-3 ${fund ? "lg:grid-cols-5" : "lg:grid-cols-6"}`}
          >
            {kpis.map((k) => (
              <div key={k.label} className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
                <div className="text-xs uppercase tracking-wide text-zinc-500">{k.label}</div>
                <div className={`mt-1 text-lg font-bold ${k.cor}`}>{k.value}</div>
              </div>
            ))}
          </div>

          {/* Bloco explicativo */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-sm text-zinc-400">
            <div className="mb-2 font-semibold text-zinc-200">
              📊 Como interpretar este backtest
            </div>
            {fund ? (
              <div className="space-y-2">
                <p>
                  A estratégia compra quando o score fundamentalista ≥ 7.0 (empresa com bons
                  fundamentos no preço certo) e vende quando:
                </p>
                <ul className="ml-4 list-disc space-y-1">
                  <li>Score cai abaixo de 5.0 por 3 dias consecutivos</li>
                  <li>ROE cai mais de 30% em relação ao momento da compra</li>
                </ul>
                <p>
                  Esta estratégia testa a tese de dividendos: comprar empresas boas e segurar
                  enquanto os fundamentos sustentam.
                </p>
                <p className="text-amber-300">
                  ⚠️ Resultado indicativo: o histórico tem poucos dias ainda. O backtest fica mais
                  confiável com 30+ dias de dados.
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                <p>
                  A estratégia compra quando MA50 cruza MA200 para cima (tendência de alta
                  confirmada) e vende no stop -8%, take profit +20%, ou quando MA50 cruza MA200 para
                  baixo.
                </p>
                <p>
                  Alpha = retorno da estratégia − Buy &amp; Hold no mesmo período. Alpha negativo
                  significa que teria sido melhor simplesmente comprar e segurar. Para ações de
                  dividendos, isso é comum — o backtest fundamental testa uma abordagem mais
                  adequada.
                </p>
              </div>
            )}
          </div>

          {/* Gráfico só no técnico */}
          {!fund && (
            <BacktestChart historico={dados.historico} historico_bh={dados.historico_bh} />
          )}

          {/* Trades */}
          <div className="overflow-x-auto rounded-xl border border-zinc-800">
            <table className="w-full text-sm">
              <thead className="bg-zinc-900 text-zinc-400">
                <tr>
                  {["Data", "Tipo", "Preço", "Qtd", "Lucro", fund ? "Motivo saída" : "Motivo"].map(
                    (h) => (
                      <th key={h} className="px-3 py-2 text-left">
                        {h}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody>
                {(dados.trades ?? []).length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-3 py-3 text-center text-zinc-500">
                      {fund
                        ? "Nenhum sinal de entrada encontrado no período"
                        : "Nenhum cruzamento MA50/MA200 encontrado no período. Experimente um período maior ou tente o modo Fundamental."}
                    </td>
                  </tr>
                ) : (
                  (dados.trades ?? []).map((t, i) => {
                    const lucroPos = (t.lucro ?? 0) >= 0;
                    const cor =
                      t.tipo === "COMPRA"
                        ? "bg-emerald-950/20"
                        : lucroPos
                          ? "bg-emerald-950/30"
                          : "bg-red-950/30";
                    return (
                      <tr key={i} className={`border-t border-zinc-800 ${cor}`}>
                        <td className="px-3 py-2">{ddmm(t.data)}</td>
                        <td className="px-3 py-2 font-medium">{t.tipo}</td>
                        <td className="px-3 py-2">R${t.preco.toFixed(2)}</td>
                        <td className="px-3 py-2">{t.qtd}</td>
                        <td className={`px-3 py-2 ${t.lucro == null ? "" : corVal(t.lucro)}`}>
                          {t.lucro == null ? "—" : `R$${t.lucro.toFixed(2)}`}
                        </td>
                        <td className="px-3 py-2 text-zinc-400">{t.motivo ?? "—"}</td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          <p className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-xs text-zinc-500">
            {fund
              ? "Compra quando score ≥ 7.0. Vende quando score < 5.0 por 3 dias consecutivos, ROE cai >30%, ou dívida explode com qualidade caindo. Testa a tese de dividendos, não swing trade."
              : "A estratégia usa cruzamento MA50/MA200. Alpha = retorno ativo − Buy & Hold no mesmo período. Resultados históricos não garantem retornos futuros."}
          </p>
        </div>
      ) : (
        <div className="text-zinc-500">{dados?.erro ?? "Sem dados para este ativo/período."}</div>
      )}

      {/* Análise consolidada — todos os ativos */}
      <section className="mt-10 border-t border-zinc-800 pt-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-bold">📈 Análise consolidada — todos os ativos</h2>
          <button
            onClick={rodarComparativo}
            disabled={rodandoComp}
            className="min-h-[44px] rounded-lg bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50 sm:min-h-0"
          >
            {rodandoComp ? "⏳ Calculando..." : "Rodar análise completa"}
          </button>
        </div>

        {rodandoComp ? (
          <div className="animate-pulse rounded-xl border border-zinc-800 bg-zinc-900 p-6 text-center text-sm text-zinc-400">
            ⏳ Calculando backtest para todos os ativos... Isso pode levar 2-3 minutos.
          </div>
        ) : comp ? (
          <div className="space-y-6">
            <div className="overflow-x-auto rounded-xl border border-zinc-800">
              <table className="w-full text-sm">
                <thead className="bg-zinc-900 text-zinc-400">
                  <tr>
                    {["Ticker", "Setor", "Retorno", "CAGR", "Alpha", "Sharpe", "Win Rate", "Trades", "Veredito"].map(
                      (h) => (
                        <th key={h} className="px-3 py-2 text-left">
                          {h}
                        </th>
                      ),
                    )}
                  </tr>
                </thead>
                <tbody>
                  {comp.ranking.map((it) => (
                    <tr key={it.ticker} className="border-t border-zinc-800">
                      <td className="px-3 py-2 font-medium">{it.ticker}</td>
                      <td className="px-3 py-2 text-zinc-400">{it.setor}</td>
                      <td className={`px-3 py-2 ${corVal(it.retorno_pct)}`}>{pct(it.retorno_pct)}</td>
                      <td className="px-3 py-2">{pct(it.cagr_pct)}</td>
                      <td className={`px-3 py-2 ${corVal(it.alpha_pct)}`}>{pct(it.alpha_pct)}</td>
                      <td className="px-3 py-2">{it.sharpe?.toFixed(2) ?? "—"}</td>
                      <td className="px-3 py-2">
                        {it.win_rate_pct == null ? "—" : `${it.win_rate_pct}%`}
                      </td>
                      <td className="px-3 py-2">{it.n_trades ?? 0}</td>
                      <td className="px-3 py-2 whitespace-nowrap">{veredito(it)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Resumo — 3 números grandes */}
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-center">
                <div className="text-3xl font-bold text-emerald-400">
                  {comp.pct_com_lucro ?? "—"}%
                </div>
                <div className="mt-1 text-xs text-zinc-500">dos ativos com lucro</div>
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-center">
                <div className="text-3xl font-bold text-emerald-400">
                  {comp.pct_venceu_bh ?? "—"}%
                </div>
                <div className="mt-1 text-xs text-zinc-500">venceram Buy &amp; Hold</div>
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-center">
                <div className={`text-3xl font-bold ${corVal(comp.alpha_medio)}`}>
                  {pct(comp.alpha_medio)}
                </div>
                <div className="mt-1 text-xs text-zinc-500">alpha médio da carteira</div>
              </div>
            </div>

            <p className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-xs text-zinc-500">
              Análise usando estratégia técnica MA50/MA200. Período: 5 anos. Capital inicial:
              R$10.000 por ativo. Resultados históricos não garantem retornos futuros.
            </p>
          </div>
        ) : (
          <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 text-center text-sm text-zinc-500">
            Clique em “Rodar análise completa” para comparar a estratégia em todos os ativos (pode
            levar 2-3 minutos).
          </div>
        )}
      </section>
    </main>
  );
}
