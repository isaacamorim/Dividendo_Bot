"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { HistoricoPonto } from "@/types";

const ddmm = (d: string) => {
  const p = d.split("-");
  return `${p[2]}/${p[1]}`;
};

export default function ScoreChart({ serie }: { serie: HistoricoPonto[] }) {
  if (serie.length <= 1) {
    return (
      <div className="flex h-72 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-center text-sm text-zinc-500">
        Mais dados disponíveis após alguns dias de execução
      </div>
    );
  }

  const dados = serie.map((p) => ({ ...p, dataFmt: ddmm(p.data) }));

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      <h3 className="mb-3 text-sm font-semibold text-zinc-400">Score no tempo</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={dados}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="dataFmt" stroke="#71717a" fontSize={12} />
          <YAxis domain={[0, 10]} stroke="#71717a" fontSize={12} />
          <Tooltip
            contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", borderRadius: 8 }}
            labelStyle={{ color: "#a1a1aa" }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            formatter={(v: number, _n: string, item: any) => [
              `${v} (${item.payload.sinal})`,
              "Score",
            ]}
          />
          <Line type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
