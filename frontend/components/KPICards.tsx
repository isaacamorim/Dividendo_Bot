interface Props {
  buy: number;
  hold: number;
  sell: number;
  ultima_atualizacao: string;
}

export default function KPICards({ buy, hold, sell, ultima_atualizacao }: Props) {
  const cards = [
    { label: "BUY", value: buy, cor: "border-emerald-800 bg-emerald-950/40 text-emerald-400" },
    { label: "HOLD", value: hold, cor: "border-amber-800 bg-amber-950/40 text-amber-400" },
    { label: "SELL", value: sell, cor: "border-red-800 bg-red-950/40 text-red-400" },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {cards.map((c) => (
        <div key={c.label} className={`rounded-xl border p-4 ${c.cor}`}>
          <div className="text-xs uppercase tracking-wide opacity-70">{c.label}</div>
          <div className="text-3xl font-bold">{c.value}</div>
        </div>
      ))}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-zinc-300">
        <div className="text-xs uppercase tracking-wide opacity-70">Atualizado</div>
        <div className="mt-1 text-lg font-semibold">{ultima_atualizacao}</div>
      </div>
    </div>
  );
}
