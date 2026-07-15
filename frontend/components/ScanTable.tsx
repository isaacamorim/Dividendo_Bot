"use client";

import { useState } from "react";
import { AtivoResult, Sinal } from "@/types";
import GptAnaliseModal from "@/components/GptAnaliseModal";

type Col = keyof AtivoResult;
type Filtro = "TODOS" | Sinal;

const num = (v: number | null, d = 2) => (v == null ? "—" : v.toFixed(d));
const truncar = (s: string, n = 14) => (s.length > n ? s.slice(0, n) + "…" : s);

const COLS: { key: Col; label: string; sortable?: boolean }[] = [
  { key: "ticker", label: "Ticker" },
  { key: "setor_perfil", label: "Setor", sortable: false },
  { key: "preco", label: "Preço" },
  { key: "ma200", label: "MA200" },
  { key: "preco_justo", label: "P.Justo" },
  { key: "upside", label: "Upside" },
  { key: "dy", label: "DY" },
  { key: "div_estimado", label: "Div/est" },
  { key: "roe", label: "ROE" },
  { key: "pl", label: "P/L" },
  { key: "score", label: "Score" },
  { key: "sinal", label: "Sinal" },
];

export default function ScanTable({ resultados }: { resultados: AtivoResult[] }) {
  const [filtro, setFiltro] = useState<Filtro>("TODOS");
  const [sortCol, setSortCol] = useState<Col>("score");
  const [asc, setAsc] = useState(false);
  const [gptTicker, setGptTicker] = useState<string | null>(null);

  const linhaCor = (s: string) =>
    s === "BUY" ? "bg-emerald-950/30" : s === "SELL" ? "bg-red-950/30" : "bg-amber-950/20";
  const sinalCor = (s: string) =>
    s === "BUY" ? "text-emerald-400" : s === "SELL" ? "text-red-400" : "text-amber-400";
  const sinalBadge = (s: string) =>
    s === "BUY"
      ? "bg-emerald-900/40 text-emerald-400"
      : s === "SELL"
        ? "bg-red-900/40 text-red-400"
        : "bg-amber-900/40 text-amber-400";
  const upsideFmt = (u: number | null) =>
    u == null ? "—" : `${u > 0 ? "+" : ""}${u.toFixed(0)}%`;
  const divFmt = (r: AtivoResult) =>
    r.div_estimado == null
      ? "—"
      : r.frequencia === "mensal"
        ? `R$${(r.div_estimado / 12).toFixed(2)}/mês`
        : `R$${r.div_estimado.toFixed(2)}/ano`;

  let dados = filtro === "TODOS" ? resultados : resultados.filter((r) => r.sinal === filtro);
  dados = [...dados].sort((a, b) => {
    const av = a[sortCol];
    const bv = b[sortCol];
    if (typeof av === "number" && typeof bv === "number") return asc ? av - bv : bv - av;
    return asc
      ? String(av).localeCompare(String(bv))
      : String(bv).localeCompare(String(av));
  });

  function sort(c: Col) {
    if (c === sortCol) setAsc(!asc);
    else {
      setSortCol(c);
      setAsc(false);
    }
  }

  return (
    <div>
      <div className="mb-3 flex gap-2">
        {(["TODOS", "BUY", "HOLD", "SELL"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFiltro(f)}
            className={`min-h-[44px] rounded-lg px-3 py-1 text-sm sm:min-h-0 ${
              filtro === f ? "bg-zinc-100 text-zinc-900" : "bg-zinc-800 text-zinc-300"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Tabela — sm+ */}
      <div className="hidden overflow-x-auto rounded-xl border border-zinc-800 sm:block">
        <table className="w-full text-sm">
          <thead className="bg-zinc-900 text-zinc-400">
            <tr>
              {COLS.map((c) => {
                const podeOrdenar = c.sortable !== false;
                return (
                  <th
                    key={c.key}
                    onClick={podeOrdenar ? () => sort(c.key) : undefined}
                    className={`px-3 py-2 text-left ${
                      podeOrdenar ? "cursor-pointer select-none hover:text-zinc-100" : ""
                    }`}
                  >
                    {c.label}
                    {podeOrdenar && sortCol === c.key ? (asc ? " ▲" : " ▼") : ""}
                  </th>
                );
              })}
              <th className="px-3 py-2 text-left">IA</th>
            </tr>
          </thead>
          <tbody>
            {dados.map((r) => (
              <tr key={r.ticker} className={`border-t border-zinc-800 ${linhaCor(r.sinal)}`}>
                <td className="px-3 py-2 font-medium">{r.ticker}</td>
                <td className="px-3 py-2 text-zinc-400" title={r.setor_perfil}>
                  {truncar(r.setor_perfil)}
                </td>
                <td className="px-3 py-2">R${num(r.preco)}</td>
                <td
                  className={`px-3 py-2 ${
                    r.ma200 == null
                      ? ""
                      : (r.preco ?? 0) >= r.ma200
                        ? "text-emerald-400"
                        : "text-red-400"
                  }`}
                >
                  {r.ma200 == null ? "—" : `R$${r.ma200.toFixed(2)}`}
                </td>
                <td className="px-3 py-2">R${num(r.preco_justo)}</td>
                <td
                  className={`px-3 py-2 ${
                    (r.upside ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {r.upside == null ? "—" : `${r.upside > 0 ? "+" : ""}${r.upside.toFixed(0)}%`}
                </td>
                <td className="px-3 py-2">{num(r.dy, 1)}%</td>
                <td className="px-3 py-2">
                  {r.div_estimado == null
                    ? "—"
                    : r.frequencia === "mensal"
                      ? `R$${(r.div_estimado / 12).toFixed(2)}/mês`
                      : `R$${r.div_estimado.toFixed(2)}/ano`}
                </td>
                <td className="px-3 py-2">{num(r.roe, 1)}%</td>
                <td className="px-3 py-2">{num(r.pl, 1)}</td>
                <td className="px-3 py-2 font-semibold">{num(r.score, 1)}</td>
                <td className={`px-3 py-2 font-semibold ${sinalCor(r.sinal)}`}>{r.sinal}</td>
                <td className="px-3 py-2">
                  <button
                    onClick={() => setGptTicker(r.ticker)}
                    title="Análise com IA"
                    className="rounded-lg bg-zinc-800 px-2 py-1 text-xs text-zinc-300 hover:bg-zinc-700"
                  >
                    🤖 GPT
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Cards — mobile (<sm) */}
      <div className="space-y-3 sm:hidden">
        {dados.map((r) => (
          <div
            key={r.ticker}
            className={`rounded-xl border border-zinc-800 p-4 ${linhaCor(r.sinal)}`}
          >
            {/* Linha 1: Ticker · Setor · Sinal */}
            <div className="flex items-center justify-between gap-2">
              <div className="flex min-w-0 items-baseline gap-2">
                <span className="font-bold">{r.ticker}</span>
                <span className="truncate text-xs text-zinc-400" title={r.setor_perfil}>
                  {truncar(r.setor_perfil)}
                </span>
              </div>
              <span
                className={`shrink-0 rounded px-2 py-0.5 text-xs font-semibold ${sinalBadge(r.sinal)}`}
              >
                {r.sinal}
              </span>
            </div>

            {/* Linha 2: Score · DY · Upside */}
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-sm text-zinc-300">
              <span>
                Score: <span className="font-semibold text-zinc-100">{num(r.score, 1)}</span>
              </span>
              <span>DY: {num(r.dy, 1)}%</span>
              <span>
                Upside:{" "}
                <span className={(r.upside ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"}>
                  {upsideFmt(r.upside)}
                </span>
              </span>
            </div>

            {/* Linha 3: Preço · P.Justo · MA200 */}
            <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-zinc-300">
              <span>Preço: R${num(r.preco)}</span>
              <span>P.Justo: R${num(r.preco_justo)}</span>
              <span>
                MA200:{" "}
                <span
                  className={
                    r.ma200 == null
                      ? ""
                      : (r.preco ?? 0) >= r.ma200
                        ? "text-emerald-400"
                        : "text-red-400"
                  }
                >
                  {r.ma200 == null ? "—" : `R$${r.ma200.toFixed(2)}`}
                </span>
              </span>
            </div>

            {/* Linha 4: ROE · P/L · Div */}
            <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-zinc-300">
              <span>ROE: {num(r.roe, 1)}%</span>
              <span>P/L: {num(r.pl, 1)}</span>
              <span>Div: {divFmt(r)}</span>
            </div>

            {/* Linha 5: botão GPT full-width, 44px */}
            <button
              onClick={() => setGptTicker(r.ticker)}
              className="mt-3 flex min-h-[44px] w-full items-center justify-center rounded-lg bg-zinc-800 text-sm text-zinc-300 hover:bg-zinc-700"
            >
              🤖 Análise GPT
            </button>
          </div>
        ))}
      </div>

      {gptTicker && (
        <GptAnaliseModal ticker={gptTicker} onClose={() => setGptTicker(null)} />
      )}
    </div>
  );
}
