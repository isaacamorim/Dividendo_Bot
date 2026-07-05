"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { CapitalPonto } from "@/types";

const ddmm = (d: string) => {
  const p = d.split("-");
  return `${p[2]}/${p[1]}`;
};
const nomes: Record<string, string> = { estrategia: "Estratégia", bh: "Buy & Hold" };

export default function BacktestChart({
  historico,
  historico_bh,
}: {
  historico?: CapitalPonto[];
  historico_bh?: CapitalPonto[];
}) {
  if (!historico || historico.length === 0) {
    return (
      <div className="flex h-72 items-center justify-center rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-center text-sm text-zinc-400">
        💡 O gráfico aparece na primeira consulta (ao vivo). Clique em outro ativo e volte, ou
        aguarde o cache expirar (24h) para ver o gráfico novamente.
      </div>
    );
  }

  const dados = historico.map((h, i) => ({
    dataFmt: ddmm(h.data),
    estrategia: h.capital,
    bh: historico_bh?.[i]?.capital ?? null,
  }));

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      <h3 className="mb-3 text-sm font-semibold text-zinc-400">
        Capital: Estratégia vs Buy &amp; Hold
      </h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={dados}>
          <defs>
            <linearGradient id="gEstr" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gBh" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#71717a" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#71717a" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
          <XAxis dataKey="dataFmt" stroke="#71717a" fontSize={11} minTickGap={40} />
          <YAxis stroke="#71717a" fontSize={11} />
          <Tooltip
            contentStyle={{ background: "#18181b", border: "1px solid #3f3f46", borderRadius: 8 }}
            formatter={(v, name) => [`R$${v}`, nomes[String(name)] ?? String(name)]}
          />
          <Legend formatter={(v) => nomes[String(v)] ?? String(v)} />
          <Area type="monotone" dataKey="bh" stroke="#71717a" fill="url(#gBh)" strokeWidth={2} />
          <Area
            type="monotone"
            dataKey="estrategia"
            stroke="#3b82f6"
            fill="url(#gEstr)"
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
