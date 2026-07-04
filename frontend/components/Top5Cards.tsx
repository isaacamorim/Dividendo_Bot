import { AtivoResult } from "@/types";

const corSinal = (s: string) =>
  s === "BUY" ? "text-emerald-400" : s === "SELL" ? "text-red-400" : "text-amber-400";

export default function Top5Cards({ resultados }: { resultados: AtivoResult[] }) {
  const top = [...resultados]
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
    .slice(0, 5);

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
      {top.map((r) => (
        <div key={r.ticker} className="rounded-xl border border-zinc-800 bg-zinc-900 p-4">
          <div className="flex items-start justify-between">
            <div>
              <div className="font-bold">{r.ticker}</div>
              <div className="text-xs text-zinc-500">{r.setor_perfil}</div>
            </div>
            <span className={`text-sm font-semibold ${corSinal(r.sinal)}`}>{r.sinal}</span>
          </div>
          <div className="mt-2 text-2xl font-bold">{r.score?.toFixed(1) ?? "—"}</div>
          <div className="mt-1 text-xs text-zinc-400">
            DY {r.dy?.toFixed(1) ?? "—"}% · upside{" "}
            {r.upside == null ? "—" : `${r.upside > 0 ? "+" : ""}${r.upside.toFixed(0)}%`}
          </div>
          <div className="text-xs text-zinc-500">
            div/ano R${r.div_estimado?.toFixed(2) ?? "—"}
          </div>
        </div>
      ))}
    </div>
  );
}
