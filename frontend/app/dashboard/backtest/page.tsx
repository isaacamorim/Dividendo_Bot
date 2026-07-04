"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { BacktestResult } from "@/types";
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

const pct = (v: number | null | undefined) =>
  v == null ? "—" : `${v > 0 ? "+" : ""}${v.toFixed(2)}%`;
const corVal = (v: number | null | undefined) =>
  (v ?? 0) >= 0 ? "text-emerald-400" : "text-red-400";
const ddmm = (d: string) => {
  const p = d.split("-");
  return `${p[2]}/${p[1]}`;
};

export default function Backtest() {
  const router = useRouter();
  const [ticker, setTicker] = useState("PETR4");
  const [periodo, setPeriodo] = useState("5y");
  const [dados, setDados] = useState<BacktestResult | null>(null);
  const [carregando, setCarregando] = useState(true);

  const carregar = useCallback(
    async (tk: string, per: string) => {
      setCarregando(true);
      try {
        const resp = await fetch(`${API}/backtest/${tk}?periodo=${per}`, {
          credentials: "include",
        });
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
    carregar(ticker, periodo);
  }, [ticker, periodo, carregar]);

  const kpis = dados
    ? [
        { label: "Retorno", value: pct(dados.retorno_pct), cor: corVal(dados.retorno_pct) },
        { label: "CAGR", value: pct(dados.cagr_pct), cor: "text-zinc-100" },
        { label: "Sharpe", value: dados.sharpe?.toFixed(2) ?? "—", cor: "text-zinc-100" },
        { label: "Max Drawdown", value: pct(dados.max_drawdown), cor: "text-red-400" },
        { label: "Alpha", value: pct(dados.alpha_pct), cor: corVal(dados.alpha_pct) },
        { label: "Win Rate", value: dados.win_rate_pct == null ? "—" : `${dados.win_rate_pct}%`, cor: "text-zinc-100" },
      ]
    : [];

  const selCls =
    "rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 text-sm outline-none focus:border-emerald-500";

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
      </div>

      {carregando ? (
        <div className="animate-pulse text-zinc-500">Rodando backtest...</div>
      ) : dados && !dados.erro ? (
        <div className="space-y-6">
          <div className="flex items-center gap-2 text-xs text-zinc-500">
            <span>{dados.intervalo_datas ?? ""}</span>
            <span className="rounded bg-zinc-800 px-2 py-0.5">
              {dados.origem === "cache" ? "⚡ cache" : "🔄 ao vivo"}
            </span>
          </div>

          {/* KPIs */}
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {kpis.map((k) => (
              <div key={k.label} className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
                <div className="text-xs uppercase tracking-wide text-zinc-500">{k.label}</div>
                <div className={`mt-1 text-lg font-bold ${k.cor}`}>{k.value}</div>
              </div>
            ))}
          </div>

          <BacktestChart historico={dados.historico} historico_bh={dados.historico_bh} />

          {/* Trades */}
          <div className="overflow-x-auto rounded-xl border border-zinc-800">
            <table className="w-full text-sm">
              <thead className="bg-zinc-900 text-zinc-400">
                <tr>
                  {["Data", "Tipo", "Preço", "Qtd", "Lucro", "Motivo"].map((h) => (
                    <th key={h} className="px-3 py-2 text-left">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(dados.trades ?? []).length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-3 py-3 text-center text-zinc-500">
                      Sem trades (ou resultado em cache)
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
            A estratégia usa cruzamento MA50/MA200. Alpha = retorno ativo − Buy &amp; Hold no mesmo
            período. Resultados históricos não garantem retornos futuros.
          </p>
        </div>
      ) : (
        <div className="text-zinc-500">
          {dados?.erro ?? "Sem dados para este ativo/período."}
        </div>
      )}
    </main>
  );
}
