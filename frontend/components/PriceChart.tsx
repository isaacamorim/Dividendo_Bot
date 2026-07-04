"use client";

import {
  CartesianGrid,
  Legend,
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

const nomes: Record<string, string> = { preco: "Preço", preco_justo: "Preço Justo" };

export default function PriceChart({ serie }: { serie: HistoricoPonto[] }) {
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
      <h3 className="mb-3 text-sm font-semibold text-zinc-400">Preço vs Preço Justo</h3>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={dados}>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="dataFmt" stroke="#71717a" fontSize={12} />
          <YAxis stroke="#71717a" fontSize={12} />
          <Tooltip
            contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", borderRadius: 8 }}
            labelStyle={{ color: "#a1a1aa" }}
            formatter={(value, name, item) =>
              name === "preco"
                ? [
                    `R$${value} (upside ${
                      (item as { payload: { upside: number | null } }).payload.upside ?? "—"
                    }%)`,
                    "Preço",
                  ]
                : [`R$${value}`, "Preço Justo"]
            }
          />
          <Legend formatter={(v: string) => nomes[v] ?? v} />
          <Line type="monotone" dataKey="preco" stroke="#22c55e" strokeWidth={2} dot={{ r: 3 }} />
          <Line
            type="monotone"
            dataKey="preco_justo"
            stroke="#f97316"
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
