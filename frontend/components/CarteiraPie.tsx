"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Posicao } from "@/types";

const CORES = [
  "#3b82f6", "#22c55e", "#f97316", "#a855f7",
  "#eab308", "#ec4899", "#14b8a6", "#ef4444",
];

export default function CarteiraPie({ posicoes }: { posicoes: Posicao[] }) {
  const total = posicoes.reduce((s, p) => s + p.investido, 0);
  const dados = posicoes.map((p) => ({ name: p.ticker, value: p.investido }));
  const pcts = posicoes.map((p) => ({
    ticker: p.ticker,
    pct: total ? (p.investido / total) * 100 : 0,
  }));
  const concentrado = pcts.some((d) => d.pct > 30);

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-400">Composição da carteira</h3>
        {concentrado && (
          <span className="rounded bg-red-950 px-2 py-1 text-xs text-red-400">
            ⚠️ Concentração
          </span>
        )}
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie data={dados} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={85}>
            {dados.map((_, i) => (
              <Cell key={i} fill={CORES[i % CORES.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(v) => `R$${v}`}
            contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", borderRadius: 8 }}
          />
        </PieChart>
      </ResponsiveContainer>
      <ul className="mt-2 space-y-1 text-xs">
        {pcts.map((d, i) => (
          <li key={d.ticker} className="flex items-center gap-2">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ background: CORES[i % CORES.length] }}
            />
            <span className="text-zinc-300">{d.ticker}</span>
            <span className={`ml-auto ${d.pct > 30 ? "text-red-400" : "text-zinc-500"}`}>
              {d.pct.toFixed(1)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
