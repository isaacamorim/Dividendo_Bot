"use client";

import { useState } from "react";
import { AtivoResult, Sinal } from "@/types";

type Col = keyof AtivoResult;
type Filtro = "TODOS" | Sinal;

const num = (v: number | null, d = 2) => (v == null ? "—" : v.toFixed(d));

const COLS: { key: Col; label: string }[] = [
  { key: "ticker", label: "Ticker" },
  { key: "preco", label: "Preço" },
  { key: "preco_justo", label: "P.Justo" },
  { key: "upside", label: "Upside" },
  { key: "dy", label: "DY" },
  { key: "div_estimado", label: "Div/ano" },
  { key: "roe", label: "ROE" },
  { key: "pl", label: "P/L" },
  { key: "score", label: "Score" },
  { key: "sinal", label: "Sinal" },
];

export default function ScanTable({ resultados }: { resultados: AtivoResult[] }) {
  const [filtro, setFiltro] = useState<Filtro>("TODOS");
  const [sortCol, setSortCol] = useState<Col>("score");
  const [asc, setAsc] = useState(false);

  const linhaCor = (s: string) =>
    s === "BUY" ? "bg-emerald-950/30" : s === "SELL" ? "bg-red-950/30" : "bg-amber-950/20";
  const sinalCor = (s: string) =>
    s === "BUY" ? "text-emerald-400" : s === "SELL" ? "text-red-400" : "text-amber-400";

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
            className={`rounded-lg px-3 py-1 text-sm ${
              filtro === f ? "bg-zinc-100 text-zinc-900" : "bg-zinc-800 text-zinc-300"
            }`}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="overflow-x-auto rounded-xl border border-zinc-800">
        <table className="w-full text-sm">
          <thead className="bg-zinc-900 text-zinc-400">
            <tr>
              {COLS.map((c) => (
                <th
                  key={c.key}
                  onClick={() => sort(c.key)}
                  className="cursor-pointer select-none px-3 py-2 text-left hover:text-zinc-100"
                >
                  {c.label}
                  {sortCol === c.key ? (asc ? " ▲" : " ▼") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {dados.map((r) => (
              <tr key={r.ticker} className={`border-t border-zinc-800 ${linhaCor(r.sinal)}`}>
                <td className="px-3 py-2 font-medium">{r.ticker}</td>
                <td className="px-3 py-2">R${num(r.preco)}</td>
                <td className="px-3 py-2">R${num(r.preco_justo)}</td>
                <td
                  className={`px-3 py-2 ${
                    (r.upside ?? 0) >= 0 ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {r.upside == null ? "—" : `${r.upside > 0 ? "+" : ""}${r.upside.toFixed(0)}%`}
                </td>
                <td className="px-3 py-2">{num(r.dy, 1)}%</td>
                <td className="px-3 py-2">R${num(r.div_estimado)}</td>
                <td className="px-3 py-2">{num(r.roe, 1)}%</td>
                <td className="px-3 py-2">{num(r.pl, 1)}</td>
                <td className="px-3 py-2 font-semibold">{num(r.score, 1)}</td>
                <td className={`px-3 py-2 font-semibold ${sinalCor(r.sinal)}`}>{r.sinal}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
